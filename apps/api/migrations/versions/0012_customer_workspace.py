"""Add support, budget, goal and simulated deposit records."""

import sqlalchemy as sa
from alembic import op

revision = "0012_customer_workspace"
down_revision = "0011_totp_mfa"
branch_labels = None
depends_on = None


def _tables():
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade():
    tables = _tables()
    if "support_tickets" not in tables:
        op.create_table(
            "support_tickets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("subject", sa.String(160), nullable=False),
            sa.Column("category", sa.String(40), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="open"),
            sa.Column("staff_response", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])
    if "spending_budgets" not in tables:
        op.create_table(
            "spending_budgets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
            sa.Column("month", sa.String(7), nullable=False),
            sa.Column("category", sa.String(40), nullable=False),
            sa.Column("limit_amount", sa.Numeric(20, 4), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="PKR"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("customer_id", "month", "category"),
        )
        op.create_index("ix_spending_budgets_customer_id", "spending_budgets", ["customer_id"])
    if "savings_goals" not in tables:
        op.create_table(
            "savings_goals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("target_amount", sa.Numeric(20, 4), nullable=False),
            sa.Column("current_amount", sa.Numeric(20, 4), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(3), nullable=False, server_default="PKR"),
            sa.Column("target_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(30), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_savings_goals_customer_id", "savings_goals", ["customer_id"])
    if "deposit_positions" not in tables:
        op.create_table(
            "deposit_positions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
            sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
            sa.Column("product_code", sa.String(40), nullable=False),
            sa.Column("principal", sa.Numeric(20, 4), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("term_months", sa.Integer(), nullable=False),
            sa.Column("annual_yield", sa.Numeric(8, 4), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="simulated_active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_deposit_positions_customer_id", "deposit_positions", ["customer_id"])
        op.create_index("ix_deposit_positions_account_id", "deposit_positions", ["account_id"])


def downgrade():
    tables = _tables()
    if "deposit_positions" in tables:
        op.drop_table("deposit_positions")
    if "savings_goals" in tables:
        op.drop_table("savings_goals")
    if "spending_budgets" in tables:
        op.drop_table("spending_budgets")
    if "support_tickets" in tables:
        op.drop_table("support_tickets")
