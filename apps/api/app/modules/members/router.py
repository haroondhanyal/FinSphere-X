from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, require_permission
from app.modules.accounts.models import Account, Wallet
from app.modules.identity.models import AuditLog, AuthSession, Customer, User
from app.modules.phase5_8.models import BusinessOrganization

router = APIRouter(prefix="/admin/members", tags=["Member management"])
ASSIGNABLE_ROLES = ("customer", "operations", "admin", "business", "merchant")


class MemberCreateInput(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role: str = Field(pattern="^(customer|operations|admin|business|merchant)$")
    phone: str = Field(default="", max_length=40)
    country: str = Field(default="", max_length=100)
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")
    legal_name: str = Field(default="", max_length=180)


class MemberStatusInput(BaseModel):
    is_active: bool


def serialize_member(user: User, account_count: int = 0):
    customer = user.customer
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "full_name": customer.full_name if customer else "",
        "phone": customer.phone if customer else "",
        "kyc_status": customer.kyc_status if customer else "not_applicable",
        "account_count": account_count,
        "created_at": user.created_at,
    }


@router.get("")
def list_members(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_permission("roles:manage")),
):
    users = db.query(User).order_by(User.created_at.desc(), User.id.desc()).all()
    customer_ids = [user.customer.id for user in users if user.customer]
    account_counts = dict(
        db.query(Account.customer_id, func.count(Account.id))
        .filter(Account.customer_id.in_(customer_ids))
        .group_by(Account.customer_id)
        .all()
    ) if customer_ids else {}
    return [
        serialize_member(
            user,
            account_counts.get(user.customer.id, 0) if user.customer else 0,
        )
        for user in users
    ]


@router.post("", status_code=201)
def create_member(
    body: MemberCreateInput,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("roles:manage")),
):
    email = str(body.email).lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account already exists for this email")
    full_name = body.full_name.strip()
    if len(full_name) < 2:
        raise HTTPException(422, "Full name must contain at least two characters")
    if body.role in ("business", "merchant") and len(body.legal_name.strip()) < 2:
        raise HTTPException(422, "A legal organization name is required for this role")

    user = User(email=email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.flush()
    customer = Customer(
        user_id=user.id,
        full_name=full_name,
        phone=body.phone.strip(),
        country=body.country.strip(),
        kyc_status="pending" if body.role == "customer" else "approved",
    )
    db.add(customer)
    db.flush()
    db.add(
        Account(
            customer_id=customer.id,
            account_number=f"FSX{customer.id:010d}",
            account_type="current",
            currency=body.currency,
            balance=0,
        )
    )
    db.add(Wallet(customer_id=customer.id, currency=body.currency))
    if body.role in ("business", "merchant"):
        db.add(
            BusinessOrganization(
                user_id=user.id,
                legal_name=body.legal_name.strip(),
                status="pending_review",
            )
        )
    db.add(
        AuditLog(
            user_id=admin.id,
            action="member.created",
            resource="user",
            resource_id=str(user.id),
            detail=f"role={body.role}; email={email}",
        )
    )
    db.commit()
    db.refresh(user)
    return serialize_member(user, 1)


@router.patch("/{user_id}/status")
def update_member_status(
    user_id: int,
    body: MemberStatusInput,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission("roles:manage")),
):
    if user_id == admin.id and not body.is_active:
        raise HTTPException(409, "You cannot suspend your own account")
    member = db.get(User, user_id)
    if not member:
        raise HTTPException(404, "Member not found")
    if member.is_active and not body.is_active and member.role == "admin":
        active_admins = db.query(User).filter_by(role="admin", is_active=True).count()
        if active_admins <= 1:
            raise HTTPException(409, "The last active admin cannot be suspended")
    member.is_active = body.is_active
    if not body.is_active:
        for session in db.query(AuthSession).filter_by(user_id=member.id).all():
            if not session.revoked_at:
                session.revoked_at = datetime.now(UTC)
    db.add(
        AuditLog(
            user_id=admin.id,
            action="member.status_updated",
            resource="user",
            resource_id=str(member.id),
            detail=f"is_active={body.is_active}",
        )
    )
    db.commit()
    return {"id": member.id, "is_active": member.is_active}
