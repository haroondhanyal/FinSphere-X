"""Track one-time password reset token versions."""

import sqlalchemy as sa
from alembic import op

revision = "0009_password_reset_version"
down_revision = "0008_auth_profile_details"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "password_reset_version" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "password_reset_version", sa.Integer(), nullable=False, server_default="0"
            ),
        )


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "password_reset_version" in columns:
        op.drop_column("users", "password_reset_version")
