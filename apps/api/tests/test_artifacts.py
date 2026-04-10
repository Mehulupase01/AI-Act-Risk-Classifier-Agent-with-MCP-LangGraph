from fastapi.testclient import TestClient


def _get_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eucomply.dev", "password": "change-me-now"},
    )
    return response.json()["access_token"]


def _create_case(client: TestClient, token: str) -> dict:
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
    return response.json()


def test_artifact_upload_and_processing_flow(client: TestClient) -> None:
    token = _get_token(client)
    case = _create_case(client, token)
    case_id = case["id"]

    upload = client.post(
        f"/api/v1/cases/{case_id}/artifacts",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "hiring-assistant.txt",
                b"This hiring chatbot helps candidate screening in employment workflows. "
                b"Recruiters review all outputs before action.",
                "text/plain",
            )
        },
    )

    assert upload.status_code == 201
    artifact = upload.json()
    assert artifact["filename"] == "hiring-assistant.txt"
    assert artifact["status"] == "uploaded"

    artifact_id = artifact["id"]
    process = client.post(
        f"/api/v1/cases/{case_id}/artifacts/{artifact_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert process.status_code == 200
    processed = process.json()
    assert processed["artifact"]["status"] == "processed"
    assert processed["chunk_count"] >= 1
    assert processed["fact_count"] >= 2
    assert {fact["field_path"] for fact in processed["artifact"]["extracted_facts"]} >= {
        "use_case.domain",
        "system.modalities",
    }

    listing = client.get(
        f"/api/v1/cases/{case_id}/artifacts",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(
        f"/api/v1/cases/{case_id}/artifacts/{artifact_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert detail.status_code == 200
    assert detail.json()["parser_name"] == "plain_text"


def test_artifact_conflicts_are_marked(client: TestClient) -> None:
    token = _get_token(client)
    case = _create_case(client, token)
    case_id = case["id"]

    first = client.post(
        f"/api/v1/cases/{case_id}/artifacts",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "candidate-screening.txt",
                b"Candidate screening for hiring decisions",
                "text/plain",
            )
        },
    ).json()
    client.post(
        f"/api/v1/cases/{case_id}/artifacts/{first['id']}/process",
        headers={"Authorization": f"Bearer {token}"},
    )

    second = client.post(
        f"/api/v1/cases/{case_id}/artifacts",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "credit-risk.txt",
                b"Credit scoring support for bank loan decisions.",
                "text/plain",
            )
        },
    ).json()
    processed = client.post(
        f"/api/v1/cases/{case_id}/artifacts/{second['id']}/process",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    conflict_facts = [
        fact for fact in processed["artifact"]["extracted_facts"] if fact["status"] == "conflict"
    ]
    assert conflict_facts
    assert conflict_facts[0]["field_path"] == "use_case.domain"
