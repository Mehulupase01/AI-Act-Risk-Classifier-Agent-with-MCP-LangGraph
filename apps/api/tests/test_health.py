from fastapi.testclient import TestClient


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health/liveness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "EU-Comply API"


def test_readiness(client: TestClient) -> None:
    response = client.get("/api/v1/health/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checks"][0]["name"] == "configuration"


def test_cors_preflight_for_browser_console(client: TestClient) -> None:
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
