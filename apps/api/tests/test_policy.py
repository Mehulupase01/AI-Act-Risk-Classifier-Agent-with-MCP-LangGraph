from fastapi.testclient import TestClient


def _get_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eucomply.dev", "password": "change-me-now"},
    )
    return response.json()["access_token"]


def test_policy_snapshots_are_seeded_and_listed(client: TestClient) -> None:
    token = _get_token(client)
    response = client.get(
        "/api/v1/policy-snapshots",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    snapshot = payload[0]
    assert snapshot["slug"] == "eu-ai-act-baseline-2026-04-10"
    assert snapshot["jurisdiction"] == "eu"
    assert len(snapshot["sources"]) == 3
    assert snapshot["sources"][0]["slug"] == "eu-ai-act-regulation"


def test_policy_sources_are_listed(client: TestClient) -> None:
    token = _get_token(client)
    response = client.get(
        "/api/v1/policy-sources",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3
    assert {source["slug"] for source in payload} == {
        "eu-ai-act-regulation",
        "eu-ai-act-faq",
        "eu-ai-act-standardisation",
    }


def test_policy_snapshot_detail_includes_fragments(client: TestClient) -> None:
    token = _get_token(client)
    response = client.get(
        "/api/v1/policy-snapshots/eu-ai-act-baseline-2026-04-10",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "eu-ai-act-baseline-2026-04-10"
    assert len(payload["fragments"]) == 5
    assert payload["fragments"][0]["citation"] == "Article 5"
    assert payload["fragments"][0]["source_slug"] == "eu-ai-act-regulation"
