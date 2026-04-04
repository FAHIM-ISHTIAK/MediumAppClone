"""Add is_edited flag to responses."""

import sqlalchemy as sa

from alembic import op


revision = "20260404_0005"
down_revision = "20260404_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "responses",
        sa.Column("is_edited", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("responses", "is_edited")
