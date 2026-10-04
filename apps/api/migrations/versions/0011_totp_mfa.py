"""Add TOTP MFA and authentication challenge state."""

import sqlalchemy as sa
from alembic import op

revision = "0011_totp_mfa"
down_revision = "0010_dispute_decision_notes"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    additions = (
        ("mfa_enabled", sa.Boolean(), False, "0"),
        ("mfa_secret_encrypted", sa.Text(), True, None),
        ("mfa_recovery_codes_hashes", sa.Text(), True, None),
        ("mfa_last_counter", sa.Integer(), True, None),
        ("mfa_failed_attempts", sa.Integer(), False, "0"),
        ("mfa_locked_until", sa.DateTime(timezone=True), True, None),
    )
    for name, type_, nullable, default in additions:
        if name not in columns:
            op.add_column(
                "users",
                sa.Column(name, type_, nullable=nullable, server_default=default),
            )


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    for name in ("mfa_locked_until", "mfa_failed_attempts", "mfa_last_counter", "mfa_recovery_codes_hashes", "mfa_secret_encrypted", "mfa_enabled"):
        if name in columns:
            op.drop_column("users", name)
