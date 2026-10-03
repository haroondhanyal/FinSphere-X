"""Create the Phase 1–4 identity, accounts, ledger, payments and cards schema."""

from alembic import op

from app.core.database import Base
from app.modules.accounts import models as account_models  # noqa: F401
from app.modules.cards import models as card_models  # noqa: F401
from app.modules.identity import models as identity_models  # noqa: F401

revision = "0001_phase_1_4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    phase_tables = (
        "users",
        "customers",
        "audit_logs",
        "kyc_documents",
        "role_permissions",
        "accounts",
        "wallets",
        "beneficiaries",
        "transactions",
        "ledger_accounts",
        "journal_entries",
        "journal_lines",
        "cards",
    )
    Base.metadata.create_all(
        bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in phase_tables]
    )


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
