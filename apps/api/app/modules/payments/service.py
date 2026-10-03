from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.accounts.models import (
    Account,
    Beneficiary,
    FinancialTransaction,
    JournalEntry,
    JournalLine,
    LedgerAccount,
)
from app.modules.identity.models import AuditLog, Customer


def replay_matches(
    transaction: FinancialTransaction,
    customer: Customer,
    source: Account,
    amount: Decimal,
    beneficiary: Beneficiary | None,
    destination: Account | None,
    transaction_type: str,
) -> bool:
    return (
        transaction.customer_id == customer.id
        and transaction.source_account_id == source.id
        and transaction.amount == amount
        and transaction.destination_account_id == (destination.id if destination else None)
        and transaction.beneficiary_id == (beneficiary.id if beneficiary else None)
        and transaction.transaction_type == transaction_type
    )


def post_transfer(
    db: Session,
    customer: Customer,
    source: Account,
    amount: Decimal,
    idempotency_key: str,
    beneficiary: Beneficiary | None = None,
    destination: Account | None = None,
    transaction_type: str = "transfer",
):
    existing = db.query(FinancialTransaction).filter_by(idempotency_key=idempotency_key).first()
    if existing:
        if not replay_matches(
            existing, customer, source, amount, beneficiary, destination, transaction_type
        ):
            raise HTTPException(409, "Idempotency key was already used for a different request")
        return existing
    if source.status != "active":
        raise HTTPException(409, "Source account is not active")
    if amount <= 0 or amount.quantize(Decimal("0.0001")) != amount:
        raise HTTPException(422, "Amount must be positive with at most four decimal places")
    if source.balance < amount:
        raise HTTPException(422, "Insufficient available balance")
    if destination and destination.currency != source.currency:
        raise HTTPException(422, "Source and destination currencies must match in this release")
    if beneficiary and beneficiary.currency != source.currency:
        raise HTTPException(422, "Beneficiary currency must match the source account")

    reference = f"FSX-{uuid4().hex[:12].upper()}"
    tx = FinancialTransaction(
        reference=reference,
        idempotency_key=idempotency_key,
        customer_id=customer.id,
        source_account_id=source.id,
        destination_account_id=destination.id if destination else None,
        beneficiary_id=beneficiary.id if beneficiary else None,
        transaction_type=transaction_type,
        amount=amount,
        currency=source.currency,
        status="posted",
    )
    source.balance -= amount
    if destination:
        destination.balance += amount
    db.add(tx)
    db.flush()

    source_gl = db.query(LedgerAccount).filter_by(account_id=source.id).first()
    if not source_gl:
        source_gl = LedgerAccount(
            account_id=source.id,
            code=f"customer-account:{source.id}",
            name=f"Customer account {source.id}",
            currency=source.currency,
        )
        db.add(source_gl)
        db.flush()
    if destination:
        destination_gl = db.query(LedgerAccount).filter_by(account_id=destination.id).first()
        if not destination_gl:
            destination_gl = LedgerAccount(
                account_id=destination.id,
                code=f"customer-account:{destination.id}",
                name=f"Customer account {destination.id}",
                currency=destination.currency,
            )
            db.add(destination_gl)
            db.flush()
    else:
        destination_gl = (
            db.query(LedgerAccount).filter_by(code=f"external-clearing:{source.currency}").first()
        )
        if not destination_gl:
            destination_gl = LedgerAccount(
                code=f"external-clearing:{source.currency}",
                name=f"External clearing {source.currency}",
                currency=source.currency,
            )
            db.add(destination_gl)
            db.flush()

    entry = JournalEntry(transaction_id=tx.id, reference=reference)
    db.add(entry)
    db.flush()
    db.add_all(
        [
            JournalLine(
                journal_entry_id=entry.id,
                ledger_account_id=source_gl.id,
                debit=amount,
                credit=Decimal("0"),
            ),
            JournalLine(
                journal_entry_id=entry.id,
                ledger_account_id=destination_gl.id,
                debit=Decimal("0"),
                credit=amount,
            ),
        ]
    )
    db.add(
        AuditLog(
            user_id=customer.user_id,
            action="transaction.posted",
            resource=transaction_type,
            resource_id=str(tx.id),
            detail=reference,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(FinancialTransaction).filter_by(idempotency_key=idempotency_key).first()
        if existing and replay_matches(
            existing, customer, source, amount, beneficiary, destination, transaction_type
        ):
            return existing
        raise HTTPException(
            409, "A concurrent posting conflict occurred; retry with the same idempotency key"
        )
    db.refresh(tx)
    return tx
