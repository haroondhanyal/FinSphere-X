import secrets
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import current_user
from app.modules.accounts.models import Account
from app.modules.cards.models import Card
from app.modules.customers.router import customer_for
from app.modules.identity.models import AuditLog, User

router = APIRouter(prefix="/cards", tags=["Cards"])


class IssueCardInput(BaseModel):
    account_id: int
    card_type: str = Field(default="debit", pattern="^(debit|virtual|prepaid)$")


class LimitInput(BaseModel):
    daily_limit: str = Field(min_length=1, max_length=32)


def card_view(card: Card):
    return {
        "id": card.id,
        "masked_number": f"•••• •••• •••• {card.last4}",
        "last4": card.last4,
        "card_type": card.card_type,
        "status": card.status,
        "daily_limit": str(card.daily_limit),
        "created_at": card.created_at,
    }


@router.get("")
def list_cards(db: Session = Depends(get_db), user: User = Depends(current_user)):
    customer = customer_for(db, user)
    return [card_view(c) for c in db.query(Card).filter_by(customer_id=customer.id).all()]


@router.post("", status_code=201)
def issue_card(
    body: IssueCardInput, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    account = db.query(Account).filter_by(id=body.account_id, customer_id=customer.id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    card = Card(
        customer_id=customer.id,
        account_id=account.id,
        last4=f"{secrets.randbelow(10000):04d}",
        card_type=body.card_type,
        status="inactive",
    )
    db.add(card)
    db.flush()
    db.add(
        AuditLog(user_id=user.id, action="card.issued", resource="card", resource_id=str(card.id))
    )
    db.commit()
    db.refresh(card)
    return card_view(card)


@router.post("/{card_id}/{action}")
def card_action(
    card_id: int, action: str, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    customer = customer_for(db, user)
    card = db.query(Card).filter_by(id=card_id, customer_id=customer.id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    transitions = {
        "activate": {"inactive": "active"},
        "freeze": {"active": "frozen"},
        "unfreeze": {"frozen": "active"},
        "block": {"active": "blocked", "frozen": "blocked", "inactive": "blocked"},
    }
    if action not in transitions or card.status not in transitions[action]:
        raise HTTPException(409, "This card action is not valid for its current status")
    card.status = transitions[action][card.status]
    db.add(
        AuditLog(
            user_id=user.id, action=f"card.{action}", resource="card", resource_id=str(card.id)
        )
    )
    db.commit()
    return card_view(card)


@router.patch("/{card_id}/limit")
def update_limit(
    card_id: int,
    body: LimitInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    customer = customer_for(db, user)
    card = db.query(Card).filter_by(id=card_id, customer_id=customer.id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    try:
        limit = Decimal(body.daily_limit)
    except InvalidOperation:
        raise HTTPException(422, "Limit must be a decimal")
    if limit <= 0 or limit > Decimal("10000000"):
        raise HTTPException(422, "Limit must be between 0 and 10,000,000")
    card.daily_limit = limit
    db.add(
        AuditLog(
            user_id=user.id, action="card.limit.updated", resource="card", resource_id=str(card.id)
        )
    )
    db.commit()
    return card_view(card)
