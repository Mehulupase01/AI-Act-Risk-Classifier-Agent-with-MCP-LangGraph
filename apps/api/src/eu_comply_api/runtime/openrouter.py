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
from eu_comply_api.runtime.exceptions import RuntimeProviderError


class OpenRouterAdapter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._timeout = httpx.Timeout(settings.request_timeout_seconds)

    def _headers(self) -> dict[str, str]:
        if not self._settings.openrouter_api_key:
            raise RuntimeProviderError("OpenRouter API key is not configured.")
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        if self._settings.openrouter_site_url:
            headers["HTTP-Referer"] = self._settings.openrouter_site_url
        if self._settings.openrouter_app_name:
            headers["X-Title"] = self._settings.openrouter_app_name
        return headers

    async def list_models(self) -> list[ModelCapability]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._settings.openrouter_base_url}/models",
                headers=self._headers(),
            )
            response.raise_for_status()
            payload = response.json()
        models: list[ModelCapability] = []
        for item in payload.get("data", []):
            architecture = item.get("architecture", {})
            supported_parameters = set(item.get("supported_parameters", []))
            models.append(
                ModelCapability(
                    provider=ProviderKind.OPENROUTER,
                    model_id=item["id"],
                    label=item.get("name", item["id"]),
                    context_length=item.get("context_length")
                    or item.get("top_provider", {}).get("context_length"),
                    supports_chat=True,
                    supports_embeddings=False,
                    supports_json_output="response_format" in supported_parameters
                    or "structured_outputs" in supported_parameters,
                    input_modalities=list(architecture.get("input_modalities", ["text"])),
                    output_modalities=list(architecture.get("output_modalities", ["text"])),
                    notes=item.get("description"),
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
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_completion_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._settings.openrouter_base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        content = body["choices"][0]["message"]["content"]
        return ChatResponse(
            provider=ProviderKind.OPENROUTER,
            model=body.get("model", request.model),
            content=content,
            raw=body,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise RuntimeProviderError(
            "OpenRouter embeddings are not enabled in the first runtime slice."
        )
