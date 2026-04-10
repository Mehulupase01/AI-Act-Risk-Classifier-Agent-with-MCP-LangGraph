from fastapi.testclient import TestClient


def _get_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eucomply.dev", "password": "change-me-now"},
    )
    return response.json()["access_token"]


def _case_payload() -> dict:
    return {
        "title": "Hiring Screening Assistant",
        "description": "Assesses inbound candidates before recruiter review.",
        "owner_team": "People Operations",
        "policy_snapshot_slug": "eu-ai-act-baseline-2026-04-10",
        "dossier": {
            "system_name": "Candidate Screening Assistant",
            "actor_role": "provider",
            "sector": "employment",
            "intended_purpose": "Support recruiters with candidate screening and triage.",
            "model_provider": "OpenAI",
            "model_name": "gpt-4.1-mini",
            "uses_generative_ai": True,
            "affects_natural_persons": True,
            "geographic_scope": ["EU"],
            "deployment_channels": ["internal_web_app"],
            "human_oversight_summary": (
                "Recruiters review every flagged recommendation before action."
            ),
        }
    }


def test_case_can_be_created_and_fetched(client: TestClient) -> None:
    token = _get_token(client)
    create = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"},
        json=_case_payload(),
    )

    assert create.status_code == 201
    payload = create.json()
    assert payload["title"] == "Hiring Screening Assistant"
    assert payload["status"] == "draft"
    assert payload["dossier"]["system_name"] == "Candidate Screening Assistant"

    case_id = payload["id"]
    fetch = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert fetch.status_code == 200
    assert fetch.json()["id"] == case_id


def test_case_list_and_update_flow(client: TestClient) -> None:
    token = _get_token(client)
    created = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"},
        json=_case_payload(),
    )
    case_id = created.json()["id"]

    listing = client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert listing.status_code == 200
    payload = listing.json()
    assert len(payload) == 1
    assert payload[0]["system_name"] == "Candidate Screening Assistant"

    update = client.patch(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "status": "ready_for_assessment",
            "owner_team": "AI Governance",
            "dossier": {
                "system_name": "Candidate Screening Assistant",
                "actor_role": "deployer",
                "sector": "employment",
                "intended_purpose": "Support recruiters with candidate screening and triage.",
                "model_provider": "OpenAI",
                "model_name": "gpt-4.1-mini",
                "uses_generative_ai": True,
                "affects_natural_persons": True,
                "geographic_scope": ["EU", "DE"],
                "deployment_channels": ["internal_web_app"],
                "human_oversight_summary": (
                    "Recruiters review every flagged recommendation before action."
                ),
            }
        },
    )

    assert update.status_code == 200
    updated = update.json()
    assert updated["status"] == "ready_for_assessment"
    assert updated["owner_team"] == "AI Governance"
    assert updated["actor_role"] == "deployer"
    assert updated["dossier"]["geographic_scope"] == ["EU", "DE"]
