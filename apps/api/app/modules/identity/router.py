import hashlib
import hmac
import json
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from urllib.parse import quote
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.mfa import decrypt_totp_secret, encrypt_totp_secret, matching_counter, new_totp_secret, provisioning_uri
from app.core.security import (
    create_access_token,
    create_refresh_token,
    current_user,
    hash_password,
    oauth2_scheme,
    verify_password,
)
from app.modules.accounts.models import Account, Wallet
from app.modules.identity.models import AuditLog, AuthSession, Customer, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(default="", max_length=40)
    country: str = Field(default="", max_length=100)
    state: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class MfaChallengeInput(BaseModel):
    challenge_token: str
    code: str = Field(min_length=6, max_length=32)


class MfaPasswordCodeInput(BaseModel):
    password: str
    code: str = Field(min_length=6, max_length=32)


class MfaPasswordInput(BaseModel):
    password: str


class MfaEnableInput(BaseModel):
    code: str = Field(pattern="^[0-9]{6}$")


class RefreshInput(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=12, max_length=128)


def token_pair(db: Session, user: User):
    token_id = str(uuid4())
    expires_at = datetime.now(UTC) + timedelta(days=14)
    session = AuthSession(user_id=user.id, token_id=token_id, expires_at=expires_at)
    db.add(session)
    db.flush()
    return {
        "access_token": create_access_token(user.id, user.role, token_id),
        "refresh_token": create_refresh_token(user.id, token_id, expires_at),
        "token_type": "bearer",
        "expires_in": settings.jwt_expires_minutes * 60,
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }


def consume_totp_counter(db: Session, user: User, code: str) -> bool:
    if not user.mfa_secret_encrypted:
        return False
    try:
        secret = decrypt_totp_secret(user.mfa_secret_encrypted)
    except ValueError:
        return False
    counter = matching_counter(secret, code)
    if counter is None:
        return False
    result = db.execute(
        update(User)
        .where(
            User.id == user.id,
            or_(User.mfa_last_counter.is_(None), User.mfa_last_counter < counter),
        )
        .values(mfa_last_counter=counter, mfa_failed_attempts=0, mfa_locked_until=None)
    )
    return result.rowcount == 1


def consume_mfa_code(db: Session, user: User, code: str) -> bool:
    if len(code) == 6 and code.isascii() and code.isdigit():
        return consume_totp_counter(db, user, code)
    if not user.mfa_recovery_codes_hashes:
        return False
    try:
        hashes = json.loads(user.mfa_recovery_codes_hashes)
    except json.JSONDecodeError:
        return False
    digest = hashlib.sha256(code.strip().upper().encode("ascii", errors="ignore")).hexdigest()
    for index, expected in enumerate(hashes):
        if hmac.compare_digest(str(expected), digest):
            user.mfa_recovery_codes_hashes = json.dumps(hashes[:index] + hashes[index + 1 :])
            user.mfa_failed_attempts = 0
            user.mfa_locked_until = None
            return True
    return False


def register_mfa_failure(db: Session, user: User):
    now = datetime.now(UTC)
    lock_until = user.mfa_locked_until
    if lock_until and lock_until.tzinfo is None:
        lock_until = lock_until.replace(tzinfo=UTC)
    if lock_until and lock_until > now:
        raise HTTPException(429, "MFA verification is temporarily locked. Try again later.")
    if lock_until:
        user.mfa_failed_attempts = 0
        user.mfa_locked_until = None
    user.mfa_failed_attempts += 1
    if user.mfa_failed_attempts >= 5:
        user.mfa_locked_until = now + timedelta(minutes=15)
    db.commit()
    if user.mfa_locked_until:
        raise HTTPException(429, "Too many MFA attempts. Try again in 15 minutes.")
    raise HTTPException(401, "Authenticator code is invalid or already used")


@router.post("/register", status_code=201)
def register(body: RegisterInput, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account already exists for this email")
    user = User(email=email, password_hash=hash_password(body.password), role="customer")
    db.add(user)
    db.flush()
    customer = Customer(
        user_id=user.id,
        full_name=body.full_name,
        phone=body.phone,
        country=body.country,
        state=body.state,
        city=body.city,
    )
    db.add(customer)
    db.flush()
    account = Account(customer_id=customer.id, account_number=f"FSX{customer.id:010d}", balance=0)
    db.add(account)
    db.add(Wallet(customer_id=customer.id, balance=0))
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
def login(body: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    if user.mfa_enabled:
        if not user.mfa_secret_encrypted:
            raise HTTPException(503, "MFA is enabled but unavailable. Contact support.")
        challenge = jwt.encode(
            {"sub": str(user.id), "typ": "mfa_challenge", "exp": datetime.now(UTC) + timedelta(minutes=5)},
            settings.jwt_secret,
            algorithm="HS256",
        )
        return {"mfa_required": True, "challenge_token": challenge, "expires_in": 300}
    result = token_pair(db, user)
    db.commit()
    return result


@router.post("/mfa/verify")
def verify_mfa(body: MfaChallengeInput, db: Session = Depends(get_db)):
    try:
        claims = jwt.decode(body.challenge_token, settings.jwt_secret, algorithms=["HS256"])
        if claims.get("typ") != "mfa_challenge":
            raise jwt.InvalidTokenError("Wrong challenge type")
        user = db.get(User, int(claims["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(401, "MFA challenge is invalid or expired")
    if not user or not user.is_active or not user.mfa_enabled:
        raise HTTPException(401, "MFA challenge is invalid or expired")
    lock_until = user.mfa_locked_until
    if lock_until and lock_until.tzinfo is None:
        lock_until = lock_until.replace(tzinfo=UTC)
    if lock_until and lock_until > datetime.now(UTC):
        raise HTTPException(429, "MFA verification is temporarily locked. Try again later.")
    if not consume_mfa_code(db, user, body.code):
        register_mfa_failure(db, user)
    result = token_pair(db, user)
    db.commit()
    return result


@router.post("/mfa/setup")
def setup_mfa(body: MfaPasswordInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Password is incorrect")
    if user.mfa_enabled:
        raise HTTPException(409, "MFA is already enabled")
    secret = new_totp_secret()
    recovery_codes = [secrets.token_hex(5).upper() for _ in range(10)]
    user.mfa_secret_encrypted = encrypt_totp_secret(secret)
    user.mfa_recovery_codes_hashes = json.dumps([hashlib.sha256(code.encode()).hexdigest() for code in recovery_codes])
    user.mfa_last_counter = None
    user.mfa_failed_attempts = 0
    user.mfa_locked_until = None
    db.commit()
    return {"secret": secret, "provisioning_uri": provisioning_uri(secret, user.email), "recovery_codes": recovery_codes, "issuer": "FinSphere X", "message": "Save these one-time recovery codes securely. Add the account to an authenticator app, then confirm a code to enable MFA."}


@router.post("/mfa/enable")
def enable_mfa(body: MfaEnableInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.mfa_enabled:
        raise HTTPException(409, "MFA is already enabled")
    if not user.mfa_secret_encrypted:
        raise HTTPException(409, "Start authenticator setup before enabling MFA")
    if not consume_totp_counter(db, user, body.code):
        register_mfa_failure(db, user)
    user.mfa_enabled = True
    for session in db.query(AuthSession).filter_by(user_id=user.id).all():
        if not session.revoked_at:
            session.revoked_at = datetime.now(UTC)
    db.add(AuditLog(user_id=user.id, action="auth.mfa_enabled", resource="user", resource_id=str(user.id)))
    db.commit()
    return {"enabled": True, "message": "MFA enabled. Sign in again using your authenticator code."}


@router.post("/mfa/disable")
def disable_mfa(body: MfaPasswordCodeInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not user.mfa_enabled:
        raise HTTPException(409, "MFA is not enabled")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Password is incorrect")
    if not consume_mfa_code(db, user, body.code):
        register_mfa_failure(db, user)
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.mfa_recovery_codes_hashes = None
    user.mfa_last_counter = None
    for session in db.query(AuthSession).filter_by(user_id=user.id).all():
        if not session.revoked_at:
            session.revoked_at = datetime.now(UTC)
    db.add(AuditLog(user_id=user.id, action="auth.mfa_disabled", resource="user", resource_id=str(user.id)))
    db.commit()
    return {"enabled": False, "message": "MFA disabled. Sign in again."}


@router.get("/mfa/status")
def mfa_status(user: User = Depends(current_user)):
    return {"enabled": user.mfa_enabled}


@router.post("/password-reset/request")
def request_password_reset(body: PasswordResetRequest, db: Session = Depends(get_db)):
    configured = bool(settings.smtp_host and settings.smtp_from_email)
    user = db.query(User).filter_by(email=body.email.lower()).first()
    if user and configured:
        expires = datetime.now(UTC) + timedelta(minutes=20)
        token = jwt.encode(
            {
                "sub": str(user.id),
                "version": user.password_reset_version,
                "typ": "password_reset",
                "exp": expires,
            },
            settings.jwt_secret,
            algorithm="HS256",
        )
        link = f"{settings.web_origin.rstrip('/')}/reset-password?token={quote(token, safe='')}"
        message = EmailMessage()
        message["Subject"] = "Reset your FinSphere X password"
        message["From"] = settings.smtp_from_email
        message["To"] = user.email
        message.set_content(
            f"Use this one-time link within 20 minutes to reset your password:\n\n{link}\n\n"
            "If you did not request this change, you can ignore this email."
        )
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=8) as server:
                server.starttls()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
        except (OSError, smtplib.SMTPException):
            raise HTTPException(503, "Password reset email could not be delivered")
    return {
        "message": "If that account exists, password reset instructions will be sent.",
        "email_delivery_configured": configured,
    }


@router.post("/password-reset/confirm")
def confirm_password_reset(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    try:
        claims = jwt.decode(body.token, settings.jwt_secret, algorithms=["HS256"])
        if claims.get("typ") != "password_reset":
            raise jwt.InvalidTokenError("Wrong token type")
        user = db.get(User, int(claims["sub"]))
        if not user or int(claims["version"]) != user.password_reset_version:
            raise jwt.InvalidTokenError("Reset token already used")
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            400, "Password reset link is invalid, expired, or already used"
        )

    user.password_hash = hash_password(body.new_password)
    user.password_reset_version += 1
    for session in db.query(AuthSession).filter_by(user_id=user.id).all():
        if not session.revoked_at:
            session.revoked_at = datetime.now(UTC)
    db.commit()
    return {"message": "Password updated. Sign in with your new password."}


@router.post("/refresh")
def refresh(body: RefreshInput, db: Session = Depends(get_db)):
    import jwt

    try:
        claims = jwt.decode(body.refresh_token, settings.jwt_secret, algorithms=["HS256"])
        if claims.get("typ") != "refresh":
            raise jwt.InvalidTokenError("Wrong token type")
        token_id = str(claims["sid"])
        user_id = int(claims["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Refresh token is invalid or expired")
    session = db.query(AuthSession).filter_by(token_id=token_id, user_id=user_id).first()
    user = db.get(User, user_id)
    if not session or session.revoked_at or not user or not user.is_active:
        raise HTTPException(401, "Refresh session has expired; sign in again")
    session.revoked_at = datetime.now(UTC)
    result = token_pair(db, user)
    db.commit()
    return result


@router.post("/logout")
def logout(body: RefreshInput, db: Session = Depends(get_db)):
    import jwt

    try:
        claims = jwt.decode(body.refresh_token, settings.jwt_secret, algorithms=["HS256"])
        if claims.get("typ") != "refresh":
            raise jwt.InvalidTokenError("Wrong session")
    except (jwt.PyJWTError, KeyError, ValueError):
        return {"status": "signed_out"}
    session = (
        db.query(AuthSession).filter_by(token_id=claims["sid"], user_id=int(claims["sub"])).first()
    )
    if session and not session.revoked_at:
        session.revoked_at = datetime.now(UTC)
        db.commit()
    return {"status": "signed_out"}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    access_token: str = Depends(oauth2_scheme),
):
    try:
        claims = jwt.decode(access_token, settings.jwt_secret, algorithms=["HS256"])
        current_token_id = str(claims.get("sid", ""))
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Please sign in") from exc
    now = datetime.now(UTC)
    rows = db.query(AuthSession).filter_by(user_id=user.id).order_by(AuthSession.created_at.desc()).all()
    active = []
    for row in rows:
        expires_at = row.expires_at.replace(tzinfo=UTC) if row.expires_at.tzinfo is None else row.expires_at
        if not row.revoked_at and expires_at > now:
            active.append({"id": row.id, "created_at": row.created_at, "expires_at": row.expires_at, "current": row.token_id == current_token_id})
    return {"sessions": active}


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    access_token: str = Depends(oauth2_scheme),
):
    row = db.query(AuthSession).filter_by(id=session_id, user_id=user.id).first()
    if not row or row.revoked_at:
        raise HTTPException(404, "Session not found")
    try:
        claims = jwt.decode(access_token, settings.jwt_secret, algorithms=["HS256"])
        is_current = row.token_id == str(claims.get("sid", ""))
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Please sign in") from exc
    row.revoked_at = datetime.now(UTC)
    db.add(AuditLog(user_id=user.id, action="auth.session_revoked", resource="auth_session", resource_id=str(row.id)))
    db.commit()
    return {"id": row.id, "revoked": True, "current_session": is_current}
