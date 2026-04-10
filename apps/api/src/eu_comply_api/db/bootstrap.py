from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.config import Settings
from eu_comply_api.core.security import hash_password
from eu_comply_api.db.models import (
    ApiClientRecord,
    LLMRuntimeProfileRecord,
    OrganizationRecord,
    UserRecord,
)
from eu_comply_api.services.policy_fixture_loader import PolicyFixtureLoader


async def bootstrap_defaults(session: AsyncSession, settings: Settings) -> None:
    organization = await session.scalar(
        select(OrganizationRecord).where(
            OrganizationRecord.slug == settings.bootstrap_default_org_slug,
        )
    )
    if organization is None:
        organization = OrganizationRecord(
            slug=settings.bootstrap_default_org_slug,
            name=settings.bootstrap_default_org_name,
        )
        session.add(organization)
        await session.flush()

    admin_user = await session.scalar(
        select(UserRecord).where(
            UserRecord.organization_id == organization.id,
            UserRecord.email == settings.bootstrap_admin_email,
        )
    )
    if admin_user is None:
        session.add(
            UserRecord(
                organization_id=organization.id,
                email=settings.bootstrap_admin_email,
                display_name="EU-Comply Admin",
                hashed_password=hash_password(settings.bootstrap_admin_password),
                is_superuser=True,
            )
        )

    api_client = await session.scalar(
        select(ApiClientRecord).where(ApiClientRecord.client_id == settings.bootstrap_api_client_id)
    )
    if api_client is None:
        session.add(
            ApiClientRecord(
                organization_id=organization.id,
                client_id=settings.bootstrap_api_client_id,
                client_secret_hash=hash_password(settings.bootstrap_api_client_secret),
                name="Default Bootstrap Client",
                description="Bootstrap client for local development and service flows.",
                scopes=["runtime:read", "runtime:write"],
            )
        )

    runtime_profile = await session.scalar(
        select(LLMRuntimeProfileRecord).where(
            LLMRuntimeProfileRecord.organization_id == organization.id,
        )
    )
    if runtime_profile is None:
        session.add(
            LLMRuntimeProfileRecord(
                organization_id=organization.id,
                default_provider=settings.llm_default_provider,
                default_chat_model=(
                    settings.ollama_default_chat_model
                    if settings.llm_default_provider == "ollama"
                    else settings.openrouter_default_model
                ),
                default_embedding_provider=settings.embedding_default_provider,
                default_embedding_model=settings.ollama_default_embedding_model,
                metadata_json={},
            )
        )

    loader = PolicyFixtureLoader(session)
    await loader.seed_default_fixture(settings.policy_fixture_path)
