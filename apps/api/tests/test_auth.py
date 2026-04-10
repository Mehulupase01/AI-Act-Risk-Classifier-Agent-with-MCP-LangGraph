from fastapi.testclient import TestClient


def test_user_login(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eucomply.dev", "password": "change-me-now"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["actor_type"] == "user"
    assert payload["organization"]["slug"] == "default"


def test_client_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/token",
        json={
            "client_id": "eu-comply-dev-client",
            "client_secret": "eu-comply-dev-secret",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["actor_type"] == "api_client"
