from fastapi.testclient import TestClient


def _get_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eucomply.dev", "password": "change-me-now"},
    )
    return response.json()["access_token"]


def _create_case(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Monitoring Case",
            "description": "Readiness and metrics coverage",
            "owner_team": "AI Governance",
            "policy_snapshot_slug": "eu-ai-act-baseline-2026-04-10",
            "dossier": {
                "system_name": "Monitoring Case",
                "actor_role": "provider",
                "sector": "employment",
                "intended_purpose": "Assist recruiters with candidate screening decisions.",
                "uses_generative_ai": True,
                "affects_natural_persons": True,
                "geographic_scope": ["EU"],
                "deployment_channels": ["internal_web_app"],
                "human_oversight_summary": "Recruiters review recommendations.",
            },
        },
    )
    return response.json()["id"]


def test_readiness_runs_real_checks(client: TestClient) -> None:
    response = client.get("/api/v1/health/readiness")

    assert response.status_code == 200
    payload = response.json()
    check_names = {check["name"] for check in payload["checks"]}
    assert {
        "configuration",
        "database",
        "bootstrap_organization",
        "policy_snapshots",
    } <= check_names


def test_metrics_exposes_org_scoped_counts(client: TestClient) -> None:
    token = _get_token(client)
    case_id = _create_case(client, token)

    connector = client.post(
        "/api/v1/connectors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Metrics Connector",
            "slug": "metrics-connector",
            "kind": "webhook",
            "config": {"channel": "internal"},
        },
    ).json()
    client.post(
        f"/api/v1/cases/{case_id}/reassessments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "reason": "manual_request",
            "title": "Metrics pending reassessment",
            "auto_process": False,
        },
    )
    client.post(
        f"/api/v1/connectors/{connector['id']}/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "events": [
                {
                    "case_id": case_id,
                    "reason": "evidence_updated",
                    "title": "Fresh evidence arrived",
                    "detail": "New supplier evidence bundle was uploaded.",
                }
            ],
            "auto_process_triggers": False,
        },
    )

    response = client.get(
        "/api/v1/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.text
    assert "eu_comply_cases_total 1" in payload
    assert "eu_comply_connectors_total 1" in payload
    assert "eu_comply_connector_sync_runs_total 1" in payload
    assert "eu_comply_reassessment_pending_total 2" in payload
