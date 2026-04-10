import pytest
from fastapi.testclient import TestClient

from eu_comply_api.domain.models import AssessmentOutcome
from eu_comply_api.services.rule_pack_service import RulePackService


def _get_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eucomply.dev", "password": "change-me-now"},
    )
    return response.json()["access_token"]


def test_rule_packs_are_listed(client: TestClient) -> None:
    token = _get_token(client)
    response = client.get(
        "/api/v1/rule-packs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["pack_id"] == "eu-ai-act-baseline"
    assert payload[0]["rule_count"] == 3


def test_rule_pack_detail_is_available(client: TestClient) -> None:
    token = _get_token(client)
    response = client.get(
        "/api/v1/rule-packs/eu-ai-act-baseline",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["pack_id"] == "eu-ai-act-baseline"
    assert len(payload["rules"]) == 3
    assert payload["rules"][0]["outcome"] == "prohibited"


@pytest.mark.asyncio
async def test_rule_pack_evaluation_returns_prohibited_hit() -> None:
    service = RulePackService()
    facts = {
        "system": {"capabilities": {"remote_biometric_identification": True}},
        "deployment": {"context": {"law_enforcement_real_time_public_space": True}},
    }

    result = await service.evaluate("eu-ai-act-baseline", facts)

    assert result.primary_outcome == AssessmentOutcome.PROHIBITED
    assert result.hits[0].rule_id == "prohibited_real_time_remote_biometric_identification"


@pytest.mark.asyncio
async def test_rule_pack_evaluation_returns_transparency_hit() -> None:
    service = RulePackService()
    facts = {
        "system": {"modalities": ["chatbot"]},
        "deployment": {"interacts_with_natural_persons": True},
    }

    result = await service.evaluate("eu-ai-act-baseline", facts)

    assert result.primary_outcome == AssessmentOutcome.TRANSPARENCY_ONLY
    assert result.hits[0].rule_id == "transparency_chatbot_interaction"
