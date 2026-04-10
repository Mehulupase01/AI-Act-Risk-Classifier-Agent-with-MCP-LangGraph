"""cases and dossiers foundation

Revision ID: 004_cases_and_dossiers
Revises: 003_norm_fragments
Create Date: 2026-04-10 05:05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_cases_and_dossiers"
down_revision: str | None = "003_norm_fragments"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="draft"),
        sa.Column("owner_team", sa.String(length=120), nullable=False),
        sa.Column("policy_snapshot_slug", sa.String(length=120), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cases_organization_id"), "cases", ["organization_id"], unique=False)
    op.create_index(op.f("ix_cases_status"), "cases", ["status"], unique=False)

    op.create_table(
        "system_dossiers",
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("system_name", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=64), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=False),
        sa.Column("intended_purpose", sa.Text(), nullable=False),
        sa.Column("model_provider", sa.String(length=255), nullable=True),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("uses_generative_ai", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("affects_natural_persons", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("geographic_scope", sa.JSON(), nullable=False),
        sa.Column("deployment_channels", sa.JSON(), nullable=False),
        sa.Column("human_oversight_summary", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", name="uq_system_dossiers_case_id"),
    )
    op.create_index(op.f("ix_system_dossiers_case_id"), "system_dossiers", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_system_dossiers_case_id"), table_name="system_dossiers")
    op.drop_table("system_dossiers")
    op.drop_index(op.f("ix_cases_status"), table_name="cases")
    op.drop_index(op.f("ix_cases_organization_id"), table_name="cases")
    op.drop_table("cases")
