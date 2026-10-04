from calendar import monthrange
from datetime import UTC, date, datetime, time
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import current_user, require_roles
from app.modules.accounts.models import Account, FinancialTransaction
from app.modules.accounts.models import Beneficiary
from app.modules.cards.models import Card
from app.modules.customers.router import customer_for
from app.modules.identity.models import AuditLog, User
from app.modules.workspace.models import DepositPosition, SavingsGoal, SpendingBudget, SupportTicket

router = APIRouter(tags=["Support and customer planning"])
STAFF_ROLES = ("operations", "admin")
DEPOSIT_PRODUCTS = {
    "term-3m": {"name": "3 month term deposit", "term_months": 3, "annual_yield": Decimal("5.0"), "minimum": Decimal("1000")},
    "term-6m": {"name": "6 month term deposit", "term_months": 6, "annual_yield": Decimal("5.5"), "minimum": Decimal("5000")},
    "term-12m": {"name": "12 month term deposit", "term_months": 12, "annual_yield": Decimal("6.0"), "minimum": Decimal("10000")},
}


def add_months(value: datetime, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


class SupportTicketInput(BaseModel):
    subject: str = Field(min_length=4, max_length=160)
    category: str = Field(pattern="^(accounts|cards|payments|profile|other)$")
    body: str = Field(min_length=10, max_length=4000)


class SupportTicketReview(BaseModel):
    status: str = Field(pattern="^(in_progress|resolved|closed)$")
    staff_response: str = Field(min_length=3, max_length=2000)


class BudgetInput(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[1-2])$")
    category: str = Field(pattern="^(transfers|payments|wallet)$")
    limit_amount: Decimal = Field(gt=0, le=Decimal("1000000000"))
    currency: str = Field(default="PKR", pattern="^[A-Z]{3}$")


class GoalInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    target_amount: Decimal = Field(gt=0, le=Decimal("1000000000"))
    currency: str = Field(default="PKR", pattern="^[A-Z]{3}$")
    target_date: date | None = None


class GoalContribution(BaseModel):
    amount: Decimal = Field(gt=0, le=Decimal("1000000000"))


class DepositInput(BaseModel):
    source_account_id: int = Field(gt=0)
    product_code: str = Field(pattern="^term-(3|6|12)m$")
    amount: Decimal = Field(gt=0, le=Decimal("1000000000"))


def ticket_json(row: SupportTicket):
    return {"id": row.id, "subject": row.subject, "category": row.category, "body": row.body, "status": row.status, "staff_response": row.staff_response, "created_at": row.created_at, "updated_at": row.updated_at}


@router.get("/support/tickets")
def list_support_tickets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(SupportTicket)
    if user.role not in STAFF_ROLES:
        query = query.filter_by(user_id=user.id)
    rows = query.order_by(SupportTicket.updated_at.desc()).limit(100).all()
    return [ticket_json(row) for row in rows]


@router.post("/support/tickets", status_code=201)
def create_support_ticket(body: SupportTicketInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    row = SupportTicket(user_id=user.id, subject=body.subject.strip(), category=body.category, body=body.body.strip())
    db.add(row)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="support.ticket_created", resource="support_ticket", resource_id=str(row.id), detail=row.subject))
    db.commit()
    db.refresh(row)
    return ticket_json(row)


@router.patch("/support/tickets/{ticket_id}")
def review_support_ticket(ticket_id: int, body: SupportTicketReview, db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF_ROLES))):
    row = db.get(SupportTicket, ticket_id)
    if not row:
        raise HTTPException(404, "Support ticket not found")
    row.status = body.status
    row.staff_response = body.staff_response.strip()
    row.updated_at = datetime.now(UTC)
    db.add(AuditLog(user_id=user.id, action="support.ticket_reviewed", resource="support_ticket", resource_id=str(row.id), detail=body.status))
    db.commit()
    return ticket_json(row)


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(AuditLog).filter_by(user_id=user.id).order_by(AuditLog.created_at.desc()).limit(50).all()
    return {"items": [{"id": row.id, "title": row.action.replace(".", " ").replace("_", " ").title(), "detail": row.detail, "created_at": row.created_at, "resource": row.resource, "resource_id": row.resource_id} for row in rows], "source": "Recent account activity", "read_tracking": False}


@router.get("/search")
def global_search(q: str = Query(min_length=2, max_length=80), db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    results = []
    for row in db.query(Account).filter_by(customer_id=customer.id).all():
        if q.casefold() in row.account_number.casefold() or q.casefold() in row.account_type.casefold():
            results.append({"type": "account", "label": row.account_type.title() + " account", "detail": "••••" + row.account_number[-4:] + " · " + row.currency, "href": "/accounts/" + str(row.id)})
    transactions = db.query(FinancialTransaction).filter_by(customer_id=customer.id).all()
    for row in transactions:
        if q.casefold() in row.reference.casefold() or q.casefold() in row.transaction_type.casefold():
            results.append({"type": "transaction", "label": row.transaction_type.replace("_", " ").title(), "detail": row.reference + " · " + str(row.amount) + " " + row.currency, "href": "/transfers"})
    for row in db.query(Beneficiary).filter_by(customer_id=customer.id).all():
        if q.casefold() in row.name.casefold():
            results.append({"type": "beneficiary", "label": row.name, "detail": "••••" + row.account_number[-4:], "href": "/transfers"})
    for row in db.query(Card).filter_by(customer_id=customer.id).all():
        if q.casefold() in row.last4.casefold() or q.casefold() in row.status.casefold():
            results.append({"type": "card", "label": row.card_type.title() + " card", "detail": "•••• " + row.last4 + " · " + row.status, "href": "/cards"})
    return {"results": results[:12]}


def budget_spent(db: Session, customer_id: int, month: str, category: str, currency: str) -> Decimal:
    year, month_number = (int(part) for part in month.split("-"))
    start = datetime.combine(date(year, month_number, 1), time.min, tzinfo=UTC)
    next_month = date(year + (month_number == 12), 1 if month_number == 12 else month_number + 1, 1)
    end = datetime.combine(next_month, time.min, tzinfo=UTC)
    types = {"transfers": ["transfer"], "payments": ["payment"], "wallet": ["wallet_withdraw"]}[category]
    rows = db.query(FinancialTransaction.amount).filter(
        FinancialTransaction.customer_id == customer_id,
        FinancialTransaction.currency == currency,
        FinancialTransaction.status == "posted",
        FinancialTransaction.transaction_type.in_(types),
        FinancialTransaction.created_at >= start,
        FinancialTransaction.created_at < end,
    ).all()
    return sum((row[0] for row in rows), Decimal("0"))


@router.get("/budgets")
def list_budgets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    rows = db.query(SpendingBudget).filter_by(customer_id=customer.id).order_by(SpendingBudget.month.desc(), SpendingBudget.category).all()
    return [{"id": row.id, "month": row.month, "category": row.category, "limit_amount": str(row.limit_amount), "spent": str((spent := budget_spent(db, customer.id, row.month, row.category, row.currency))), "remaining": str(row.limit_amount - spent), "currency": row.currency} for row in rows]


@router.post("/budgets", status_code=201)
def save_budget(body: BudgetInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    try:
        date.fromisoformat(body.month + "-01")
    except ValueError as exc:
        raise HTTPException(422, "Month is invalid") from exc
    row = db.query(SpendingBudget).filter_by(customer_id=customer.id, month=body.month, category=body.category).first()
    if row:
        row.limit_amount = body.limit_amount
        row.currency = body.currency
    else:
        row = SpendingBudget(customer_id=customer.id, month=body.month, category=body.category, limit_amount=body.limit_amount, currency=body.currency)
        db.add(row)
    db.add(AuditLog(user_id=user.id, action="budget.saved", resource="spending_budget", detail=f"{body.month}:{body.category}"))
    db.commit()
    db.refresh(row)
    spent = budget_spent(db, customer.id, row.month, row.category, row.currency)
    return {"id": row.id, "month": row.month, "category": row.category, "limit_amount": str(row.limit_amount), "spent": str(spent), "remaining": str(row.limit_amount - spent), "currency": row.currency}


def goal_json(row: SavingsGoal):
    percent = min(100, int((row.current_amount / row.target_amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))) if row.target_amount else 0
    return {"id": row.id, "name": row.name, "target_amount": str(row.target_amount), "current_amount": str(row.current_amount), "currency": row.currency, "target_date": row.target_date, "progress_percent": percent, "status": row.status, "disclosure": "Progress tracker only; recording a contribution does not move money."}


@router.get("/goals")
def list_goals(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    return [goal_json(row) for row in db.query(SavingsGoal).filter_by(customer_id=customer.id).order_by(SavingsGoal.created_at.desc()).all()]


@router.post("/goals", status_code=201)
def create_goal(body: GoalInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    row = SavingsGoal(customer_id=customer.id, name=body.name.strip(), target_amount=body.target_amount, currency=body.currency, target_date=body.target_date)
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="goal.created", resource="savings_goal", detail=row.name))
    db.commit()
    db.refresh(row)
    return goal_json(row)


@router.post("/goals/{goal_id}/contributions")
def contribute_to_goal(goal_id: int, body: GoalContribution, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    row = db.query(SavingsGoal).filter_by(id=goal_id, customer_id=customer.id).first()
    if not row:
        raise HTTPException(404, "Savings goal not found")
    if row.status != "active":
        raise HTTPException(409, "This goal is already complete")
    row.current_amount = min(row.target_amount, row.current_amount + body.amount)
    if row.current_amount >= row.target_amount:
        row.status = "complete"
    db.add(AuditLog(user_id=user.id, action="goal.progress_recorded", resource="savings_goal", resource_id=str(row.id), detail=str(body.amount)))
    db.commit()
    return goal_json(row)


@router.get("/deposits/products")
def deposit_products(_user: User = Depends(current_user)):
    return [{"code": code, **{key: str(value) if isinstance(value, Decimal) else value for key, value in product.items()}, "currency": "PKR", "disclosure": "Illustrative local term-deposit simulation; no funds are reserved or invested."} for code, product in DEPOSIT_PRODUCTS.items()]


@router.get("/deposits/positions")
def list_deposit_positions(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    rows = db.query(DepositPosition).filter_by(customer_id=customer.id).order_by(DepositPosition.created_at.desc()).all()
    result = []
    for row in rows:
        projected = (row.principal * (Decimal("1") + row.annual_yield * row.term_months / Decimal("1200"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.append({"id": row.id, "product_code": row.product_code, "principal": str(row.principal), "projected_maturity_value": str(projected), "maturity_date": add_months(row.created_at, row.term_months), "currency": row.currency, "term_months": row.term_months, "status": row.status, "created_at": row.created_at, "disclosure": "Illustrative estimate only; no deposit was placed."})
    return result


@router.post("/deposits/positions", status_code=201)
def create_deposit_position(body: DepositInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    product = DEPOSIT_PRODUCTS.get(body.product_code)
    account = db.query(Account).filter_by(id=body.source_account_id, customer_id=customer.id, status="active").first()
    if not account:
        raise HTTPException(404, "Active source account not found")
    if not product or body.amount < product["minimum"]:
        raise HTTPException(422, "Amount is below the selected product minimum")
    if account.currency != "PKR":
        raise HTTPException(422, "These illustrative term products are available in PKR only")
    if body.amount > account.balance:
        raise HTTPException(422, "Amount exceeds the current account balance")
    row = DepositPosition(customer_id=customer.id, account_id=account.id, product_code=body.product_code, principal=body.amount, currency=account.currency, term_months=product["term_months"], annual_yield=product["annual_yield"])
    db.add(row)
    db.add(AuditLog(user_id=user.id, action="deposit.position_simulated", resource="deposit_position", detail=body.product_code))
    db.commit()
    db.refresh(row)
    projected = (row.principal * (Decimal("1") + row.annual_yield * row.term_months / Decimal("1200"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"id": row.id, "principal": str(row.principal), "projected_maturity_value": str(projected), "maturity_date": add_months(row.created_at, row.term_months), "currency": row.currency, "term_months": row.term_months, "status": row.status, "disclosure": "Simulation recorded only. No balance changed and no funds were reserved."}
