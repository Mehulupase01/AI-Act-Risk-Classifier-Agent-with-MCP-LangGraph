from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eu_comply_api.db.base import (
    Base,
    NamedSlugMixin,
    TenantScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class OrganizationRecord(UUIDPrimaryKeyMixin, TimestampMixin, NamedSlugMixin, Base):
    __tablename__ = "organizations"

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list[UserRecord]] = relationship(back_populates="organization")
    api_clients: Mapped[list[ApiClientRecord]] = relationship(back_populates="organization")
    cases: Mapped[list[CaseRecord]] = relationship(back_populates="organization")
    runtime_profile: Mapped[LLMRuntimeProfileRecord | None] = relationship(
        back_populates="organization",
        uselist=False,
    )


class UserRecord(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped[OrganizationRecord] = relationship(back_populates="users")


class ApiClientRecord(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "api_clients"
    __table_args__ = (
        UniqueConstraint("client_id", name="uq_api_clients_client_id"),
    )

    client_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    client_secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    organization: Mapped[OrganizationRecord] = relationship(back_populates="api_clients")


class AuditEventRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_events"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class LLMRuntimeProfileRecord(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "llm_runtime_profiles"
    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_llm_runtime_profiles_org"),
    )

    default_provider: Mapped[str] = mapped_column(String(32), default="ollama", nullable=False)
    default_chat_model: Mapped[str] = mapped_column(String(255), nullable=False)
    default_embedding_provider: Mapped[str] = mapped_column(
        String(32), default="ollama", nullable=False
    )
    default_embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped[OrganizationRecord] = relationship(back_populates="runtime_profile")


class CaseRecord(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "cases"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="draft", nullable=False, index=True)
    owner_team: Mapped[str] = mapped_column(String(120), nullable=False)
    policy_snapshot_slug: Mapped[str | None] = mapped_column(String(120), nullable=True)

    organization: Mapped[OrganizationRecord] = relationship(back_populates="cases")
    dossier: Mapped[SystemDossierRecord | None] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        uselist=False,
    )


class SystemDossierRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "system_dossiers"
    __table_args__ = (UniqueConstraint("case_id", name="uq_system_dossiers_case_id"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    system_name: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(64), nullable=False)
    sector: Mapped[str] = mapped_column(String(120), nullable=False)
    intended_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uses_generative_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    affects_natural_persons: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    geographic_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    deployment_channels: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    human_oversight_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped[CaseRecord] = relationship(back_populates="dossier")


class PolicySourceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "policy_sources"

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    authority: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)

    fragments: Mapped[list[NormFragmentRecord]] = relationship(back_populates="source")


class PolicySnapshotRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "policy_snapshots"

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_from: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    fragments: Mapped[list[NormFragmentRecord]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="NormFragmentRecord.order_index",
    )


class NormFragmentRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "norm_fragments"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "fragment_type",
            "citation",
            name="uq_norm_fragments_snapshot_fragment_type_citation",
        ),
    )

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fragment_type: Mapped[str] = mapped_column(String(64), nullable=False)
    citation: Mapped[str] = mapped_column(String(120), nullable=False)
    heading: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    actor_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    snapshot: Mapped[PolicySnapshotRecord] = relationship(back_populates="fragments")
    source: Mapped[PolicySourceRecord] = relationship(back_populates="fragments")
