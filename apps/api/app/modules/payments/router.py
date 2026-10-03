import csv
from decimal import Decimal, InvalidOperation
from io import StringIO

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import current_user
from app.modules.accounts.models import (
    Account,
    Beneficiary,
    FinancialTransaction,
    JournalEntry,
    JournalLine,
    LedgerAccount,
    Wallet,
)
from app.modules.customers.router import customer_for
from app.modules.identity.models import AuditLog, User
from app.modules.payments.service import post_transfer

router = APIRouter(tags=["Payments and transfers"])


class TransferInput(BaseModel):
    source_account_id: int
    beneficiary_id: int
    amount: str = Field(min_length=1, max_length=32)
    purpose: str = Field(default="Transfer", max_length=100)


class WalletMoveInput(BaseModel):
    account_id: int
    direction: str = Field(pattern="^(deposit|withdraw)$")
    amount: str = Field(min_length=1, max_length=32)


@router.post("/wallet/transfers", status_code=201)
def wallet_transfer(
    body: WalletMoveInput,
    idempotency_key: str = Header(min_length=8, max_length=120),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    customer = customer_for(db, user)
    account = (
        db.query(Account)
        .filter_by(id=body.account_id, customer_id=customer.id)
        .with_for_update()
        .first()
    )
    wallet = db.query(Wallet).filter_by(customer_id=customer.id).with_for_update().first()
    if not account or not wallet:
        raise HTTPException(404, "Account or wallet not found")
    try:
        amount = Decimal(body.amount)
    except InvalidOperation:
        raise HTTPException(422, "Amount must be a valid decimal")
    key = f"wallet:{idempotency_key}"
    existing = db.query(FinancialTransaction).filter_by(idempotency_key=key).first()
    if existing:
        if (
            existing.customer_id != customer.id
            or existing.source_account_id != account.id
            or existing.amount != amount
            or existing.transaction_type != f"wallet_{body.direction}"
        ):
            raise HTTPException(409, "Idempotency key was already used for a different request")
        return {
            "id": existing.id,
            "reference": existing.reference,
            "amount": str(existing.amount),
            "status": existing.status,
        }
    if amount <= 0 or amount.quantize(Decimal("0.0001")) != amount:
        raise HTTPException(422, "Amount must be positive with at most four decimal places")
    if account.currency != wallet.currency:
        raise HTTPException(422, "Wallet and linked account currency must match")
    if body.direction == "deposit" and account.balance < amount:
        raise HTTPException(422, "Insufficient account balance")
    if body.direction == "withdraw" and wallet.balance < amount:
        raise HTTPException(422, "Insufficient wallet balance")
    from uuid import uuid4

    reference = f"FSX-{uuid4().hex[:12].upper()}"
    transaction_type = f"wallet_{body.direction}"
    tx = FinancialTransaction(
        reference=reference,
        idempotency_key=key,
        customer_id=customer.id,
        source_account_id=account.id,
        transaction_type=transaction_type,
        amount=amount,
        currency=account.currency,
        status="posted",
    )
    if body.direction == "deposit":
        account.balance -= amount
        wallet.balance += amount
    else:
        wallet.balance -= amount
        account.balance += amount
    db.add(tx)
    db.flush()
    bank_gl = db.query(LedgerAccount).filter_by(account_id=account.id).first()
    if not bank_gl:
        bank_gl = LedgerAccount(
            account_id=account.id,
            code=f"customer-account:{account.id}",
            name=f"Customer account {account.id}",
            currency=account.currency,
        )
        db.add(bank_gl)
        db.flush()
    wallet_gl = db.query(LedgerAccount).filter_by(code=f"customer-wallet:{customer.id}").first()
    if not wallet_gl:
        wallet_gl = LedgerAccount(
            code=f"customer-wallet:{customer.id}",
            name=f"Customer wallet {customer.id}",
            currency=wallet.currency,
        )
        db.add(wallet_gl)
        db.flush()
    entry = JournalEntry(transaction_id=tx.id, reference=reference)
    db.add(entry)
    db.flush()
    if body.direction == "deposit":
        lines = [
            JournalLine(
                journal_entry_id=entry.id, ledger_account_id=bank_gl.id, debit=amount, credit=0
            ),
            JournalLine(
                journal_entry_id=entry.id, ledger_account_id=wallet_gl.id, debit=0, credit=amount
            ),
        ]
    else:
        lines = [
            JournalLine(
                journal_entry_id=entry.id, ledger_account_id=wallet_gl.id, debit=amount, credit=0
            ),
            JournalLine(
                journal_entry_id=entry.id, ledger_account_id=bank_gl.id, debit=0, credit=amount
            ),
        ]
    db.add_all(lines)
    db.add(
        AuditLog(
            user_id=user.id,
            action=f"wallet.{body.direction}",
            resource="wallet",
            resource_id=str(wallet.id),
            detail=reference,
        )
    )
    db.commit()
    return {"id": tx.id, "reference": tx.reference, "amount": str(tx.amount), "status": tx.status}


@router.post("/transfers", status_code=201)
def create_transfer(
    body: TransferInput,
    idempotency_key: str = Header(min_length=8, max_length=120),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    customer = customer_for(db, user)
    source = (
        db.query(Account)
        .filter_by(id=body.source_account_id, customer_id=customer.id)
        .with_for_update()
        .first()
    )
    beneficiary = (
        db.query(Beneficiary).filter_by(id=body.beneficiary_id, customer_id=customer.id).first()
    )
    if not source or not beneficiary:
        raise HTTPException(404, "Account or beneficiary not found")
    if not beneficiary.is_verified:
        raise HTTPException(409, "Verify this beneficiary before transferring")
    try:
        amount = Decimal(body.amount)
    except InvalidOperation:
        raise HTTPException(422, "Amount must be a valid decimal")
    destination = (
        db.query(Account)
        .filter_by(account_number=beneficiary.account_number)
        .with_for_update()
        .first()
    )
    tx = post_transfer(
        db,
        customer,
        source,
        amount,
        idempotency_key,
        beneficiary=beneficiary,
        destination=destination,
    )
    return {
        "id": tx.id,
        "reference": tx.reference,
        "amount": str(tx.amount),
        "currency": tx.currency,
        "status": tx.status,
        "created_at": tx.created_at,
    }


@router.post("/payments", status_code=201)
def create_payment(
    body: TransferInput,
    idempotency_key: str = Header(min_length=8, max_length=120),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    customer = customer_for(db, user)
    source = (
        db.query(Account)
        .filter_by(id=body.source_account_id, customer_id=customer.id)
        .with_for_update()
        .first()
    )
    beneficiary = (
        db.query(Beneficiary).filter_by(id=body.beneficiary_id, customer_id=customer.id).first()
    )
    if not source or not beneficiary or not beneficiary.is_verified:
        raise HTTPException(404, "Verified payment recipient not found")
    try:
        amount = Decimal(body.amount)
    except InvalidOperation:
        raise HTTPException(422, "Amount must be a valid decimal")
    tx = post_transfer(
        db,
        customer,
        source,
        amount,
        idempotency_key,
        beneficiary=beneficiary,
        transaction_type="payment",
    )
    return {
        "id": tx.id,
        "reference": tx.reference,
        "amount": str(tx.amount),
        "currency": tx.currency,
        "status": tx.status,
    }


@router.get("/transactions")
def list_transactions(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    rows = (
        db.query(FinancialTransaction)
        .filter_by(customer_id=customer.id)
        .order_by(FinancialTransaction.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": tx.id,
            "reference": tx.reference,
            "type": tx.transaction_type,
            "amount": str(tx.amount),
            "currency": tx.currency,
            "status": tx.status,
            "created_at": tx.created_at,
        }
        for tx in rows
    ]


@router.get("/accounts/{account_id}/statement")
def account_statement(
    account_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    account = db.query(Account).filter_by(id=account_id, customer_id=customer.id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    rows = (
        db.query(FinancialTransaction)
        .filter(
            or_(
                FinancialTransaction.source_account_id == account_id,
                FinancialTransaction.destination_account_id == account_id,
            )
        )
        .order_by(FinancialTransaction.created_at.desc())
        .all()
    )
    return {
        "account_id": account.id,
        "currency": account.currency,
        "closing_balance": str(account.balance),
        "transactions": [
            {
                "reference": tx.reference,
                "type": tx.transaction_type,
                "amount": str(tx.amount),
                "status": tx.status,
                "date": tx.created_at,
            }
            for tx in rows
        ],
    }


@router.get("/accounts/{account_id}/statement.csv")
def account_statement_csv(
    account_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    account = db.query(Account).filter_by(id=account_id, customer_id=customer.id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    rows = (
        db.query(FinancialTransaction)
        .filter(
            or_(
                FinancialTransaction.source_account_id == account_id,
                FinancialTransaction.destination_account_id == account_id,
            )
        )
        .order_by(FinancialTransaction.created_at.desc())
        .all()
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["reference", "type", "amount", "currency", "status", "created_at"])
    for tx in rows:
        writer.writerow(
            [
                tx.reference,
                tx.transaction_type,
                str(tx.amount),
                tx.currency,
                tx.status,
                tx.created_at.isoformat(),
            ]
        )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=statement-{account_id}.csv"},
    )


@router.get("/transactions/{transaction_id}/ledger")
def transaction_ledger(
    transaction_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    tx = (
        db.query(FinancialTransaction).filter_by(id=transaction_id, customer_id=customer.id).first()
    )
    if not tx:
        raise HTTPException(404, "Transaction not found")
    entry = db.query(JournalEntry).filter_by(transaction_id=tx.id).first()
    lines = db.query(JournalLine).filter_by(journal_entry_id=entry.id).all()
    return {
        "reference": entry.reference,
        "lines": [{"debit": str(line.debit), "credit": str(line.credit)} for line in lines],
    }
