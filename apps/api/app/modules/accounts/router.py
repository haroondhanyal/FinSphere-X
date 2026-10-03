from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import current_user
from app.modules.accounts.models import Account, Beneficiary, Wallet
from app.modules.customers.router import customer_for
from app.modules.identity.models import User

router = APIRouter(tags=["Accounts and wallet"])


class AccountInput(BaseModel):
    account_type: str = Field(default="current", pattern="^(current|savings|salary)$")
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")


class BeneficiaryInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    account_number: str = Field(min_length=6, max_length=34)
    bank_name: str = Field(default="FinSphere X", max_length=120)
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")


def serialize_account(account: Account):
    number = account.account_number
    return {
        "id": account.id,
        "account_number_masked": f"••••{number[-4:]}",
        "account_type": account.account_type,
        "currency": account.currency,
        "balance": str(account.balance),
        "status": account.status,
    }


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    return [
        serialize_account(a) for a in db.query(Account).filter_by(customer_id=customer.id).all()
    ]


@router.get("/accounts/{account_id}")
def get_account(account_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    account = db.query(Account).filter_by(id=account_id, customer_id=customer.id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    return serialize_account(account)


@router.post("/accounts", status_code=201)
def create_account(
    body: AccountInput, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    account = Account(
        customer_id=customer.id,
        account_number=f"FSX{customer.id:06d}{db.query(Account).filter_by(customer_id=customer.id).count() + 1:04d}",
        account_type=body.account_type,
        currency=body.currency,
        balance=Decimal("0"),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return serialize_account(account)


@router.get("/wallet")
def get_wallet(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    wallet = db.query(Wallet).filter_by(customer_id=customer.id).first()
    if not wallet:
        wallet = Wallet(customer_id=customer.id)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return {
        "id": wallet.id,
        "currency": wallet.currency,
        "balance": str(wallet.balance),
        "level": wallet.level,
        "status": wallet.status,
        "limits": {"daily_transfer": "50000.00", "monthly_transfer": "200000.00"},
    }


@router.get("/beneficiaries")
def list_beneficiaries(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    items = db.query(Beneficiary).filter_by(customer_id=customer.id).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "account_number_masked": f"••••{b.account_number[-4:]}",
            "bank_name": b.bank_name,
            "currency": b.currency,
            "is_verified": b.is_verified,
        }
        for b in items
    ]


@router.post("/beneficiaries", status_code=201)
def add_beneficiary(
    body: BeneficiaryInput, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    beneficiary = Beneficiary(
        customer_id=customer.id,
        name=body.name,
        account_number=body.account_number,
        bank_name=body.bank_name,
        currency=body.currency,
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return {"id": beneficiary.id, "name": beneficiary.name, "is_verified": beneficiary.is_verified}


@router.post("/beneficiaries/{beneficiary_id}/verify")
def verify_beneficiary(
    beneficiary_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    beneficiary = (
        db.query(Beneficiary).filter_by(id=beneficiary_id, customer_id=customer.id).first()
    )
    if not beneficiary:
        raise HTTPException(404, "Beneficiary not found")
    beneficiary.is_verified = True
    db.commit()
    return {"id": beneficiary.id, "is_verified": beneficiary.is_verified}
