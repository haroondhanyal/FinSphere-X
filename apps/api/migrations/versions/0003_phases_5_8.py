"""Add lending, business, finance and risk slices."""

from alembic import op

from app.core.database import Base
from app.modules.phase5_8 import models as phase5_8_models  # noqa: F401

revision = "0003_phases_5_8"
down_revision = "0002_refresh_sessions"
branch_labels = None
depends_on = None


def upgrade():
    tables = (
        "loan_applications",
        "business_organizations",
        "business_invoices",
        "merchant_settlements",
        "reconciliation_runs",
        "risk_cases",
    )
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in tables])


def downgrade():
    tables = (
        "risk_cases",
        "reconciliation_runs",
        "merchant_settlements",
        "business_invoices",
        "business_organizations",
        "loan_applications",
    )
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in tables])
