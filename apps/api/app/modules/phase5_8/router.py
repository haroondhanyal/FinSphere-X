from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import current_user, require_roles
from app.modules.accounts.models import JournalEntry, JournalLine, LedgerAccount
from app.modules.customers.router import customer_for
from app.modules.identity.models import AuditLog, Customer, User
from app.modules.phase5_8.models import (
    BnplInstallment,
    BnplPlan,
    BusinessExpenseClaim,
    BusinessInvoice,
    BusinessOrganization,
    FeeRule,
    LoanApplication,
    LoanInstallment,
    LoanProduct,
    MerchantDispute,
    MerchantSale,
    MerchantSettlement,
    PayrollBatch,
    ReconciliationRun,
    RiskCase,
    ScreeningRun,
)

router = APIRouter(tags=["Loans, business, finance and risk"])
STAFF_ROLES = ("operations", "admin")
BUSINESS_ROLES = ("business", "merchant", "admin")


class LoanInput(BaseModel):
    product_code: str = Field(default="personal", min_length=2, max_length=60)
    purpose: str = Field(min_length=4, max_length=240)
    amount: Decimal = Field(gt=0, le=Decimal("100000000"))
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")
    term_months: int = Field(ge=3, le=360)


class LoanDecision(BaseModel):
    decision: str = Field(pattern="^(approved|declined|more_information_required)$")


class LoanProductInput(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern="^[a-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=2, max_length=240)
    annual_rate: Decimal = Field(ge=0, le=Decimal("100"))
    minimum_amount: Decimal = Field(gt=0)
    maximum_amount: Decimal = Field(gt=0)
    minimum_term_months: int = Field(ge=1, le=360)
    maximum_term_months: int = Field(ge=1, le=360)


class OrganizationInput(BaseModel):
    legal_name: str = Field(min_length=2, max_length=180)


class InvoiceInput(BaseModel):
    customer_name: str = Field(min_length=2, max_length=180)
    amount: Decimal = Field(gt=0, le=Decimal("1000000000"))
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")


class SettlementInput(BaseModel):
    gross_amount: Decimal = Field(gt=0, le=Decimal("1000000000"))
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")


class ReconciliationInput(BaseModel):
    source: str = Field(min_length=2, max_length=80)
    external_total: Decimal = Field(ge=0)
    notes: str = Field(default="", max_length=500)


class RiskCaseInput(BaseModel):
    customer_id: int = Field(gt=0)
    category: str = Field(min_length=2, max_length=60)
    summary: str = Field(min_length=8, max_length=500)
    score: int = Field(ge=0, le=100)


class RiskDecision(BaseModel):
    decision: str = Field(pattern="^(cleared|escalated|reported|false_positive)$")


class OrganizationDecision(BaseModel):
    decision: str = Field(pattern="^(active|rejected)$")


class BnplInput(BaseModel):
    merchant_name: str = Field(min_length=2, max_length=180)
    amount: Decimal = Field(gt=0, le=Decimal("10000000"))
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")
    installments: int = Field(default=4, ge=2, le=12)


class PayrollInput(BaseModel):
    pay_period: str = Field(pattern="^\\d{4}-(0[1-9]|1[0-2])$")
    employee_count: int = Field(gt=0, le=100000)
    total_amount: Decimal = Field(gt=0, le=Decimal("1000000000"))
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")


class PayrollDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


class FeeRuleInput(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern="^[a-z0-9_-]+$")
    description: str = Field(min_length=2, max_length=240)
    percentage: Decimal = Field(ge=0, le=Decimal("100"))


class ScreeningInput(BaseModel):
    subject_name: str = Field(min_length=2, max_length=180)
    category: str = Field(pattern="^(sanctions|pep|adverse_media)$")


class EvidenceInput(BaseModel):
    evidence_reference: str = Field(min_length=2, max_length=240)


class CaseNoteInput(BaseModel):
    note: str = Field(min_length=2, max_length=1000)


class ExpenseInput(BaseModel):
    claimant_name: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=2, max_length=240)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")
    evidence_reference: str = Field(default="", max_length=240)


class SaleInput(BaseModel):
    description: str = Field(min_length=2, max_length=240)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="PKR", pattern="^(PKR|USD|EUR|GBP|AED|SAR)$")


class DisputeInput(BaseModel):
    sale_id: int = Field(gt=0)
    reason: str = Field(min_length=4, max_length=240)
    evidence_reference: str = Field(default="", max_length=240)


class DisputeDecision(BaseModel):
    decision: str = Field(pattern="^(resolved|escalated)$")
    note: str = Field(min_length=5, max_length=1000)


class WorkDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected|resolved|escalated)$")


class InvoiceStatusInput(BaseModel):
    status: str = Field(pattern="^(paid|cancelled|refunded)$")


class SettlementReviewInput(BaseModel):
    decision: str = Field(pattern="^(matched|exception)$")


def serialize_loan(row: LoanApplication):
    return {
        "id": row.id,
        "product_code": row.product_code,
        "purpose": row.purpose,
        "amount": str(row.requested_amount),
        "currency": row.currency,
        "term_months": row.term_months,
        "annual_rate": str(row.annual_rate),
        "estimated_monthly_payment": str(row.monthly_payment),
        "illustrative_score": row.illustrative_score,
        "score_reasons": row.score_reasons,
        "status": row.status,
        "created_at": row.created_at,
        "disclosure": "Illustrative estimate only; not a credit decision or loan offer.",
    }


def organization_for(db: Session, user: User):
    organization = db.query(BusinessOrganization).filter_by(user_id=user.id).first()
    if not organization:
        raise HTTPException(404, "Business profile not found")
    return organization


@router.post("/loans/applications", status_code=201)
def apply_for_loan(body: LoanInput, db: Session = Depends(get_db), user: User = Depends(require_roles("customer"))):
    customer = customer_for(db, user)
    product = db.query(LoanProduct).filter_by(code=body.product_code, active=True).first()
    if not product:
        raise HTTPException(422, "Select an active loan product")
    if not product.minimum_amount <= body.amount <= product.maximum_amount:
        raise HTTPException(422, "Amount is outside the selected product range")
    if not product.minimum_term_months <= body.term_months <= product.maximum_term_months:
        raise HTTPException(422, "Term is outside the selected product range")
    rate = product.annual_rate / Decimal("100") / Decimal("12")
    if rate:
        factor = (Decimal("1") + rate) ** body.term_months
        payment = (body.amount * rate * factor / (factor - Decimal("1"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        payment = (body.amount / body.term_months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # Synthetic request-shape heuristic only. It does not use customer or bureau data.
    score = 84
    reasons = ["Synthetic starting value; no borrower data was evaluated"]
    if body.amount > Decimal("1000000"):
        score -= 15
        reasons.append("Requested amount exceeds the demo heuristic threshold")
    if body.term_months > 36:
        score -= 10
        reasons.append("Longer term exceeds the demo heuristic threshold")
    row = LoanApplication(
        customer_id=customer.id,
        product_code=product.code,
        purpose=body.purpose,
        requested_amount=body.amount,
        currency=body.currency,
        term_months=body.term_months,
        annual_rate=product.annual_rate,
        monthly_payment=payment,
        illustrative_score=score,
        score_reasons="; ".join(reasons),
    )
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="loan.submitted", resource="loan_application", detail=f"{body.currency}:{body.amount}"))
    db.commit()
    db.refresh(row)
    return serialize_loan(row)


@router.get("/loans/products")
def list_loan_products(db: Session = Depends(get_db), _user: User = Depends(current_user)):
    rows = db.query(LoanProduct).filter_by(active=True).order_by(LoanProduct.name).all()
    return [{"code": row.code, "name": row.name, "description": row.description, "annual_rate": str(row.annual_rate), "minimum_amount": str(row.minimum_amount), "maximum_amount": str(row.maximum_amount), "minimum_term_months": row.minimum_term_months, "maximum_term_months": row.maximum_term_months, "disclosure": "Illustrative example terms only; not a credit offer."} for row in rows]


@router.post("/loans/products", status_code=201)
def create_loan_product(body: LoanProductInput, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    if body.maximum_amount < body.minimum_amount or body.maximum_term_months < body.minimum_term_months:
        raise HTTPException(422, "Maximum bounds must be greater than or equal to minimum bounds")
    if db.query(LoanProduct).filter_by(code=body.code).first():
        raise HTTPException(409, "Loan product code already exists")
    product = LoanProduct(**body.model_dump())
    db.add(product)
    db.add(AuditLog(user_id=user.id, action="loan.product_created", resource="loan_product", detail=body.code))
    db.commit()
    db.refresh(product)
    return {"code": product.code, "name": product.name, "active": product.active}


@router.get("/loans/applications")
def list_loan_applications(
    db: Session = Depends(get_db), user: User = Depends(current_user)
):
    if user.role in STAFF_ROLES:
        rows = db.query(LoanApplication).order_by(LoanApplication.created_at.desc()).all()
    else:
        if user.role != "customer":
            raise HTTPException(403, "Loan applications are available to customer accounts")
        customer = customer_for(db, user)
        rows = db.query(LoanApplication).filter_by(customer_id=customer.id).order_by(
            LoanApplication.created_at.desc()
        ).all()
    return {
        "applications": [{**serialize_loan(row), "can_review": user.role in STAFF_ROLES} for row in rows],
        "can_review": user.role in STAFF_ROLES,
        "can_manage_products": user.role == "admin",
    }


@router.patch("/loans/applications/{application_id}")
def decide_loan(
    application_id: int,
    body: LoanDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF_ROLES)),
):
    row = db.get(LoanApplication, application_id)
    if not row:
        raise HTTPException(404, "Loan application not found")
    if row.status != "submitted":
        raise HTTPException(409, "Application has already been reviewed")
    row.status = body.decision
    if body.decision == "approved":
        first_due = datetime.now(UTC) + timedelta(days=30)
        for number in range(1, row.term_months + 1):
            db.add(LoanInstallment(
                loan_id=row.id,
                installment_number=number,
                due_at=first_due + timedelta(days=30 * (number - 1)),
                amount=row.monthly_payment,
            ))
    db.add(AuditLog(user_id=user.id, action="loan.reviewed", resource="loan_application", resource_id=str(row.id), detail=body.decision))
    db.commit()
    return serialize_loan(row)


def serialize_installment(row):
    return {"id": row.id, "installment_number": row.installment_number, "due_at": row.due_at, "amount": str(row.amount), "status": row.status}


@router.get("/loans/applications/{application_id}/schedule")
def loan_schedule(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    application = db.get(LoanApplication, application_id)
    if not application:
        raise HTTPException(404, "Loan application not found")
    if user.role not in STAFF_ROLES and (user.role != "customer" or not user.customer or user.customer.id != application.customer_id):
        raise HTTPException(404, "Loan application not found")
    return {"application": serialize_loan(application), "installments": [serialize_installment(row) for row in db.query(LoanInstallment).filter_by(loan_id=application.id).order_by(LoanInstallment.installment_number).all()]}


@router.get("/loans/collections")
def collections_queue(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(LoanInstallment).filter(LoanInstallment.status.in_(["scheduled", "overdue"])).order_by(LoanInstallment.due_at).all()
    now = datetime.now(UTC)
    for item in rows:
        due = item.due_at if item.due_at.tzinfo else item.due_at.replace(tzinfo=UTC)
        if due <= now and item.status == "scheduled":
            item.status = "overdue"
    db.commit()
    return [{**serialize_installment(row), "loan_id": row.loan_id} for row in rows]


@router.post("/loans/collections/{installment_id}/record-payment")
def record_loan_payment(installment_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    return _record_loan_payment(installment_id, db, user)


@router.post("/loans/installments/{installment_id}/record-payment")
def record_own_loan_payment(installment_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(LoanInstallment, installment_id)
    if not item:
        raise HTTPException(404, "Installment not found")
    loan = db.get(LoanApplication, item.loan_id)
    if user.role not in STAFF_ROLES and (user.role != "customer" or not user.customer or not loan or loan.customer_id != user.customer.id):
        raise HTTPException(404, "Installment not found")
    return _record_loan_payment(installment_id, db, user)


def _record_loan_payment(installment_id: int, db: Session, user: User):
    item = db.get(LoanInstallment, installment_id)
    if not item:
        raise HTTPException(404, "Installment not found")
    if item.status not in ("scheduled", "overdue"):
        raise HTTPException(409, "Installment is not payable")
    item.status = "paid_demo"
    item.paid_at = datetime.now(UTC)
    db.add(AuditLog(user_id=user.id, action="loan.installment_recorded", resource="loan_installment", resource_id=str(item.id), detail="demo payment record; no funds moved"))
    db.commit()
    return serialize_installment(item)


def serialize_bnpl(plan: BnplPlan, installments: list[BnplInstallment]):
    return {"id": plan.id, "merchant_name": plan.merchant_name, "purchase_amount": str(plan.purchase_amount), "currency": plan.currency, "installment_count": plan.installment_count, "installment_amount": str(plan.installment_amount), "status": plan.status, "installments": [serialize_installment(row) for row in installments], "disclosure": "Simulated BNPL plan; no purchase financing or funds movement occurs."}


@router.post("/bnpl/plans", status_code=201)
def create_bnpl_plan(body: BnplInput, db: Session = Depends(get_db), user: User = Depends(require_roles("customer"))):
    customer = customer_for(db, user)
    amount = body.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    each = (amount / body.installments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    plan = BnplPlan(customer_id=customer.id, merchant_name=body.merchant_name, purchase_amount=amount, currency=body.currency, installment_count=body.installments, installment_amount=each)
    db.add(plan)
    db.flush()
    first_due = datetime.now(UTC) + timedelta(days=30)
    rows = []
    allocated = Decimal("0.00")
    for number in range(1, body.installments + 1):
        due_amount = amount - allocated if number == body.installments else each
        allocated += due_amount
        row = BnplInstallment(plan_id=plan.id, installment_number=number, due_at=first_due + timedelta(days=30 * (number - 1)), amount=due_amount)
        db.add(row)
        rows.append(row)
    db.add(AuditLog(user_id=user.id, action="bnpl.plan_created", resource="bnpl_plan", detail=f"{body.currency}:{amount}"))
    db.commit()
    db.refresh(plan)
    return serialize_bnpl(plan, rows)


@router.get("/bnpl/plans")
def list_bnpl_plans(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role in STAFF_ROLES:
        plans = db.query(BnplPlan).order_by(BnplPlan.created_at.desc()).all()
    elif user.role == "customer":
        customer = customer_for(db, user)
        plans = db.query(BnplPlan).filter_by(customer_id=customer.id).order_by(BnplPlan.created_at.desc()).all()
    else:
        raise HTTPException(403, "BNPL is available to customer accounts")
    return [serialize_bnpl(plan, db.query(BnplInstallment).filter_by(plan_id=plan.id).order_by(BnplInstallment.installment_number).all()) for plan in plans]


@router.get("/bnpl/collections")
def bnpl_collections(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(BnplInstallment).filter(BnplInstallment.status.in_(["scheduled", "overdue"])).order_by(BnplInstallment.due_at).all()
    now = datetime.now(UTC)
    for item in rows:
        due = item.due_at if item.due_at.tzinfo else item.due_at.replace(tzinfo=UTC)
        if due <= now and item.status == "scheduled":
            item.status = "overdue"
    db.commit()
    return [{**serialize_installment(row), "plan_id": row.plan_id} for row in rows]


@router.post("/bnpl/installments/{installment_id}/record-payment")
def record_bnpl_payment(installment_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.get(BnplInstallment, installment_id)
    if not item:
        raise HTTPException(404, "Installment not found")
    plan = db.get(BnplPlan, item.plan_id)
    if not plan or user.role not in STAFF_ROLES and (user.role != "customer" or not user.customer or user.customer.id != plan.customer_id):
        raise HTTPException(404, "Installment not found")
    if item.status not in ("scheduled", "overdue"):
        raise HTTPException(409, "Installment is not payable")
    item.status = "paid_demo"
    item.paid_at = datetime.now(UTC)
    if all(row.status == "paid_demo" or row.id == item.id for row in db.query(BnplInstallment).filter_by(plan_id=plan.id).all()):
        plan.status = "completed_demo"
    db.add(AuditLog(user_id=user.id, action="bnpl.installment_recorded", resource="bnpl_installment", resource_id=str(item.id), detail="demo payment record; no funds moved"))
    db.commit()
    return serialize_installment(item)


@router.post("/business/organizations", status_code=201)
def create_organization(
    body: OrganizationInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*BUSINESS_ROLES)),
):
    if db.query(BusinessOrganization).filter_by(user_id=user.id).first():
        raise HTTPException(409, "Business profile already exists")
    row = BusinessOrganization(user_id=user.id, legal_name=body.legal_name)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="business.profile_submitted", resource="business_organization", detail=body.legal_name))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "legal_name": row.legal_name, "status": row.status}


@router.get("/business/organizations/me")
def get_organization(db: Session = Depends(get_db), user: User = Depends(require_roles(*BUSINESS_ROLES))):
    row = organization_for(db, user)
    return {"id": row.id, "legal_name": row.legal_name, "status": row.status}


@router.get("/business/summary")
def business_summary(db: Session = Depends(get_db), user: User = Depends(require_roles(*BUSINESS_ROLES))):
    organization = organization_for(db, user)
    invoices = db.query(BusinessInvoice).filter_by(organization_id=organization.id).all()
    payroll = db.query(PayrollBatch).filter_by(organization_id=organization.id).all()
    expenses = db.query(BusinessExpenseClaim).filter_by(organization_id=organization.id).all()
    receivables = sum((row.amount for row in invoices if row.status == "issued"), Decimal("0"))
    return {"organization": organization.legal_name, "status": organization.status, "open_receivables": str(receivables), "invoice_count": len(invoices), "payroll_pending": sum(row.status == "pending_approval" for row in payroll), "expense_claims_pending": sum(row.status == "pending_approval" for row in expenses), "currency": invoices[0].currency if invoices else "PKR", "disclosure": "Summary uses local demo records only."}


@router.get("/business/organizations", dependencies=[Depends(require_roles(*STAFF_ROLES))])
def list_organizations(db: Session = Depends(get_db)):
    rows = db.query(BusinessOrganization).order_by(BusinessOrganization.created_at.desc()).all()
    return [{"id": row.id, "user_id": row.user_id, "legal_name": row.legal_name, "status": row.status} for row in rows]


@router.patch("/business/organizations/{organization_id}")
def review_organization(
    organization_id: int,
    body: OrganizationDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF_ROLES)),
):
    row = db.get(BusinessOrganization, organization_id)
    if not row:
        raise HTTPException(404, "Business profile not found")
    if row.status != "pending_review":
        raise HTTPException(409, "Business profile has already been reviewed")
    row.status = body.decision
    db.add(AuditLog(user_id=user.id, action="business.profile_reviewed", resource="business_organization", resource_id=str(row.id), detail=body.decision))
    db.commit()
    return {"id": row.id, "status": row.status}


@router.post("/business/invoices", status_code=201)
def create_invoice(body: InvoiceInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*BUSINESS_ROLES))):
    organization = organization_for(db, user)
    if organization.status != "active":
        raise HTTPException(403, "Business profile must be activated before issuing invoices")
    row = BusinessInvoice(
        organization_id=organization.id,
        invoice_number=f"INV-{uuid4().hex[:12].upper()}",
        customer_name=body.customer_name,
        amount=body.amount,
        currency=body.currency,
    )
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="business.invoice_created", resource="business_invoice", detail=row.invoice_number))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "invoice_number": row.invoice_number, "customer_name": row.customer_name, "amount": str(row.amount), "currency": row.currency, "status": row.status}


@router.get("/business/invoices")
def list_invoices(db: Session = Depends(get_db), user: User = Depends(require_roles(*BUSINESS_ROLES))):
    organization = organization_for(db, user)
    rows = db.query(BusinessInvoice).filter_by(organization_id=organization.id).order_by(BusinessInvoice.created_at.desc()).all()
    return [{"id": row.id, "invoice_number": row.invoice_number, "customer_name": row.customer_name, "amount": str(row.amount), "currency": row.currency, "status": row.status, "created_at": row.created_at} for row in rows]


@router.patch("/business/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, body: InvoiceStatusInput, db: Session = Depends(get_db), user: User = Depends(require_roles("business", "admin"))):
    organization = organization_for(db, user)
    row = db.query(BusinessInvoice).filter_by(id=invoice_id, organization_id=organization.id).first()
    if not row:
        raise HTTPException(404, "Invoice not found")
    allowed = {"issued": {"paid", "cancelled"}, "paid": {"refunded"}}
    if body.status not in allowed.get(row.status, set()):
        raise HTTPException(409, "Invoice status transition is not allowed")
    row.status = body.status
    db.add(AuditLog(user_id=user.id, action="business.invoice_status_changed", resource="business_invoice", resource_id=str(row.id), detail=body.status))
    db.commit()
    return {"id": row.id, "status": row.status, "disclosure": "Invoice status is a local simulation; no payment or refund was processed."}


@router.post("/business/payroll", status_code=201)
def create_payroll(body: PayrollInput, db: Session = Depends(get_db), user: User = Depends(require_roles("business", "admin"))):
    organization = organization_for(db, user)
    if organization.status != "active":
        raise HTTPException(403, "Business profile must be active before submitting payroll")
    row = PayrollBatch(organization_id=organization.id, pay_period=body.pay_period, employee_count=body.employee_count, total_amount=body.total_amount, currency=body.currency)
    db.add(row)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="business.payroll_submitted", resource="payroll_batch", resource_id=str(row.id), detail=body.pay_period))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "pay_period": row.pay_period, "employee_count": row.employee_count, "total_amount": str(row.total_amount), "currency": row.currency, "status": row.status, "disclosure": "Approval workflow only; payroll is not paid or transferred."}


@router.get("/business/payroll")
def list_payroll(db: Session = Depends(get_db), user: User = Depends(require_roles("business", "admin"))):
    organization = organization_for(db, user)
    rows = db.query(PayrollBatch).filter_by(organization_id=organization.id).order_by(PayrollBatch.created_at.desc()).all()
    return [{"id": row.id, "pay_period": row.pay_period, "employee_count": row.employee_count, "total_amount": str(row.total_amount), "currency": row.currency, "status": row.status} for row in rows]


@router.get("/business/payroll/review")
def payroll_review_queue(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(PayrollBatch).filter_by(status="pending_approval").order_by(PayrollBatch.created_at).all()
    return [{"id": row.id, "organization_id": row.organization_id, "pay_period": row.pay_period, "employee_count": row.employee_count, "total_amount": str(row.total_amount), "currency": row.currency} for row in rows]


@router.patch("/business/payroll/{batch_id}")
def decide_payroll(batch_id: int, body: PayrollDecision, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(PayrollBatch, batch_id)
    if not row:
        raise HTTPException(404, "Payroll batch not found")
    if row.status != "pending_approval":
        raise HTTPException(409, "Payroll batch has already been reviewed")
    row.status = body.decision
    db.add(AuditLog(user_id=user.id, action="business.payroll_reviewed", resource="payroll_batch", resource_id=str(row.id), detail=body.decision))
    db.commit()
    return {"id": row.id, "status": row.status, "disclosure": "No payroll funds were transferred."}


@router.post("/business/expenses", status_code=201)
def create_expense_claim(body: ExpenseInput, db: Session = Depends(get_db), user: User = Depends(require_roles("business", "admin"))):
    organization = organization_for(db, user)
    row = BusinessExpenseClaim(organization_id=organization.id, claimant_name=body.claimant_name, description=body.description, amount=body.amount, currency=body.currency, evidence_reference=body.evidence_reference)
    db.add(row)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="business.expense_submitted", resource="expense_claim", resource_id=str(row.id), detail=body.evidence_reference))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "claimant_name": row.claimant_name, "description": row.description, "amount": str(row.amount), "currency": row.currency, "evidence_reference": row.evidence_reference, "status": row.status}


@router.get("/business/expenses")
def list_expense_claims(db: Session = Depends(get_db), user: User = Depends(require_roles(*BUSINESS_ROLES))):
    organization = organization_for(db, user)
    rows = db.query(BusinessExpenseClaim).filter_by(organization_id=organization.id).order_by(BusinessExpenseClaim.created_at.desc()).all()
    return [{"id": row.id, "claimant_name": row.claimant_name, "description": row.description, "amount": str(row.amount), "currency": row.currency, "evidence_reference": row.evidence_reference, "status": row.status} for row in rows]


@router.get("/business/expenses/review")
def expense_review_queue(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(BusinessExpenseClaim).filter_by(status="pending_approval").order_by(BusinessExpenseClaim.created_at).all()
    return [{"id": row.id, "organization_id": row.organization_id, "claimant_name": row.claimant_name, "description": row.description, "amount": str(row.amount), "currency": row.currency, "evidence_reference": row.evidence_reference} for row in rows]


@router.patch("/business/expenses/{claim_id}")
def decide_expense_claim(claim_id: int, body: WorkDecision, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(BusinessExpenseClaim, claim_id)
    if not row:
        raise HTTPException(404, "Expense claim not found")
    if row.status != "pending_approval" or body.decision not in ("approved", "rejected"):
        raise HTTPException(409, "Expense claim cannot take this decision")
    row.status = body.decision
    db.add(AuditLog(user_id=user.id, action="business.expense_reviewed", resource="expense_claim", resource_id=str(row.id), detail=body.decision))
    db.commit()
    return {"id": row.id, "status": row.status}


@router.post("/merchant/settlements", status_code=201)
def create_settlement(body: SettlementInput, db: Session = Depends(get_db), user: User = Depends(require_roles("merchant", "admin"))):
    organization = organization_for(db, user)
    gross = body.gross_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rule = db.query(FeeRule).filter_by(code="merchant_settlement", active=True).first()
    fee_rate = rule.percentage / Decimal("100") if rule else Decimal("0.015")
    fee = (gross * fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    row = MerchantSettlement(organization_id=organization.id, reference=f"SET-{uuid4().hex[:12].upper()}", gross_amount=gross, fee_amount=fee, net_amount=gross-fee, currency=body.currency, status="simulated")
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="merchant.settlement_simulated", resource="merchant_settlement", detail=row.reference))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "reference": row.reference, "gross_amount": str(gross), "fee_amount": str(fee), "net_amount": str(gross-fee), "currency": row.currency, "status": row.status, "disclosure": "Settlement processing is simulated; no funds are moved."}


@router.get("/merchant/settlements")
def list_settlements(db: Session = Depends(get_db), user: User = Depends(require_roles("merchant", "admin"))):
    organization = organization_for(db, user)
    rows = db.query(MerchantSettlement).filter_by(organization_id=organization.id).order_by(MerchantSettlement.created_at.desc()).all()
    return [{"id": row.id, "reference": row.reference, "gross_amount": str(row.gross_amount), "fee_amount": str(row.fee_amount), "net_amount": str(row.net_amount), "currency": row.currency, "status": row.status, "disclosure": "Settlement processing is simulated; no funds are moved. The displayed 1.5% fee is illustrative."} for row in rows]


@router.get("/merchant/summary")
def merchant_summary(db: Session = Depends(get_db), user: User = Depends(require_roles("merchant", "admin"))):
    organization = organization_for(db, user)
    sales = db.query(MerchantSale).filter_by(organization_id=organization.id).all()
    settlements = db.query(MerchantSettlement).filter_by(organization_id=organization.id).all()
    captured = sum((row.amount for row in sales if row.status == "captured_demo"), Decimal("0"))
    return {"sales_count": len(sales), "captured_demo_total": str(captured), "open_disputes": db.query(MerchantDispute).filter_by(organization_id=organization.id, status="open").count(), "settlements_pending_review": sum(row.status == "simulated" for row in settlements), "currency": sales[0].currency if sales else "PKR", "disclosure": "Metrics are local demo records only; no real payment processing."}


@router.get("/merchant/settlements/review")
def settlement_review_queue(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(MerchantSettlement).filter_by(status="simulated").order_by(MerchantSettlement.created_at).all()
    return [{"id": row.id, "organization_id": row.organization_id, "reference": row.reference, "gross_amount": str(row.gross_amount), "fee_amount": str(row.fee_amount), "net_amount": str(row.net_amount), "currency": row.currency} for row in rows]


@router.patch("/merchant/settlements/{settlement_id}/review")
def review_settlement(settlement_id: int, body: SettlementReviewInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(MerchantSettlement, settlement_id)
    if not row:
        raise HTTPException(404, "Settlement not found")
    if row.status != "simulated":
        raise HTTPException(409, "Settlement has already been reviewed")
    row.status = body.decision
    db.add(AuditLog(user_id=user.id, action="merchant.settlement_reviewed", resource="merchant_settlement", resource_id=str(row.id), detail=body.decision))
    db.commit()
    return {"id": row.id, "status": row.status, "disclosure": "This control records review only; it does not settle or transfer funds."}


@router.post("/merchant/sales", status_code=201)
def create_merchant_sale(body: SaleInput, db: Session = Depends(get_db), user: User = Depends(require_roles("merchant", "admin"))):
    organization = organization_for(db, user)
    row = MerchantSale(organization_id=organization.id, reference=f"SALE-{uuid4().hex[:12].upper()}", description=body.description, amount=body.amount, currency=body.currency)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="merchant.sale_simulated", resource="merchant_sale", detail=row.reference))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "reference": row.reference, "description": row.description, "amount": str(row.amount), "currency": row.currency, "status": row.status, "disclosure": "Test sale only; no payment was collected."}


@router.get("/merchant/sales")
def list_merchant_sales(db: Session = Depends(get_db), user: User = Depends(require_roles("merchant", "admin"))):
    organization = organization_for(db, user)
    rows = db.query(MerchantSale).filter_by(organization_id=organization.id).order_by(MerchantSale.created_at.desc()).all()
    return [{"id": row.id, "reference": row.reference, "description": row.description, "amount": str(row.amount), "currency": row.currency, "status": row.status, "created_at": row.created_at} for row in rows]


@router.post("/merchant/sales/{sale_id}/refund")
def refund_merchant_sale(sale_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("merchant", "admin"))):
    organization = organization_for(db, user)
    row = db.query(MerchantSale).filter_by(id=sale_id, organization_id=organization.id).first()
    if not row:
        raise HTTPException(404, "Sale not found")
    if row.status != "captured_demo":
        raise HTTPException(409, "Sale is not refundable")
    row.status = "refunded_demo"
    db.add(AuditLog(user_id=user.id, action="merchant.refund_simulated", resource="merchant_sale", resource_id=str(row.id), detail="No funds moved"))
    db.commit()
    return {"id": row.id, "status": row.status, "disclosure": "Refund recorded for demo only; no funds were returned."}


@router.post("/merchant/disputes", status_code=201)
def create_merchant_dispute(body: DisputeInput, db: Session = Depends(get_db), user: User = Depends(require_roles("merchant", "admin"))):
    organization = organization_for(db, user)
    sale = db.query(MerchantSale).filter_by(id=body.sale_id, organization_id=organization.id).first()
    if not sale:
        raise HTTPException(404, "Sale not found")
    row = MerchantDispute(organization_id=organization.id, sale_id=sale.id, reason=body.reason, evidence_reference=body.evidence_reference)
    db.add(row)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="merchant.dispute_opened", resource="merchant_dispute", resource_id=str(row.id), detail=body.reason))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "sale_id": row.sale_id, "reason": row.reason, "evidence_reference": row.evidence_reference, "status": row.status}


@router.get("/merchant/disputes")
def list_merchant_disputes(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role in STAFF_ROLES:
        records = db.query(MerchantDispute, MerchantSale).join(MerchantSale, MerchantSale.id == MerchantDispute.sale_id).order_by(MerchantDispute.created_at.desc()).all()
        available_sales = []
    elif user.role in ("merchant", "admin"):
        organization = organization_for(db, user)
        records = db.query(MerchantDispute, MerchantSale).join(MerchantSale, MerchantSale.id == MerchantDispute.sale_id).filter(MerchantDispute.organization_id == organization.id).order_by(MerchantDispute.created_at.desc()).all()
        available_sales = [
            {"id": sale.id, "reference": sale.reference, "description": sale.description, "amount": str(sale.amount), "currency": sale.currency}
            for sale in db.query(MerchantSale).filter_by(organization_id=organization.id).order_by(MerchantSale.created_at.desc()).all()
        ]
    else:
        raise HTTPException(403, "Merchant disputes are restricted")
    return {
        "items": [
            {"id": row.id, "sale_id": row.sale_id, "sale_reference": sale.reference, "sale_description": sale.description, "sale_amount": str(sale.amount), "currency": sale.currency, "organization_id": row.organization_id, "reason": row.reason, "evidence_reference": row.evidence_reference, "status": row.status, "decision": row.decision, "decision_note": row.decision_note, "created_at": row.created_at}
            for row, sale in records
        ],
        "can_review": user.role in STAFF_ROLES,
        "available_sales": available_sales,
    }


@router.patch("/merchant/disputes/{dispute_id}")
def review_merchant_dispute(dispute_id: int, body: DisputeDecision, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(MerchantDispute, dispute_id)
    if not row:
        raise HTTPException(404, "Dispute not found")
    if row.status != "open" or body.decision not in ("resolved", "escalated"):
        raise HTTPException(409, "Dispute cannot take this decision")
    row.status = body.decision
    row.decision = body.decision
    row.decision_note = body.note.strip()
    db.add(AuditLog(user_id=user.id, action="merchant.dispute_reviewed", resource="merchant_dispute", resource_id=str(row.id), detail=f"{body.decision}: {row.decision_note}"))
    db.commit()
    return {"id": row.id, "status": row.status, "decision": row.decision}


@router.get("/finance/trial-balance")
def trial_balance(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(LedgerAccount).order_by(LedgerAccount.code).all()
    result = []
    for ledger_account in rows:
        debit = db.query(func.coalesce(func.sum(JournalLine.debit), 0)).filter_by(ledger_account_id=ledger_account.id).scalar()
        credit = db.query(func.coalesce(func.sum(JournalLine.credit), 0)).filter_by(ledger_account_id=ledger_account.id).scalar()
        result.append({"code": ledger_account.code, "name": ledger_account.name, "currency": ledger_account.currency, "debit": str(debit), "credit": str(credit)})
    debit_total = sum((Decimal(item["debit"]) for item in result), Decimal("0"))
    credit_total = sum((Decimal(item["credit"]) for item in result), Decimal("0"))
    return {"accounts": result, "debit_total": str(debit_total), "credit_total": str(credit_total), "balanced": debit_total == credit_total}


@router.get("/finance/journals")
def list_journals(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    entries = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(200).all()
    result = []
    for entry in entries:
        lines = db.query(JournalLine, LedgerAccount).join(LedgerAccount, JournalLine.ledger_account_id == LedgerAccount.id).filter(JournalLine.journal_entry_id == entry.id).all()
        result.append({"id": entry.id, "transaction_id": entry.transaction_id, "reference": entry.reference, "created_at": entry.created_at, "lines": [{"account_code": account.code, "account_name": account.name, "debit": str(line.debit), "credit": str(line.credit)} for line, account in lines]})
    return result


@router.post("/finance/reconciliation-runs", status_code=201)
def create_reconciliation(body: ReconciliationInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    ledger_total = db.query(func.coalesce(func.sum(JournalLine.debit), 0)).scalar()
    ledger_total = Decimal(str(ledger_total))
    status = "matched" if ledger_total == body.external_total else "exception"
    row = ReconciliationRun(created_by=user.id, source=body.source, ledger_total=ledger_total, external_total=body.external_total, status=status, notes=body.notes)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="reconciliation.created", resource="reconciliation_run", detail=f"{body.source}:{status}"))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "source": row.source, "ledger_total": str(row.ledger_total), "external_total": str(row.external_total), "status": row.status, "notes": row.notes}


@router.get("/finance/reconciliation-runs")
def list_reconciliations(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(ReconciliationRun).order_by(ReconciliationRun.created_at.desc()).all()
    return [{"id": row.id, "source": row.source, "ledger_total": str(row.ledger_total), "external_total": str(row.external_total), "status": row.status, "notes": row.notes, "created_at": row.created_at} for row in rows]


@router.get("/finance/fee-rules")
def list_fee_rules(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(FeeRule).order_by(FeeRule.code).all()
    return [{"id": row.id, "code": row.code, "description": row.description, "percentage": str(row.percentage), "active": row.active} for row in rows]


@router.post("/finance/fee-rules", status_code=201)
def create_fee_rule(body: FeeRuleInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    if db.query(FeeRule).filter_by(code=body.code).first():
        raise HTTPException(409, "A fee rule with this code already exists")
    row = FeeRule(code=body.code, description=body.description, percentage=body.percentage)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="finance.fee_rule_created", resource="fee_rule", detail=body.code))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "code": row.code, "description": row.description, "percentage": str(row.percentage), "active": row.active}


@router.patch("/finance/fee-rules/{rule_id}")
def toggle_fee_rule(rule_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(FeeRule, rule_id)
    if not row:
        raise HTTPException(404, "Fee rule not found")
    row.active = not row.active
    db.add(AuditLog(user_id=user.id, action="finance.fee_rule_toggled", resource="fee_rule", resource_id=str(row.id), detail=str(row.active)))
    db.commit()
    return {"id": row.id, "active": row.active}


@router.post("/risk/cases", status_code=201)
def create_risk_case(body: RiskCaseInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    if not db.get(Customer, body.customer_id):
        raise HTTPException(404, "Customer not found")
    row = RiskCase(customer_id=body.customer_id, category=body.category, summary=body.summary, score=body.score)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="risk.case_created", resource="risk_case", detail=body.category))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "customer_id": row.customer_id, "category": row.category, "summary": row.summary, "score": row.score, "status": row.status}


@router.get("/risk/cases")
def list_risk_cases(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(RiskCase).order_by(RiskCase.created_at.desc()).all()
    return [{"id": row.id, "customer_id": row.customer_id, "category": row.category, "summary": row.summary, "score": row.score, "status": row.status, "decision": row.decision, "notes": row.notes, "evidence_reference": row.evidence_reference, "created_at": row.created_at} for row in rows]


@router.get("/operations/summary")
def operations_summary(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    return {"loan_applications_pending": db.query(LoanApplication).filter_by(status="submitted").count(), "business_profiles_pending": db.query(BusinessOrganization).filter_by(status="pending_review").count(), "payroll_batches_pending": db.query(PayrollBatch).filter_by(status="pending_approval").count(), "expense_claims_pending": db.query(BusinessExpenseClaim).filter_by(status="pending_approval").count(), "risk_cases_open": db.query(RiskCase).filter_by(status="open").count(), "merchant_disputes_open": db.query(MerchantDispute).filter_by(status="open").count()}


@router.post("/risk/cases/{case_id}/notes")
def add_risk_case_note(case_id: int, body: CaseNoteInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(RiskCase, case_id)
    if not row:
        raise HTTPException(404, "Risk case not found")
    row.notes = f"{row.notes}\n{datetime.now(UTC).isoformat()} {user.email}: {body.note}".strip()
    db.add(AuditLog(user_id=user.id, action="risk.case_note_added", resource="risk_case", resource_id=str(row.id)))
    db.commit()
    return {"id": row.id, "notes": row.notes}


@router.post("/risk/cases/{case_id}/evidence")
def attach_risk_case_evidence(case_id: int, body: EvidenceInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(RiskCase, case_id)
    if not row:
        raise HTTPException(404, "Risk case not found")
    row.evidence_reference = body.evidence_reference
    db.add(AuditLog(user_id=user.id, action="risk.case_evidence_attached", resource="risk_case", resource_id=str(row.id), detail=body.evidence_reference))
    db.commit()
    return {"id": row.id, "evidence_reference": row.evidence_reference}


@router.patch("/risk/cases/{case_id}")
def decide_risk_case(case_id: int, body: RiskDecision, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(RiskCase, case_id)
    if not row:
        raise HTTPException(404, "Risk case not found")
    if row.status != "open":
        raise HTTPException(409, "Risk case has already been resolved")
    row.status = "closed"
    row.decision = body.decision
    db.add(AuditLog(user_id=user.id, action="risk.case_decided", resource="risk_case", resource_id=str(row.id), detail=body.decision))
    db.commit()
    return {"id": row.id, "status": row.status, "decision": row.decision}


@router.post("/risk/screenings", status_code=201)
def run_mock_screening(body: ScreeningInput, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    normalized = body.subject_name.casefold()
    match_terms = ("sanction", "watchlist", "test-hit", "suspicious")
    hit = any(term in normalized for term in match_terms)
    row = ScreeningRun(
        created_by=user.id,
        subject_name=body.subject_name,
        category=body.category,
        score=92 if hit else 3,
        result="potential_match" if hit else "no_match",
        rationale="Synthetic keyword fixture matched" if hit else "No synthetic fixture matched",
    )
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="risk.mock_screening", resource="screening_run", detail=f"{body.category}:{row.result}"))
    db.commit()
    db.refresh(row)
    return {"id": row.id, "subject_name": row.subject_name, "category": row.category, "score": row.score, "result": row.result, "rationale": row.rationale, "disclosure": "Mock keyword check only. It is not a real screening or compliance result and requires human review."}


@router.get("/risk/screenings")
def list_mock_screenings(db: Session = Depends(get_db), _user: User = Depends(require_roles(*STAFF_ROLES))):
    rows = db.query(ScreeningRun).order_by(ScreeningRun.created_at.desc()).all()
    return [{"id": row.id, "subject_name": row.subject_name, "category": row.category, "score": row.score, "result": row.result, "rationale": row.rationale, "created_at": row.created_at} for row in rows]
