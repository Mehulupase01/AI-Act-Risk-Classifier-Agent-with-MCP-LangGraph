from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProviderKind(StrEnum):
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class AssessmentOutcome(StrEnum):
    OUT_OF_SCOPE = "out_of_scope"
    PROHIBITED = "prohibited"
    HIGH_RISK = "high_risk"
    TRANSPARENCY_ONLY = "transparency_only"
    GPAI_RELATED = "gpai_related"
    MINIMAL_RISK = "minimal_risk"
    NEEDS_MORE_INFORMATION = "needs_more_information"


class ActorType(StrEnum):
    USER = "user"
    API_CLIENT = "api_client"


class ActorRole(StrEnum):
    PROVIDER = "provider"
    DEPLOYER = "deployer"
    IMPORTER = "importer"
    DISTRIBUTOR = "distributor"
    AUTHORIZED_REPRESENTATIVE = "authorized_representative"
    OTHER = "other"


class CaseStatus(StrEnum):
    DRAFT = "draft"
    INTAKE_IN_PROGRESS = "intake_in_progress"
    READY_FOR_ASSESSMENT = "ready_for_assessment"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    NEEDS_CHANGES = "needs_changes"


class ArtifactStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSED = "processed"
    FAILED = "failed"


class ExtractedFactStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFLICT = "conflict"


class AssessmentRunStatus(StrEnum):
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


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


class PolicySourceSummary(BaseModel):
    id: UUID
    slug: str
    title: str
    source_type: str
    authority: str
    url: str
    status: str


class PolicySnapshotSummary(BaseModel):
    id: UUID
    slug: str
    title: str
    jurisdiction: str
    effective_from: datetime
    description: str
    sources: list[PolicySourceSummary]


class NormFragmentSummary(BaseModel):
    id: UUID
    fragment_type: str
    citation: str
    heading: str
    body: str
    actor_scope: list[str]
    tags: list[str]
    order_index: int
    source_slug: str
    source_title: str


class PolicySnapshotDetail(PolicySnapshotSummary):
    fragments: list[NormFragmentSummary]


class RuleOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    EXISTS = "exists"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    CONTAINS_ANY = "contains_any"


class RuleCondition(BaseModel):
    field_path: str
    operator: RuleOperator
    value: str | bool | int | float | list[str] | None = None
    description: str | None = None


class RuleDefinition(BaseModel):
    rule_id: str
    title: str
    description: str
    priority: int
    outcome: AssessmentOutcome
    citation_refs: list[str]
    obligation_tags: list[str]
    conditions: list[RuleCondition]


class RulePackSummary(BaseModel):
    pack_id: str
    title: str
    version: str
    snapshot_slug: str
    description: str
    rule_count: int


class RulePackDetail(RulePackSummary):
    rules: list[RuleDefinition]


class RuleHit(BaseModel):
    rule_id: str
    title: str
    outcome: AssessmentOutcome
    priority: int
    citation_refs: list[str]
    obligation_tags: list[str]


class RuleEvaluationResult(BaseModel):
    pack_id: str
    primary_outcome: AssessmentOutcome | None = None
    hits: list[RuleHit]


class SystemDossierInput(BaseModel):
    system_name: str = Field(min_length=3)
    actor_role: ActorRole
    sector: str = Field(min_length=2)
    intended_purpose: str = Field(min_length=10)
    model_provider: str | None = None
    model_name: str | None = None
    uses_generative_ai: bool = False
    affects_natural_persons: bool = True
    geographic_scope: list[str] = Field(default_factory=list)
    deployment_channels: list[str] = Field(default_factory=list)
    human_oversight_summary: str | None = None


class SystemDossierResponse(SystemDossierInput):
    id: UUID
    case_id: UUID
    created_at: datetime
    updated_at: datetime


class CaseCreateRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str | None = None
    owner_team: str = Field(min_length=2)
    policy_snapshot_slug: str | None = None
    dossier: SystemDossierInput


class CaseUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    description: str | None = None
    owner_team: str | None = Field(default=None, min_length=2)
    status: CaseStatus | None = None
    policy_snapshot_slug: str | None = None
    dossier: SystemDossierInput | None = None


class CaseSummary(BaseModel):
    id: UUID
    title: str
    status: CaseStatus
    owner_team: str
    policy_snapshot_slug: str | None = None
    system_name: str
    actor_role: ActorRole
    created_at: datetime
    updated_at: datetime


class CaseDetail(CaseSummary):
    description: str | None = None
    dossier: SystemDossierResponse


class ArtifactSummary(BaseModel):
    id: UUID
    case_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    status: ArtifactStatus
    created_at: datetime
    updated_at: datetime


class ArtifactChunkSummary(BaseModel):
    id: UUID
    chunk_index: int
    text_preview: str
    char_start: int
    char_end: int


class ExtractedFactSummary(BaseModel):
    id: UUID
    field_path: str
    value: str | bool | int | float | list[str] | dict[str, str] | None
    confidence: float
    extraction_method: str
    status: ExtractedFactStatus
    rationale: str


class ArtifactDetail(ArtifactSummary):
    parser_name: str | None = None
    processing_error: str | None = None
    chunks: list[ArtifactChunkSummary]
    extracted_facts: list[ExtractedFactSummary]


class ArtifactProcessResponse(BaseModel):
    artifact: ArtifactDetail
    chunk_count: int
    fact_count: int
    conflict_count: int


class ObligationItem(BaseModel):
    tag: str
    title: str
    description: str


class AssessmentRunSummary(BaseModel):
    id: UUID
    case_id: UUID
    rule_pack_id: str
    status: AssessmentRunStatus
    primary_outcome: AssessmentOutcome
    created_at: datetime


class AssessmentRunDetail(AssessmentRunSummary):
    summary: str
    facts: dict[str, object]
    conflict_fields: list[str]
    hits: list[RuleHit]
    obligations: list[ObligationItem]


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
