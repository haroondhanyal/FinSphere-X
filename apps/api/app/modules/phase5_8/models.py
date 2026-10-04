from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class LoanApplication(Base):
    __tablename__ = "loan_applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    product_code: Mapped[str] = mapped_column(String(60), default="personal")
    purpose: Mapped[str] = mapped_column(String(240))
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    term_months: Mapped[int] = mapped_column(Integer)
    annual_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("18.0"))
    monthly_payment: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    illustrative_score: Mapped[int] = mapped_column(Integer, default=0)
    score_reasons: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="submitted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class BusinessOrganization(Base):
    __tablename__ = "business_organizations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(40), default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class BusinessInvoice(Base):
    __tablename__ = "business_invoices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("business_organizations.id"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(180))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    status: Mapped[str] = mapped_column(String(30), default="issued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class MerchantSettlement(Base):
    __tablename__ = "merchant_settlements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("business_organizations.id"), index=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    net_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(80))
    ledger_total: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    external_total: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    status: Mapped[str] = mapped_column(String(30), default="matched")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class RiskCase(Base):
    __tablename__ = "risk_cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    category: Mapped[str] = mapped_column(String(60))
    summary: Mapped[str] = mapped_column(String(500))
    score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="open")
    decision: Mapped[str] = mapped_column(String(60), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    evidence_reference: Mapped[str] = mapped_column(String(240), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class LoanInstallment(Base):
    __tablename__ = "loan_installments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loan_applications.id"), index=True)
    installment_number: Mapped[int] = mapped_column(Integer)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BnplPlan(Base):
    __tablename__ = "bnpl_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    merchant_name: Mapped[str] = mapped_column(String(180))
    purchase_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    installment_count: Mapped[int] = mapped_column(Integer, default=4)
    installment_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class BnplInstallment(Base):
    __tablename__ = "bnpl_installments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("bnpl_plans.id"), index=True)
    installment_number: Mapped[int] = mapped_column(Integer)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PayrollBatch(Base):
    __tablename__ = "payroll_batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("business_organizations.id"), index=True)
    pay_period: Mapped[str] = mapped_column(String(20))
    employee_count: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    status: Mapped[str] = mapped_column(String(30), default="pending_approval")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class FeeRule(Base):
    __tablename__ = "fee_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(240))
    percentage: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ScreeningRun(Base):
    __tablename__ = "screening_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject_name: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(40))
    score: Mapped[int] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(40))
    rationale: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class LoanProduct(Base):
    __tablename__ = "loan_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(240))
    annual_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    minimum_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    maximum_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    minimum_term_months: Mapped[int] = mapped_column(Integer, default=3)
    maximum_term_months: Mapped[int] = mapped_column(Integer, default=360)
    active: Mapped[bool] = mapped_column(default=True)


class BusinessExpenseClaim(Base):
    __tablename__ = "business_expense_claims"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("business_organizations.id"), index=True)
    claimant_name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(String(240))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    evidence_reference: Mapped[str] = mapped_column(String(240), default="")
    status: Mapped[str] = mapped_column(String(30), default="pending_approval")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class MerchantSale(Base):
    __tablename__ = "merchant_sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("business_organizations.id"), index=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(240))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    status: Mapped[str] = mapped_column(String(30), default="captured_demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class MerchantDispute(Base):
    __tablename__ = "merchant_disputes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("business_organizations.id"), index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("merchant_sales.id"), index=True)
    reason: Mapped[str] = mapped_column(String(240))
    evidence_reference: Mapped[str] = mapped_column(String(240), default="")
    status: Mapped[str] = mapped_column(String(30), default="open")
    decision: Mapped[str] = mapped_column(String(60), default="")
    decision_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
