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
                "human_oversight_summary": "Recruiters review each recommendation.",
            },
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


def test_review_approval_closes_review_gate_and_updates_case(client: TestClient) -> None:
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

    workflow = client.post(
        f"/api/v1/cases/{case_id}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    review = client.post(
        f"/api/v1/cases/{case_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "workflow_run_id": workflow["id"],
            "assessment_run_id": workflow["assessment_run_id"],
            "decision": "approved",
            "rationale": "Compliance reviewer approved the escalated workflow outcome.",
            "approved_outcome": "needs_more_information",
        },
    )

    assert review.status_code == 201
    payload = review.json()
    assert payload["decision"] == "approved"
    assert payload["approved_outcome"] == "needs_more_information"

    reviews = client.get(
        f"/api/v1/cases/{case_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reviews.status_code == 200
    assert len(reviews.json()) == 1

    case_detail = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert case_detail.status_code == 200
    assert case_detail.json()["status"] == "approved"

    workflow_detail = client.get(
        f"/api/v1/cases/{case_id}/workflow-runs/{workflow['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert workflow_detail.status_code == 200
    assert workflow_detail.json()["status"] == "completed"
    assert workflow_detail.json()["review_required"] is False


def test_review_requires_matching_workflow_and_assessment(client: TestClient) -> None:
    token = _get_token(client)
    first_case_id = _create_case(client, token)
    _upload_and_process(
        client,
        token,
        first_case_id,
        "employment.txt",
        b"This hiring chatbot helps candidate screening in employment workflows.",
    )
    workflow = client.post(
        f"/api/v1/cases/{first_case_id}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assessment = client.post(
        f"/api/v1/cases/{first_case_id}/assessments",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    review = client.post(
        f"/api/v1/cases/{first_case_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "workflow_run_id": workflow["id"],
            "assessment_run_id": assessment["id"],
            "decision": "approved",
            "rationale": "This should fail because the run references do not match.",
        },
    )

    assert review.status_code == 400
    assert "does not match" in review.json()["detail"]
