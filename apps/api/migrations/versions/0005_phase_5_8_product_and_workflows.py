"""Complete product catalog, expenses, merchant sales and dispute records."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Column, String, Text

from app.core.database import Base
from app.modules.phase5_8 import models as phase5_8_models  # noqa: F401

revision = "0005_phase_5_8_product_workflows"
down_revision = "0004_phase_5_8_completions"
branch_labels = None
depends_on = None


NEW_TABLES = (
    "loan_products",
    "business_expense_claims",
    "merchant_sales",
    "merchant_disputes",
)


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "product_code" not in {column["name"] for column in inspector.get_columns("loan_applications")}:
        op.add_column("loan_applications", Column("product_code", String(60), nullable=False, server_default="personal"))
    risk_columns = {column["name"] for column in inspector.get_columns("risk_cases")}
    if "notes" not in risk_columns:
        op.add_column("risk_cases", Column("notes", Text(), nullable=False, server_default=""))
    if "evidence_reference" not in risk_columns:
        op.add_column("risk_cases", Column("evidence_reference", String(240), nullable=False, server_default=""))
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in NEW_TABLES])


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in reversed(NEW_TABLES)])
    inspector = sa.inspect(op.get_bind())
    risk_columns = {column["name"] for column in inspector.get_columns("risk_cases")}
    if "evidence_reference" in risk_columns:
        op.drop_column("risk_cases", "evidence_reference")
    if "notes" in risk_columns:
        op.drop_column("risk_cases", "notes")
    if "product_code" in {column["name"] for column in inspector.get_columns("loan_applications")}:
        op.drop_column("loan_applications", "product_code")
