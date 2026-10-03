from decimal import Decimal

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.modules.accounts import models as account_models  # noqa: F401
from app.modules.accounts.models import Account, Wallet
from app.modules.cards import models as card_models  # noqa: F401
from app.modules.identity.models import Customer, RolePermission, User

Base.metadata.create_all(bind=engine)

roles = {
    "customer": ["accounts:read:self", "payments:create:self", "cards:manage:self"],
    "operations": ["customers:read", "payments:read", "kyc:review"],
    "admin": ["customers:read", "kyc:review", "roles:manage", "products:manage", "audit:read"],
}

with SessionLocal() as db:
    for role, permissions in roles.items():
        for permission in permissions:
            if not db.query(RolePermission).filter_by(role=role, permission=permission).first():
                db.add(RolePermission(role=role, permission=permission))
    for email, name, role in (
        ("customer@finspherex.com", "Amina Demo", "customer"),
        ("operations@finspherex.com", "Operations Demo", "operations"),
        ("admin@finspherex.com", "Admin Demo", "admin"),
    ):
        user = db.query(User).filter_by(email=email).first()
        if user:
            continue
        user = User(email=email, password_hash=hash_password("FinSphere-Demo-2026!"), role=role)
        db.add(user)
        db.flush()
        customer = Customer(user_id=user.id, full_name=name, kyc_status="approved")
        db.add(customer)
        db.flush()
        db.add(
            Account(
                customer_id=customer.id,
                account_number=f"FSX{customer.id:010d}",
                balance=Decimal("250000.00"),
                currency="PKR",
            )
        )
        db.add(
            Wallet(
                customer_id=customer.id,
                balance=Decimal("12500.00"),
                currency="PKR",
                level="verified",
            )
        )
    db.commit()

print("Seeded demo users (password: FinSphere-Demo-2026!)")
