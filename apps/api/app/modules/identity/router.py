from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    current_user,
    hash_password,
    verify_password,
)
from app.modules.accounts.models import Account, Wallet
from app.modules.identity.models import AuthSession, Customer, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(default="", max_length=40)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class RefreshInput(BaseModel):
    refresh_token: str


def token_pair(db: Session, user: User):
    token_id = str(uuid4())
    expires_at = datetime.now(UTC) + timedelta(days=14)
    session = AuthSession(user_id=user.id, token_id=token_id, expires_at=expires_at)
    db.add(session)
    db.flush()
    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id, token_id, expires_at),
        "token_type": "bearer",
        "expires_in": settings.jwt_expires_minutes * 60,
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }


@router.post("/register", status_code=201)
def register(body: RegisterInput, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account already exists for this email")
    user = User(email=email, password_hash=hash_password(body.password), role="customer")
    db.add(user)
    db.flush()
    customer = Customer(user_id=user.id, full_name=body.full_name, phone=body.phone)
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
    result = token_pair(db, user)
    db.commit()
    return result


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
