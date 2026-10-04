from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class InvestmentProduct(Base):
    __tablename__ = "investment_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(240))
    annual_yield: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    minimum_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    product_code: Mapped[str] = mapped_column(String(60), index=True)
    principal: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    status: Mapped[str] = mapped_column(String(30), default="simulated_active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class RemittanceRequest(Base):
    __tablename__ = "remittance_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    source_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    destination_country: Mapped[str] = mapped_column(String(2))
    source_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    source_currency: Mapped[str] = mapped_column(String(3))
    destination_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    destination_currency: Mapped[str] = mapped_column(String(3))
    quoted_rate: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    status: Mapped[str] = mapped_column(String(30), default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class BankingConsent(Base):
    __tablename__ = "banking_consents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider_name: Mapped[str] = mapped_column(String(120))
    scopes: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="active")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DeveloperApiClient(Base):
    __tablename__ = "developer_api_clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    key_prefix: Mapped[str] = mapped_column(String(16))
    secret_hash: Mapped[str] = mapped_column(String(64), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    event_types: Mapped[str] = mapped_column(Text)
    secret_hash: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("webhook_endpoints.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(120))
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="queued_demo")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
