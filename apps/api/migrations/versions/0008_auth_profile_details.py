"""Store registration location and optional profile image metadata."""

import sqlalchemy as sa
from alembic import op

revision = "0008_auth_profile_details"
down_revision = "0007_phases_9_11"
branch_labels = None
depends_on = None


def upgrade():
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("customers")}
    for name in ("country", "state", "city"):
        if name not in existing:
            op.add_column(
                "customers",
                sa.Column(name, sa.String(length=100), nullable=False, server_default=""),
            )
    if "profile_image_filename" not in existing:
        op.add_column(
            "customers", sa.Column("profile_image_filename", sa.String(length=255), nullable=True)
        )


def downgrade():
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("customers")}
    for name in ("profile_image_filename", "city", "state", "country"):
        if name in existing:
            op.drop_column("customers", name)
