"""Add parent_id to responses for threaded replies."""

import sqlalchemy as sa

from alembic import op


revision = "20260404_0004"
down_revision = "20260404_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "responses",
        sa.Column("parent_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_responses_parent_id_responses",
        "responses",
        "responses",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_responses_parent_id", "responses", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_responses_parent_id", table_name="responses")
    op.drop_constraint("fk_responses_parent_id_responses", "responses", type_="foreignkey")
    op.drop_column("responses", "parent_id")
