"""norm fragments foundation

Revision ID: 003_norm_fragments
Revises: 002_policy_snapshot_foundation
Create Date: 2026-04-10 04:05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_norm_fragments"
down_revision: str | None = "002_policy_snapshot_foundation"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "norm_fragments",
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("fragment_type", sa.String(length=64), nullable=False),
        sa.Column("citation", sa.String(length=120), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("actor_scope", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["snapshot_id"], ["policy_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["policy_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_id",
            "fragment_type",
            "citation",
            name="uq_norm_fragments_snapshot_fragment_type_citation",
        ),
    )
    op.create_index(op.f("ix_norm_fragments_snapshot_id"), "norm_fragments", ["snapshot_id"], unique=False)
    op.create_index(op.f("ix_norm_fragments_source_id"), "norm_fragments", ["source_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_norm_fragments_source_id"), table_name="norm_fragments")
    op.drop_index(op.f("ix_norm_fragments_snapshot_id"), table_name="norm_fragments")
    op.drop_table("norm_fragments")
