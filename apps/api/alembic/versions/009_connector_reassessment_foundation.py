"""connector and reassessment foundation

Revision ID: 009_connector_reassessment_foundation
Revises: 008_review_decisions
Create Date: 2026-04-10 22:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009_connector_reassessment_foundation"
down_revision: str | None = "008_review_decisions"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connectors",
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_connectors_org_slug"),
    )
    op.create_index(op.f("ix_connectors_kind"), "connectors", ["kind"], unique=False)
    op.create_index(
        op.f("ix_connectors_organization_id"),
        "connectors",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_connectors_slug"), "connectors", ["slug"], unique=False)
    op.create_index(op.f("ix_connectors_status"), "connectors", ["status"], unique=False)

    op.create_table(
        "connector_sync_runs",
        sa.Column("connector_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("initiated_by", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("trigger_count", sa.Integer(), nullable=False),
        sa.Column("processed_trigger_count", sa.Integer(), nullable=False),
        sa.Column("unmapped_event_count", sa.Integer(), nullable=False),
        sa.Column("request_payload_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["connector_id"], ["connectors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_connector_sync_runs_case_id"),
        "connector_sync_runs",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_connector_sync_runs_connector_id"),
        "connector_sync_runs",
        ["connector_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_connector_sync_runs_organization_id"),
        "connector_sync_runs",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_connector_sync_runs_status"),
        "connector_sync_runs",
        ["status"],
        unique=False,
    )

    op.create_table(
        "reassessment_triggers",
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("connector_id", sa.Uuid(), nullable=True),
        sa.Column("sync_run_id", sa.Uuid(), nullable=True),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connector_id"], ["connectors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["sync_run_id"],
            ["connector_sync_runs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reassessment_triggers_case_id"),
        "reassessment_triggers",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reassessment_triggers_connector_id"),
        "reassessment_triggers",
        ["connector_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reassessment_triggers_reason"),
        "reassessment_triggers",
        ["reason"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reassessment_triggers_status"),
        "reassessment_triggers",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reassessment_triggers_sync_run_id"),
        "reassessment_triggers",
        ["sync_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reassessment_triggers_workflow_run_id"),
        "reassessment_triggers",
        ["workflow_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_reassessment_triggers_workflow_run_id"),
        table_name="reassessment_triggers",
    )
    op.drop_index(op.f("ix_reassessment_triggers_sync_run_id"), table_name="reassessment_triggers")
    op.drop_index(op.f("ix_reassessment_triggers_status"), table_name="reassessment_triggers")
    op.drop_index(op.f("ix_reassessment_triggers_reason"), table_name="reassessment_triggers")
    op.drop_index(op.f("ix_reassessment_triggers_connector_id"), table_name="reassessment_triggers")
    op.drop_index(op.f("ix_reassessment_triggers_case_id"), table_name="reassessment_triggers")
    op.drop_table("reassessment_triggers")

    op.drop_index(op.f("ix_connector_sync_runs_status"), table_name="connector_sync_runs")
    op.drop_index(
        op.f("ix_connector_sync_runs_organization_id"),
        table_name="connector_sync_runs",
    )
    op.drop_index(op.f("ix_connector_sync_runs_connector_id"), table_name="connector_sync_runs")
    op.drop_index(op.f("ix_connector_sync_runs_case_id"), table_name="connector_sync_runs")
    op.drop_table("connector_sync_runs")

    op.drop_index(op.f("ix_connectors_status"), table_name="connectors")
    op.drop_index(op.f("ix_connectors_slug"), table_name="connectors")
    op.drop_index(op.f("ix_connectors_organization_id"), table_name="connectors")
    op.drop_index(op.f("ix_connectors_kind"), table_name="connectors")
    op.drop_table("connectors")
