"""Add disclosed sample-only lending decision support fields."""

import sqlalchemy as sa
from alembic import op

revision = "0006_loan_decision_support"
down_revision = "0005_phase_5_8_product_workflows"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("loan_applications")}
    if "illustrative_score" not in columns:
        op.add_column("loan_applications", sa.Column("illustrative_score", sa.Integer(), nullable=False, server_default="0"))
    if "score_reasons" not in columns:
        op.add_column("loan_applications", sa.Column("score_reasons", sa.Text(), nullable=False, server_default=""))


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("loan_applications")}
    if "score_reasons" in columns:
        op.drop_column("loan_applications", "score_reasons")
    if "illustrative_score" in columns:
        op.drop_column("loan_applications", "illustrative_score")
