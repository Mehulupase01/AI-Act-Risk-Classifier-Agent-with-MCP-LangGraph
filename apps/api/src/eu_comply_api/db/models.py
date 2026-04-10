from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, UniqueConstraint
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

    users: Mapped[list["UserRecord"]] = relationship(back_populates="organization")
    api_clients: Mapped[list["ApiClientRecord"]] = relationship(back_populates="organization")
    runtime_profile: Mapped["LLMRuntimeProfileRecord | None"] = relationship(
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
