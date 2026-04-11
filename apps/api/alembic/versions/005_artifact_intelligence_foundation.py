"""artifact intelligence foundation

Revision ID: 005_artifact_intelligence
Revises: 004_cases_and_dossiers
Create Date: 2026-04-10 08:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_artifact_intelligence"
down_revision: str | None = "004_cases_and_dossiers"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="uploaded"),
        sa.Column("parser_name", sa.String(length=120), nullable=True),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artifacts_case_id"), "artifacts", ["case_id"], unique=False)
    op.create_index(op.f("ix_artifacts_sha256"), "artifacts", ["sha256"], unique=False)
    op.create_index(op.f("ix_artifacts_status"), "artifacts", ["status"], unique=False)

    op.create_table(
        "artifact_chunks",
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "artifact_id",
            "chunk_index",
            name="uq_artifact_chunks_artifact_chunk_index",
        ),
    )
    op.create_index(op.f("ix_artifact_chunks_artifact_id"), "artifact_chunks", ["artifact_id"], unique=False)

    op.create_table(
        "extracted_facts",
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("field_path", sa.String(length=255), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="candidate"),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("source_chunk_indexes", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_extracted_facts_artifact_id"), "extracted_facts", ["artifact_id"], unique=False)
    op.create_index(op.f("ix_extracted_facts_case_id"), "extracted_facts", ["case_id"], unique=False)
    op.create_index(op.f("ix_extracted_facts_field_path"), "extracted_facts", ["field_path"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_extracted_facts_field_path"), table_name="extracted_facts")
    op.drop_index(op.f("ix_extracted_facts_case_id"), table_name="extracted_facts")
    op.drop_index(op.f("ix_extracted_facts_artifact_id"), table_name="extracted_facts")
    op.drop_table("extracted_facts")
    op.drop_index(op.f("ix_artifact_chunks_artifact_id"), table_name="artifact_chunks")
    op.drop_table("artifact_chunks")
    op.drop_index(op.f("ix_artifacts_status"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_sha256"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_case_id"), table_name="artifacts")
    op.drop_table("artifacts")
