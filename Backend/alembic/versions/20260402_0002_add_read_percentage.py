"""Add read_percentage column to reading_history."""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0002"
down_revision = "20260401_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reading_history",
        sa.Column("read_percentage", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("reading_history", "read_percentage")
