"""Remove 50-clap cap from claps table."""

from alembic import op


revision = "20260404_0003"
down_revision = "20260402_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("clap_count_range", "claps", type_="check")
    op.create_check_constraint("clap_count_min", "claps", "count >= 1")


def downgrade() -> None:
    op.drop_constraint("clap_count_min", "claps", type_="check")
    op.create_check_constraint("clap_count_range", "claps", "count >= 1 AND count <= 50")
