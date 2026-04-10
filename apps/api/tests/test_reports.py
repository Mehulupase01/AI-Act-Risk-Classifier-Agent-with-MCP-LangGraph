import base64
import json
from io import BytesIO
from zipfile import ZipFile

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


def test_report_export_returns_markdown_with_review_context(client: TestClient) -> None:
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
    workflow = client.post(
        f"/api/v1/cases/{case_id}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    client.post(
        f"/api/v1/cases/{case_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "workflow_run_id": workflow["id"],
            "assessment_run_id": workflow["assessment_run_id"],
            "decision": "approved",
            "rationale": "Reviewed and approved for controlled use with oversight retained.",
            "approved_outcome": "high_risk",
        },
    )

    response = client.post(
        f"/api/v1/cases/{case_id}/reports/export",
        headers={"Authorization": f"Bearer {token}"},
        json={"format": "markdown"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"].endswith(".md")
    assert payload["media_type"] == "text/markdown"
    assert "# Hiring Assistant Assessment Report" in payload["content"]
    assert "Latest Review" in payload["content"]
    assert "high_risk" in payload["content"]


def test_report_export_returns_structured_json(client: TestClient) -> None:
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
    client.post(
        f"/api/v1/cases/{case_id}/assessments",
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.post(
        f"/api/v1/cases/{case_id}/reports/export",
        headers={"Authorization": f"Bearer {token}"},
        json={"format": "json"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"].endswith(".json")
    assert payload["media_type"] == "application/json"
    content = json.loads(payload["content"])
    assert content["case"]["id"] == case_id
    assert content["latest_assessment"]["primary_outcome"] == "high_risk"
    assert content["review_history"] == []


def test_audit_pack_export_returns_zip_bundle_with_manifest(client: TestClient) -> None:
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
    workflow = client.post(
        f"/api/v1/cases/{case_id}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    client.post(
        f"/api/v1/cases/{case_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "workflow_run_id": workflow["id"],
            "assessment_run_id": workflow["assessment_run_id"],
            "decision": "approved",
            "rationale": "Approved after governance review with human oversight retained.",
            "approved_outcome": "high_risk",
        },
    )
    client.post(
        f"/api/v1/cases/{case_id}/reassessments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "reason": "manual_request",
            "title": "Annual governance refresh",
            "detail": "Requested for the yearly oversight cycle.",
            "auto_process": False,
        },
    )

    response = client.post(
        f"/api/v1/cases/{case_id}/reports/audit-pack",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"].endswith(".zip")
    assert payload["media_type"] == "application/zip"
    assert payload["manifest"]["case_id"] == case_id
    assert payload["manifest"]["reassessment_count"] == 1

    archive_bytes = base64.b64decode(payload["content_base64"])
    with ZipFile(BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "reports/assessment-report.json" in names
        assert "reports/assessment-report.md" in names
        assert "workspace/case-workspace.json" in names
        assert "workflow/reassessments.json" in names

        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["case_id"] == case_id
        assert manifest["artifact_count"] == 1
