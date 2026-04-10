from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProviderKind(StrEnum):
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class ActorType(StrEnum):
    USER = "user"
    API_CLIENT = "api_client"


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class OrganizationSummary(BaseModel):
    id: UUID
    slug: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    actor_type: ActorType
    organization: OrganizationSummary


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class ClientTokenRequest(BaseModel):
    client_id: str = Field(min_length=3)
    client_secret: str = Field(min_length=8)


class RuntimeConfigResponse(BaseModel):
    organization: OrganizationSummary
    default_provider: ProviderKind
    default_chat_model: str
    default_embedding_provider: ProviderKind
    default_embedding_model: str
    created_at: datetime
    updated_at: datetime


class RuntimeConfigUpdate(BaseModel):
    default_provider: ProviderKind | None = None
    default_chat_model: str | None = None
    default_embedding_provider: ProviderKind | None = None
    default_embedding_model: str | None = None


class ProviderSummary(BaseModel):
    provider: ProviderKind
    label: str
    base_url: str
    configured: bool
    supports_chat: bool
    supports_embeddings: bool


class ModelCapabilitySummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    provider: ProviderKind
    model_id: str = Field(alias="modelId")
    label: str
    context_length: int | None = Field(default=None, alias="contextLength")
    supports_chat: bool = Field(alias="supportsChat")
    supports_embeddings: bool | None = Field(default=None, alias="supportsEmbeddings")
    supports_json_output: bool | None = Field(default=None, alias="supportsJsonOutput")
    input_modalities: list[str] = Field(default_factory=list, alias="inputModalities")
    output_modalities: list[str] = Field(default_factory=list, alias="outputModalities")
    notes: str | None = None


class RuntimeDiscoveryResponse(BaseModel):
    provider: ProviderKind
    models: list[ModelCapabilitySummary]


class LivenessResponse(BaseModel):
    status: HealthStatus
    service: str
    version: str
    environment: str


class ReadinessCheck(BaseModel):
    name: str
    status: HealthStatus
    detail: str


class ReadinessResponse(BaseModel):
    status: HealthStatus
    checks: list[ReadinessCheck]
