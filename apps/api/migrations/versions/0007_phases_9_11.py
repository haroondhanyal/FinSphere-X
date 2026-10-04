"""Add investments, remittance, open banking and developer sandbox tables."""

from alembic import op

from app.core.database import Base
from app.modules.phase9_11 import models as phase9_11_models  # noqa: F401

revision = "0007_phases_9_11"
down_revision = "0006_loan_decision_support"
branch_labels = None
depends_on = None

TABLES = (
    "investment_products",
    "portfolio_positions",
    "remittance_requests",
    "banking_consents",
    "developer_api_clients",
    "webhook_endpoints",
    "webhook_deliveries",
)


def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in TABLES])


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in reversed(TABLES)])
