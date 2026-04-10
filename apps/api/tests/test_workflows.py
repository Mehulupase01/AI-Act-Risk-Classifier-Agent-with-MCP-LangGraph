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
            "title": "Hiring Assistant",
            "description": "Employment support tool",
            "owner_team": "AI Governance",
            "policy_snapshot_slug": "eu-ai-act-baseline-2026-04-10",
            "dossier": {
                "system_name": "Hiring Assistant",
                "actor_role": "provider",
                "sector": "employment",
                "intended_purpose": "Assist recruiters with candidate screening decisions.",
                "uses_generative_ai": True,
                "affects_natural_persons": True,
                "geographic_scope": ["EU"],
                "deployment_channels": ["internal_web_app"],
                "human_oversight_summary": "Recruiters review each recommendation."
            }
        },
    )
    return response.json()["id"]


def _upload_and_process(
    client: TestClient,
    token: str,
    case_id: str,
    filename: str,
    payload: bytes,
) -> None:
    upload = client.post(
        f"/api/v1/cases/{case_id}/artifacts",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, payload, "text/plain")},
    )
    artifact_id = upload.json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/artifacts/{artifact_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_workflow_run_completes_for_clean_case(client: TestClient) -> None:
    token = _get_token(client)
    case_id = _create_case(client, token)
    _upload_and_process(
        client,
        token,
        case_id,
        "employment.txt",
        (
            b"This hiring chatbot helps candidate screening in employment workflows. "
            b"Recruiters review all outputs before action."
        ),
    )

    response = client.post(
        f"/api/v1/cases/{case_id}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["review_required"] is False
    assert payload["assessment_run_id"] is not None


def test_workflow_run_routes_conflict_case_to_review(client: TestClient) -> None:
    token = _get_token(client)
    case_id = _create_case(client, token)
    _upload_and_process(
        client,
        token,
        case_id,
        "employment.txt",
        b"Candidate screening for hiring decisions.",
    )
    _upload_and_process(
        client,
        token,
        case_id,
        "finance.txt",
        b"Credit scoring support for bank loan decisions.",
    )

    response = client.post(
        f"/api/v1/cases/{case_id}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "pending_review"
    assert payload["review_required"] is True
    assert payload["review_reason"] is not None

    listing = client.get(
        f"/api/v1/cases/{case_id}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1
