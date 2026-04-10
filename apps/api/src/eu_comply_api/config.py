from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderKind = Literal["openrouter", "ollama"]
EnvironmentKind = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EU_COMPLY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EU-Comply API"
    app_version: str = "0.1.0"
    environment: EnvironmentKind = "development"
    api_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    auto_create_schema: bool = True

    database_url: str = (
        "postgresql+asyncpg://eu_comply:eu_comply@localhost:5432/eu_comply"
    )
    redis_url: str = "redis://localhost:6379/0"
    object_store_endpoint: str = "http://localhost:9000"
    object_store_bucket: str = "eu-comply-artifacts"
    object_store_access_key: str = "eucomply"
    object_store_secret_key: str = "eucomply123"

    bootstrap_default_org_slug: str = "default"
    bootstrap_default_org_name: str = "EU-Comply Default Organization"
    bootstrap_admin_email: str = "admin@eucomply.dev"
    bootstrap_admin_password: str = "change-me-now"
    bootstrap_api_client_id: str = "eu-comply-dev-client"
    bootstrap_api_client_secret: str = "eu-comply-dev-secret"
    policy_fixture_path: str | None = None

    llm_default_provider: ProviderKind = "ollama"
    embedding_default_provider: ProviderKind = "ollama"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str | None = None
    openrouter_default_model: str = "openai/gpt-4o-mini"
    openrouter_site_url: str | None = None
    openrouter_app_name: str = "EU-Comply"
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_chat_model: str = "qwen3:8b"
    ollama_default_embedding_model: str = "nomic-embed-text"

    request_timeout_seconds: float = Field(default=30.0, ge=1.0)
    runtime_discovery_timeout_seconds: float = Field(default=15.0, ge=1.0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
