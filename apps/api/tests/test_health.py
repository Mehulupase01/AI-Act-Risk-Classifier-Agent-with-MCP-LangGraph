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
