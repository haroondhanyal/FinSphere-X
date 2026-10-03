from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    account_number: Mapped[str] = mapped_column(String(34), unique=True, index=True)
    account_type: Mapped[str] = mapped_column(String(40), default="current")
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Wallet(Base):
    __tablename__ = "wallets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), unique=True)
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0"))
    level: Mapped[str] = mapped_column(String(30), default="basic")
    status: Mapped[str] = mapped_column(String(30), default="active")


class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    account_number: Mapped[str] = mapped_column(String(34))
    bank_name: Mapped[str] = mapped_column(String(120), default="FinSphere X")
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class FinancialTransaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    source_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    destination_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    beneficiary_id: Mapped[int | None] = mapped_column(
        ForeignKey("beneficiaries.id"), nullable=True
    )
    transaction_type: Mapped[str] = mapped_column(String(40), default="transfer")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    fee: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    status: Mapped[str] = mapped_column(String(30), default="posted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), unique=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"), index=True)
    ledger_account_id: Mapped[int] = mapped_column(ForeignKey("ledger_accounts.id"))
    debit: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0"))
    credit: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0"))
