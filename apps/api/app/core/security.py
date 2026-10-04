import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt, expected = encoded.split("$", 2)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000)
        return scheme == "pbkdf2_sha256" and hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str, session_id: str | None = None) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    claims = {"sub": str(user_id), "role": role, "typ": "access", "exp": expires}
    if session_id:
        claims["sid"] = session_id
    return jwt.encode(
        claims,
        settings.jwt_secret,
        algorithm="HS256",
    )


def create_refresh_token(user_id: int, token_id: str, expires_at: datetime) -> str:
    return jwt.encode(
        {"sub": str(user_id), "sid": token_id, "typ": "refresh", "exp": expires_at},
        settings.jwt_secret,
        algorithm="HS256",
    )


def current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.modules.identity.models import AuthSession, User

    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in")
    if not token:
        raise unauthorized
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if claims.get("typ") != "access":
            raise jwt.InvalidTokenError("Wrong token type")
        user_id = int(claims["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise unauthorized
    session_id = claims.get("sid")
    if session_id:
        session = db.query(AuthSession).filter_by(token_id=str(session_id), user_id=user_id).first()
        if (
            not session
            or session.revoked_at
            or (session.expires_at.replace(tzinfo=UTC) if session.expires_at.tzinfo is None else session.expires_at) <= datetime.now(UTC)
        ):
            raise unauthorized
    return user


def require_roles(*roles: str):
    def guard(user=Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=403, detail="You do not have permission for this action"
            )
        return user

    return guard


def require_permission(permission: str):
    def guard(user=Depends(current_user), db: Session = Depends(get_db)):
        from app.modules.identity.models import RolePermission

        granted = db.query(RolePermission).filter_by(role=user.role, permission=permission).first()
        if not granted:
            raise HTTPException(
                status_code=403, detail="You do not have permission for this action"
            )
        return user

    return guard
