from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    last4: Mapped[str] = mapped_column(String(4))
    card_type: Mapped[str] = mapped_column(String(20), default="debit")
    status: Mapped[str] = mapped_column(String(20), default="inactive")
    daily_limit: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("100000"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
