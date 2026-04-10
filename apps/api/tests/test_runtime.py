from fastapi.testclient import TestClient

from eu_comply_api.config import get_settings
from eu_comply_api.runtime.factory import build_runtime_adapter


def _get_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eucomply.dev", "password": "change-me-now"},
    )
    return response.json()["access_token"]


def test_runtime_providers(client: TestClient) -> None:
    token = _get_token(client)
    response = client.get(
        "/api/v1/runtime/providers",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert {item["provider"] for item in payload} == {"openrouter", "ollama"}


def test_runtime_config_update(client: TestClient) -> None:
    token = _get_token(client)
    update = client.put(
        "/api/v1/runtime/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "default_provider": "openrouter",
            "default_chat_model": "openai/gpt-4o-mini",
            "default_embedding_provider": "ollama",
            "default_embedding_model": "nomic-embed-text",
        },
    )

    assert update.status_code == 200
    payload = update.json()
    assert payload["default_provider"] == "openrouter"


def test_runtime_model_discovery_can_be_mocked(
    client: TestClient,
    monkeypatch,
) -> None:
    token = _get_token(client)

    async def fake_list_models():
        return []

    adapter = build_runtime_adapter("ollama", get_settings())
    monkeypatch.setattr(adapter, "list_models", fake_list_models)
    monkeypatch.setattr(
        "eu_comply_api.services.runtime_control_service.build_runtime_adapter",
        lambda provider, settings: adapter,
    )

    response = client.get(
        "/api/v1/runtime/models?provider=ollama",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "ollama"
