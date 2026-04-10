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
            "title": "Claims Assistant",
            "description": "Insurance claims support system",
            "owner_team": "AI Governance",
            "policy_snapshot_slug": "eu-ai-act-baseline-2026-04-10",
            "dossier": {
                "system_name": "Claims Assistant",
                "actor_role": "provider",
                "sector": "insurance",
                "intended_purpose": "Support claims triage and insurer case handling decisions.",
                "uses_generative_ai": True,
                "affects_natural_persons": True,
                "geographic_scope": ["EU"],
                "deployment_channels": ["internal_web_app"],
                "human_oversight_summary": "Claims staff review generated recommendations.",
            },
        },
    )
    return response.json()["id"]


def test_connector_sync_creates_and_processes_reassessment(client: TestClient) -> None:
    token = _get_token(client)
    case_id = _create_case(client, token)

    connector = client.post(
        "/api/v1/connectors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Primary Model Registry",
            "slug": "primary-model-registry",
            "kind": "model_registry",
            "description": "Captures promoted model versions.",
            "config": {"workspace": "registry-prod"},
        },
    )
    assert connector.status_code == 201
    connector_id = connector.json()["id"]

    sync = client.post(
        f"/api/v1/connectors/{connector_id}/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "events": [
                {
                    "case_id": case_id,
                    "reason": "model_changed",
                    "title": "Production model upgraded",
                    "detail": "The registry promoted a new foundation model revision.",
                    "payload": {"from_version": "2026.03", "to_version": "2026.04"},
                }
            ],
            "auto_process_triggers": True,
        },
    )
    assert sync.status_code == 200
    sync_payload = sync.json()
    assert sync_payload["sync_run"]["trigger_count"] == 1
    assert sync_payload["sync_run"]["processed_trigger_count"] == 1
    assert sync_payload["triggers"][0]["status"] == "processed"
    assert sync_payload["triggers"][0]["workflow_run_id"] is not None

    reassessments = client.get(
        f"/api/v1/cases/{case_id}/reassessments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reassessments.status_code == 200
    assert len(reassessments.json()) == 1
    assert reassessments.json()[0]["reason"] == "model_changed"

    sync_runs = client.get(
        f"/api/v1/connectors/{connector_id}/sync-runs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sync_runs.status_code == 200
    assert len(sync_runs.json()) == 1
    assert sync_runs.json()[0]["status"] == "completed"


def test_manual_reassessment_can_remain_pending(client: TestClient) -> None:
    token = _get_token(client)
    case_id = _create_case(client, token)

    reassessment = client.post(
        f"/api/v1/cases/{case_id}/reassessments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "reason": "manual_request",
            "title": "Re-check insurer workflow scope",
            "detail": "The deployment scope changed and needs a human-led reassessment.",
            "auto_process": False,
        },
    )
    assert reassessment.status_code == 201
    payload = reassessment.json()
    assert payload["status"] == "pending"
    assert payload["workflow_run_id"] is None

    listing = client.get(
        f"/api/v1/cases/{case_id}/reassessments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["title"] == "Re-check insurer workflow scope"


def test_connector_sync_rejects_unsupported_reassessment_reason(client: TestClient) -> None:
    token = _get_token(client)
    case_id = _create_case(client, token)

    connector = client.post(
        "/api/v1/connectors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Evidence Drive",
            "slug": "evidence-drive",
            "kind": "document_repository",
            "config": {"library": "sharepoint"},
        },
    )
    connector_id = connector.json()["id"]

    sync = client.post(
        f"/api/v1/connectors/{connector_id}/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "case_id": case_id,
            "events": [
                {
                    "reason": "model_changed",
                    "title": "Wrong connector event",
                }
            ],
        },
    )
    assert sync.status_code == 400
    assert "does not support" in sync.json()["detail"]
