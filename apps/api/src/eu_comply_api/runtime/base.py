from __future__ import annotations

from dataclasses import dataclass, field

from eu_comply_api.domain.models import ProviderKind


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


@dataclass(slots=True)
class ChatRequest:
    model: str
    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass(slots=True)
class ChatResponse:
    provider: ProviderKind
    model: str
    content: str
    raw: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class EmbeddingRequest:
    model: str
    input_texts: list[str]


@dataclass(slots=True)
class EmbeddingResponse:
    provider: ProviderKind
    model: str
    embeddings: list[list[float]]
    raw: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ModelCapability:
    provider: ProviderKind
    model_id: str
    label: str
    context_length: int | None
    supports_chat: bool
    supports_embeddings: bool | None
    supports_json_output: bool | None
    input_modalities: list[str]
    output_modalities: list[str]
    notes: str | None = None
