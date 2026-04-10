from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.config import Settings
from eu_comply_api.db.models import LLMRuntimeProfileRecord, OrganizationRecord
from eu_comply_api.domain.models import (
    ModelCapabilitySummary,
    ProviderKind,
    ProviderSummary,
    RuntimeConfigResponse,
    RuntimeConfigUpdate,
    RuntimeDiscoveryResponse,
)
from eu_comply_api.runtime.factory import build_runtime_adapter


class RuntimeControlService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def list_providers(self) -> list[ProviderSummary]:
        return [
            ProviderSummary(
                provider=ProviderKind.OPENROUTER,
                label="OpenRouter",
                base_url=self._settings.openrouter_base_url,
                configured=bool(self._settings.openrouter_api_key),
                supports_chat=True,
                supports_embeddings=False,
            ),
            ProviderSummary(
                provider=ProviderKind.OLLAMA,
                label="Ollama",
                base_url=self._settings.ollama_base_url,
                configured=True,
                supports_chat=True,
                supports_embeddings=True,
            ),
        ]

    async def list_models(self, provider: ProviderKind) -> RuntimeDiscoveryResponse:
        adapter = build_runtime_adapter(provider, self._settings)
        models = await adapter.list_models()
        return RuntimeDiscoveryResponse(
            provider=provider,
            models=[
                ModelCapabilitySummary(
                    provider=model.provider,
                    modelId=model.model_id,
                    label=model.label,
                    contextLength=model.context_length,
                    supportsChat=model.supports_chat,
                    supportsEmbeddings=model.supports_embeddings,
                    supportsJsonOutput=model.supports_json_output,
                    inputModalities=model.input_modalities,
                    outputModalities=model.output_modalities,
                    notes=model.notes,
                )
                for model in models
            ],
        )

    async def get_runtime_config(self, organization_id: UUID) -> RuntimeConfigResponse:
        runtime_profile = await self._session.scalar(
            select(LLMRuntimeProfileRecord).where(
                LLMRuntimeProfileRecord.organization_id == organization_id,
            )
        )
        organization = await self._session.get(OrganizationRecord, organization_id)
        if runtime_profile is None or organization is None:
            raise ValueError("Runtime profile not found.")
        return RuntimeConfigResponse(
            organization={
                "id": organization.id,
                "slug": organization.slug,
                "name": organization.name,
            },
            default_provider=ProviderKind(runtime_profile.default_provider),
            default_chat_model=runtime_profile.default_chat_model,
            default_embedding_provider=ProviderKind(runtime_profile.default_embedding_provider),
            default_embedding_model=runtime_profile.default_embedding_model,
            created_at=runtime_profile.created_at,
            updated_at=runtime_profile.updated_at,
        )

    async def update_runtime_config(
        self,
        organization_id: UUID,
        payload: RuntimeConfigUpdate,
    ) -> RuntimeConfigResponse:
        runtime_profile = await self._session.scalar(
            select(LLMRuntimeProfileRecord).where(
                LLMRuntimeProfileRecord.organization_id == organization_id,
            )
        )
        if runtime_profile is None:
            raise ValueError("Runtime profile not found.")

        if payload.default_provider is not None:
            runtime_profile.default_provider = payload.default_provider
        if payload.default_chat_model is not None:
            runtime_profile.default_chat_model = payload.default_chat_model
        if payload.default_embedding_provider is not None:
            runtime_profile.default_embedding_provider = payload.default_embedding_provider
        if payload.default_embedding_model is not None:
            runtime_profile.default_embedding_model = payload.default_embedding_model

        await self._session.commit()
        await self._session.refresh(runtime_profile)
        return await self.get_runtime_config(organization_id)
