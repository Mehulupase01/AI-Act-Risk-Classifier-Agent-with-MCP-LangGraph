from __future__ import annotations

from typing import Any

import httpx

from eu_comply_api.config import Settings
from eu_comply_api.domain.models import ProviderKind
from eu_comply_api.runtime.base import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelCapability,
)


class OllamaAdapter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._timeout = httpx.Timeout(settings.request_timeout_seconds)

    async def list_models(self) -> list[ModelCapability]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
        models: list[ModelCapability] = []
        for item in payload.get("models", []):
            details = item.get("details", {})
            model_id = item.get("model", item.get("name", "unknown"))
            lowered = model_id.lower()
            models.append(
                ModelCapability(
                    provider=ProviderKind.OLLAMA,
                    model_id=model_id,
                    label=item.get("name", model_id),
                    context_length=item.get("context_length"),
                    supports_chat=True,
                    supports_embeddings=(
                        "embed" in lowered or "nomic" in lowered or "bge" in lowered
                    ),
                    supports_json_output=None,
                    input_modalities=["text"],
                    output_modalities=["text"],
                    notes=details.get("parameter_size"),
                )
            )
        return models

    async def chat(self, request: ChatRequest) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "stream": False,
        }
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()
        return ChatResponse(
            provider=ProviderKind.OLLAMA,
            model=body.get("model", request.model),
            content=body["message"]["content"],
            raw=body,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        payload: dict[str, Any] = {
            "model": request.model,
            "input": request.input_texts,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/embed", json=payload)
            response.raise_for_status()
            body = response.json()
        return EmbeddingResponse(
            provider=ProviderKind.OLLAMA,
            model=body.get("model", request.model),
            embeddings=body.get("embeddings", []),
            raw=body,
        )
