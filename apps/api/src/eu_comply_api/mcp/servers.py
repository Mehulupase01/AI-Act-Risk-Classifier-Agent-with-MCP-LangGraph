from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from eu_comply_api.config import Settings
from eu_comply_api.db.models import OrganizationRecord
from eu_comply_api.domain.models import (
    ArtifactDetail,
    AssessmentRunDetail,
    CaseDetail,
    CaseSummary,
    CaseWorkspaceSnapshot,
    NormFragmentSummary,
    PolicySnapshotDetail,
    PolicySnapshotSummary,
    ReassessmentReason,
    ReassessmentTriggerCreateRequest,
    ReassessmentTriggerDetail,
    ReassessmentTriggerSummary,
    ReportExportRequest,
    ReportExportResponse,
    ReportFormat,
    ReviewDecisionSummary,
    WorkflowRunDetail,
)
from eu_comply_api.services.artifact_service import ArtifactService
from eu_comply_api.services.assessment_service import AssessmentService
from eu_comply_api.services.case_service import CaseService
from eu_comply_api.services.policy_service import PolicyService
from eu_comply_api.services.reassessment_service import ReassessmentService
from eu_comply_api.services.report_service import ReportService
from eu_comply_api.services.review_service import ReviewService
from eu_comply_api.services.workflow_service import WorkflowService


@dataclass(slots=True)
class MountedMCPServer:
    name: str
    mount_path: str
    server: FastMCP


@dataclass(slots=True)
class MCPRuntimeContext:
    settings: Settings
    session_factory: async_sessionmaker[AsyncSession]

    @property
    def default_org_slug(self) -> str:
        return self.settings.mcp_default_org_slug or self.settings.bootstrap_default_org_slug

    @asynccontextmanager
    async def organization_session(self) -> AsyncIterator[tuple[AsyncSession, UUID]]:
        async with self.session_factory() as session:
            organization_id = await self._resolve_organization_id(session)
            yield session, organization_id

    async def _resolve_organization_id(self, session: AsyncSession) -> UUID:
        organization = await session.scalar(
            select(OrganizationRecord).where(OrganizationRecord.slug == self.default_org_slug)
        )
        if organization is None:
            raise LookupError(
                f"MCP default organization slug '{self.default_org_slug}' could not be resolved."
            )
        return organization.id


def build_mcp_servers(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> list[MountedMCPServer]:
    if not settings.mcp_enabled:
        return []

    context = MCPRuntimeContext(settings=settings, session_factory=session_factory)
    return [
        MountedMCPServer(
            name="policy-corpus-mcp",
            mount_path="/mcp/policy",
            server=_build_policy_server(context),
        ),
        MountedMCPServer(
            name="system-dossier-mcp",
            mount_path="/mcp/dossiers",
            server=_build_dossier_server(context),
        ),
        MountedMCPServer(
            name="assessment-mcp",
            mount_path="/mcp/assessments",
            server=_build_assessment_server(context),
        ),
    ]


def _build_policy_server(context: MCPRuntimeContext) -> FastMCP:
    mcp = FastMCP(
        "EU-Comply Policy Corpus",
        instructions=(
            "Use these policy tools and resources to inspect AI Act policy snapshots, "
            "citations, and normalized legal fragments. Treat them as authoritative "
            "platform context, not as approval actions."
        ),
        json_response=True,
        streamable_http_path="/",
    )

    @mcp.tool()
    async def list_policy_snapshots() -> list[PolicySnapshotSummary]:
        async with context.organization_session() as (session, _):
            return await PolicyService(session).list_snapshots()

    @mcp.tool()
    async def get_policy_snapshot(snapshot_slug: str) -> PolicySnapshotDetail:
        async with context.organization_session() as (session, _):
            return await PolicyService(session).get_snapshot(snapshot_slug)

    @mcp.tool()
    async def search_policy_fragments(
        snapshot_slug: str,
        query: str | None = None,
        actor_scope: str | None = None,
        tag: str | None = None,
        limit: int = 10,
    ) -> list[NormFragmentSummary]:
        async with context.organization_session() as (session, _):
            detail = await PolicyService(session).get_snapshot(snapshot_slug)

        query_text = query.strip().lower() if query else None
        results: list[NormFragmentSummary] = []
        for fragment in detail.fragments:
            if actor_scope and actor_scope not in fragment.actor_scope:
                continue
            if tag and tag not in fragment.tags:
                continue
            if query_text:
                haystack = " ".join(
                    [
                        fragment.citation,
                        fragment.heading,
                        fragment.body,
                        " ".join(fragment.tags),
                        " ".join(fragment.actor_scope),
                    ]
                ).lower()
                if query_text not in haystack:
                    continue
            results.append(fragment)
            if len(results) >= limit:
                break
        return results

    @mcp.resource("policy://snapshots")
    async def policy_snapshots_resource() -> str:
        async with context.organization_session() as (session, _):
            snapshots = await PolicyService(session).list_snapshots()
        return _to_json_text(snapshots)

    @mcp.resource("policy://snapshots/{snapshot_slug}")
    async def policy_snapshot_resource(snapshot_slug: str) -> str:
        async with context.organization_session() as (session, _):
            snapshot = await PolicyService(session).get_snapshot(snapshot_slug)
        return _to_json_text(snapshot)

    @mcp.prompt()
    def review_policy_snapshot(snapshot_slug: str, case_context: str) -> str:
        return (
            "Review the EU-Comply policy snapshot for the referenced case context.\n"
            f"Snapshot slug: {snapshot_slug}\n"
            f"Case context: {case_context}\n"
            "Identify the most relevant citations, actor obligations, and any uncertainty "
            "that should be escalated to a human reviewer."
        )

    return mcp


def _build_dossier_server(context: MCPRuntimeContext) -> FastMCP:
    mcp = FastMCP(
        "EU-Comply System Dossiers",
        instructions=(
            "Use these tools and resources to inspect org-scoped cases, dossiers, "
            "artifacts, and review history. Do not invent missing facts."
        ),
        json_response=True,
        streamable_http_path="/",
    )

    @mcp.tool()
    async def list_cases() -> list[CaseSummary]:
        async with context.organization_session() as (session, organization_id):
            return await CaseService(session).list_cases(organization_id)

    @mcp.tool()
    async def get_case(case_id: str) -> CaseDetail:
        async with context.organization_session() as (session, organization_id):
            return await CaseService(session).get_case(organization_id, UUID(case_id))

    @mcp.tool()
    async def list_case_artifacts(case_id: str) -> list[ArtifactDetail]:
        async with context.organization_session() as (session, organization_id):
            artifact_service = ArtifactService(session, context.settings)
            summaries = await artifact_service.list_artifacts(
                organization_id,
                UUID(case_id),
            )
            return [
                await artifact_service.get_artifact(organization_id, UUID(case_id), artifact.id)
                for artifact in summaries
            ]

    @mcp.tool()
    async def get_case_workspace(case_id: str) -> CaseWorkspaceSnapshot:
        case_uuid = UUID(case_id)
        async with context.organization_session() as (session, organization_id):
            case = await CaseService(session).get_case(organization_id, case_uuid)
            artifact_service = ArtifactService(session, context.settings)
            artifact_summaries = await artifact_service.list_artifacts(organization_id, case_uuid)
            artifacts = [
                await artifact_service.get_artifact(organization_id, case_uuid, artifact.id)
                for artifact in artifact_summaries
            ]
            assessments = await AssessmentService(session).list_assessments(
                organization_id,
                case_uuid,
            )
            workflows = await WorkflowService(session).list_workflows(organization_id, case_uuid)
            reviews = await ReviewService(session).list_reviews(organization_id, case_uuid)
        return CaseWorkspaceSnapshot(
            case=case,
            artifacts=artifacts,
            assessments=assessments,
            workflows=workflows,
            reviews=reviews,
        )

    @mcp.resource("case://{case_id}")
    async def case_resource(case_id: str) -> str:
        async with context.organization_session() as (session, organization_id):
            case = await CaseService(session).get_case(organization_id, UUID(case_id))
        return _to_json_text(case)

    @mcp.resource("case://{case_id}/workspace")
    async def case_workspace_resource(case_id: str) -> str:
        workspace = await get_case_workspace(case_id)
        return _to_json_text(workspace)

    @mcp.prompt()
    def summarize_case_for_review(case_id: str) -> str:
        return (
            "Summarize the referenced EU-Comply case for a governance reviewer. "
            f"Case ID: {case_id}. Use stored dossier facts, artifacts, reviews, and "
            "workflow state. Call out missing evidence explicitly."
        )

    return mcp


def _build_assessment_server(context: MCPRuntimeContext) -> FastMCP:
    mcp = FastMCP(
        "EU-Comply Assessments",
        instructions=(
            "Use these tools to inspect or execute deterministic assessments and governed "
            "workflows. Review approvals remain outside the MCP write surface."
        ),
        json_response=True,
        streamable_http_path="/",
    )

    @mcp.tool()
    async def list_assessments(case_id: str) -> list[AssessmentRunDetail]:
        async with context.organization_session() as (session, organization_id):
            return await AssessmentService(session).list_assessments(
                organization_id,
                UUID(case_id),
            )

    @mcp.tool()
    async def run_assessment(case_id: str) -> AssessmentRunDetail:
        async with context.organization_session() as (session, organization_id):
            return await AssessmentService(session).run_assessment(
                organization_id,
                UUID(case_id),
            )

    @mcp.tool()
    async def list_workflows(case_id: str) -> list[WorkflowRunDetail]:
        async with context.organization_session() as (session, organization_id):
            return await WorkflowService(session).list_workflows(organization_id, UUID(case_id))

    @mcp.tool()
    async def run_workflow(case_id: str) -> WorkflowRunDetail:
        async with context.organization_session() as (session, organization_id):
            return await WorkflowService(session).run_governed_assessment(
                organization_id,
                UUID(case_id),
            )

    @mcp.tool()
    async def list_case_reviews(case_id: str) -> list[ReviewDecisionSummary]:
        async with context.organization_session() as (session, organization_id):
            return await ReviewService(session).list_reviews(organization_id, UUID(case_id))

    @mcp.tool()
    async def list_case_reassessments(case_id: str) -> list[ReassessmentTriggerSummary]:
        async with context.organization_session() as (session, organization_id):
            return await ReassessmentService(session).list_triggers(
                organization_id,
                UUID(case_id),
            )

    @mcp.tool()
    async def trigger_case_reassessment(
        case_id: str,
        reason: str = "manual_request",
        title: str = "Manual reassessment request",
        detail: str | None = None,
        auto_process: bool = True,
    ) -> ReassessmentTriggerDetail:
        async with context.organization_session() as (session, organization_id):
            return await ReassessmentService(session).create_manual_trigger(
                organization_id,
                UUID(case_id),
                ReassessmentTriggerCreateRequest(
                    reason=ReassessmentReason(reason),
                    title=title,
                    detail=detail,
                    auto_process=auto_process,
                ),
                requested_by="mcp:assessment-mcp",
            )

    @mcp.tool()
    async def export_case_report(
        case_id: str,
        format: str = "json",
    ) -> ReportExportResponse:
        async with context.organization_session() as (session, organization_id):
            return await ReportService(session).export_case_report(
                organization_id,
                UUID(case_id),
                ReportExportRequest(format=ReportFormat(format)),
            )

    @mcp.resource("assessment://{case_id}/latest")
    async def latest_assessment_resource(case_id: str) -> str:
        assessments = await list_assessments(case_id)
        return _to_json_text(assessments[0] if assessments else None)

    @mcp.resource("workflow://{case_id}/latest")
    async def latest_workflow_resource(case_id: str) -> str:
        workflows = await list_workflows(case_id)
        return _to_json_text(workflows[0] if workflows else None)

    @mcp.resource("reassessment://{case_id}/latest")
    async def latest_reassessment_resource(case_id: str) -> str:
        triggers = await list_case_reassessments(case_id)
        return _to_json_text(triggers[0] if triggers else None)

    @mcp.prompt()
    def assess_case_prompt(case_id: str) -> str:
        return (
            "Review the current deterministic assessment state for the referenced EU-Comply case. "
            f"Case ID: {case_id}. Use the latest assessment, workflow, and review history to "
            "prepare a reviewer-facing summary without inventing new evidence."
        )

    return mcp


def _to_json_text(payload: object) -> str:
    return json.dumps(jsonable_encoder(payload), indent=2)
