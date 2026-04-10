from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from sqlalchemy import select

from eu_comply_api.config import get_settings
from eu_comply_api.db.models import OrganizationRecord
from eu_comply_api.db.session import get_session_factory, reset_session_state
from eu_comply_api.domain.models import ActorRole, CaseCreateRequest, SystemDossierInput
from eu_comply_api.main import create_app
from eu_comply_api.services.case_service import CaseService


@pytest.fixture()
def mcp_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "eu_comply_mcp_test.db"
    monkeypatch.setenv("EU_COMPLY_DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("EU_COMPLY_AUTO_CREATE_SCHEMA", "true")
    monkeypatch.setenv("EU_COMPLY_OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("EU_COMPLY_BOOTSTRAP_ADMIN_PASSWORD", "change-me-now")
    monkeypatch.setenv("EU_COMPLY_BOOTSTRAP_API_CLIENT_SECRET", "eu-comply-dev-secret")
    monkeypatch.setenv("EU_COMPLY_ARTIFACT_STORAGE_PATH", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    reset_session_state()
    app = create_app()
    yield app
    get_settings.cache_clear()
    reset_session_state()


@asynccontextmanager
async def _running_app(app) -> AsyncIterator[object]:
    async with app.router.lifespan_context(app):
        yield app


@asynccontextmanager
async def _mcp_session(app, path: str) -> AsyncIterator[ClientSession]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://127.0.0.1:8000",
    ) as http_client:
        async with streamable_http_client(
            f"http://127.0.0.1:8000{path}",
            http_client=http_client,
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


async def _create_case() -> str:
    settings = get_settings()
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        organization_id = await session.scalar(
            select(OrganizationRecord.id).where(
                OrganizationRecord.slug == settings.bootstrap_default_org_slug
            )
        )
        if organization_id is None:
            raise AssertionError("Default organization was not bootstrapped.")
        case = await CaseService(session).create_case(
            organization_id,
            CaseCreateRequest(
                title="Hiring Assistant",
                description="Employment support tool",
                owner_team="AI Governance",
                policy_snapshot_slug="eu-ai-act-baseline-2026-04-10",
                dossier=SystemDossierInput(
                    system_name="Hiring Assistant",
                    actor_role=ActorRole.PROVIDER,
                    sector="employment",
                    intended_purpose="Assist recruiters with candidate screening decisions.",
                    model_provider="OpenRouter",
                    model_name="openai/gpt-4o-mini",
                    uses_generative_ai=True,
                    affects_natural_persons=True,
                    geographic_scope=["EU"],
                    deployment_channels=["internal_web_app"],
                    human_oversight_summary="Recruiters review each recommendation.",
                ),
            ),
        )
    return str(case.id)


def _unwrap_structured_content(payload):
    if isinstance(payload, dict) and set(payload.keys()) == {"result"}:
        return payload["result"]
    return payload


def _tool_payload(result):
    if getattr(result, "isError", False):
        text_blocks = [item.text for item in result.content if hasattr(item, "text")]
        detail = text_blocks[0] if text_blocks else "Unknown MCP tool error"
        raise AssertionError(detail)
    if result.structuredContent is not None:
        return _unwrap_structured_content(result.structuredContent)
    text_blocks = [item.text for item in result.content if hasattr(item, "text")]
    if not text_blocks:
        return None
    return json.loads(text_blocks[0])


@pytest.mark.anyio
async def test_policy_mcp_lists_snapshots_and_reads_resources(mcp_app) -> None:
    async with _running_app(mcp_app):
        async with _mcp_session(mcp_app, "/mcp/policy/") as session:
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} >= {
                "list_policy_snapshots",
                "get_policy_snapshot",
                "search_policy_fragments",
            }

            result = await session.call_tool("list_policy_snapshots", {})
            snapshots = _tool_payload(result)
            assert snapshots
            assert snapshots[0]["slug"] == "eu-ai-act-baseline-2026-04-10"

            resources = await session.list_resources()
            assert any(
                str(resource.uri) == "policy://snapshots"
                for resource in resources.resources
            )

            read_result = await session.read_resource("policy://snapshots")
            payload = json.loads(read_result.contents[0].text)
            assert payload[0]["slug"] == "eu-ai-act-baseline-2026-04-10"

            template_listing = await session.list_resource_templates()
            assert any(
                template.uriTemplate == "policy://snapshots/{snapshot_slug}"
                for template in template_listing.resourceTemplates
            )


@pytest.mark.anyio
async def test_dossier_mcp_returns_case_workspace(mcp_app) -> None:
    async with _running_app(mcp_app):
        case_id = await _create_case()

        async with _mcp_session(mcp_app, "/mcp/dossiers/") as session:
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} >= {
                "list_cases",
                "get_case",
                "list_case_artifacts",
                "get_case_workspace",
            }

            workspace_result = await session.call_tool("get_case_workspace", {"case_id": case_id})
            workspace = _tool_payload(workspace_result)
            assert workspace["case"]["id"] == case_id
            assert workspace["reviews"] == []

            read_result = await session.read_resource(f"case://{case_id}")
            payload = json.loads(read_result.contents[0].text)
            assert payload["id"] == case_id
            assert payload["dossier"]["system_name"] == "Hiring Assistant"


@pytest.mark.anyio
async def test_assessment_mcp_runs_assessment_and_exports_report(mcp_app) -> None:
    async with _running_app(mcp_app):
        case_id = await _create_case()

        async with _mcp_session(mcp_app, "/mcp/assessments/") as session:
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} >= {
                "list_assessments",
                "run_assessment",
                "list_workflows",
                "run_workflow",
                "list_case_reviews",
                "list_case_reassessments",
                "trigger_case_reassessment",
                "export_case_report",
            }

            assessment_result = await session.call_tool("run_assessment", {"case_id": case_id})
            assessment = _tool_payload(assessment_result)
            assert assessment["case_id"] == case_id
            assert assessment["status"] in {"completed", "needs_review"}

            report_result = await session.call_tool(
                "export_case_report",
                {"case_id": case_id, "format": "json"},
            )
            report = _tool_payload(report_result)
            assert report["filename"].endswith(".json")

            reassessment_result = await session.call_tool(
                "trigger_case_reassessment",
                {
                    "case_id": case_id,
                    "reason": "manual_request",
                    "title": "MCP reassessment",
                    "detail": "Triggered from the assessment MCP surface.",
                    "auto_process": False,
                },
            )
            reassessment = _tool_payload(reassessment_result)
            assert reassessment["case_id"] == case_id
            assert reassessment["status"] == "pending"

            reassessment_list = await session.call_tool(
                "list_case_reassessments",
                {"case_id": case_id},
            )
            triggers = _tool_payload(reassessment_list)
            assert len(triggers) == 1

            latest_assessment = await session.read_resource(f"assessment://{case_id}/latest")
            payload = json.loads(latest_assessment.contents[0].text)
            assert payload["case_id"] == case_id

            latest_reassessment = await session.read_resource(f"reassessment://{case_id}/latest")
            reassessment_payload = json.loads(latest_reassessment.contents[0].text)
            assert reassessment_payload["title"] == "MCP reassessment"
