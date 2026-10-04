"""Add BNPL, collections, payroll, fee rules and mock screening."""

from alembic import op

from app.core.database import Base
from app.modules.phase5_8 import models as phase5_8_models  # noqa: F401

revision = "0004_phase_5_8_completions"
down_revision = "0003_phases_5_8"
branch_labels = None
depends_on = None


TABLES = (
    "loan_installments",
    "bnpl_plans",
    "bnpl_installments",
    "payroll_batches",
    "fee_rules",
    "screening_runs",
)


def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in TABLES])


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in reversed(TABLES)])
