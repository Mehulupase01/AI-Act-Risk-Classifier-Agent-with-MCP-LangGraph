"""assessment runs foundation

Revision ID: 006_assessment_runs
Revises: 005_artifact_intelligence
Create Date: 2026-04-10 10:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_assessment_runs"
down_revision: str | None = "005_artifact_intelligence"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessment_runs",
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("rule_pack_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("primary_outcome", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("facts_json", sa.JSON(), nullable=False),
        sa.Column("conflict_fields", sa.JSON(), nullable=False),
        sa.Column("hits_json", sa.JSON(), nullable=False),
        sa.Column("obligations_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assessment_runs_case_id"), "assessment_runs", ["case_id"], unique=False)
    op.create_index(op.f("ix_assessment_runs_status"), "assessment_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_assessment_runs_status"), table_name="assessment_runs")
    op.drop_index(op.f("ix_assessment_runs_case_id"), table_name="assessment_runs")
    op.drop_table("assessment_runs")
