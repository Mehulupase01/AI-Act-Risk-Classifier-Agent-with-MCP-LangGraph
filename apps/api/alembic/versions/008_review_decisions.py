"""review decisions foundation

Revision ID: 008_review_decisions
Revises: 007_workflow_runs
Create Date: 2026-04-10 21:25:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_review_decisions"
down_revision: str | None = "007_workflow_runs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_decisions",
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_run_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_identifier", sa.String(length=255), nullable=False),
        sa.Column("decision", sa.String(length=64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("approved_outcome", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["assessment_run_id"], ["assessment_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_review_decisions_assessment_run_id"),
        "review_decisions",
        ["assessment_run_id"],
        unique=False,
    )
    op.create_index(op.f("ix_review_decisions_case_id"), "review_decisions", ["case_id"], unique=False)
    op.create_index(
        op.f("ix_review_decisions_decision"),
        "review_decisions",
        ["decision"],
        unique=False,
    )
    op.create_index(
        op.f("ix_review_decisions_workflow_run_id"),
        "review_decisions",
        ["workflow_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_review_decisions_workflow_run_id"), table_name="review_decisions")
    op.drop_index(op.f("ix_review_decisions_decision"), table_name="review_decisions")
    op.drop_index(op.f("ix_review_decisions_case_id"), table_name="review_decisions")
    op.drop_index(op.f("ix_review_decisions_assessment_run_id"), table_name="review_decisions")
    op.drop_table("review_decisions")
