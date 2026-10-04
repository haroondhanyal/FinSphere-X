"""Store reviewer notes on merchant dispute decisions."""

import sqlalchemy as sa
from alembic import op

revision = "0010_dispute_decision_notes"
down_revision = "0009_password_reset_version"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("merchant_disputes")}
    if "decision_note" not in columns:
        op.add_column(
            "merchant_disputes",
            sa.Column("decision_note", sa.Text(), nullable=False, server_default=""),
        )


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("merchant_disputes")}
    if "decision_note" in columns:
        op.drop_column("merchant_disputes", "decision_note")
