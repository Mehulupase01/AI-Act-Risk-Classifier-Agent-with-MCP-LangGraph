from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.config import Settings
from eu_comply_api.db.models import (
    ArtifactRecord,
    AssessmentRunRecord,
    CaseRecord,
    ConnectorRecord,
    ConnectorSyncRunRecord,
    OrganizationRecord,
    PolicySnapshotRecord,
    ReassessmentTriggerRecord,
    ReviewDecisionRecord,
    WorkflowRunRecord,
)
from eu_comply_api.domain.models import (
    HealthStatus,
    ReadinessCheck,
    ReadinessResponse,
)


class MonitoringService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def readiness(self) -> ReadinessResponse:
        checks = [
            ReadinessCheck(
                name="configuration",
                status=HealthStatus.OK,
                detail=(
                    "Runtime defaults: "
                    f"chat={self._settings.llm_default_provider}, "
                    f"embeddings={self._settings.embedding_default_provider}"
                ),
            )
        ]

        checks.append(await self._database_check())
        checks.append(await self._bootstrap_org_check())
        checks.append(await self._policy_snapshot_check())
        checks.append(self._artifact_storage_check())

        if all(check.status == HealthStatus.OK for check in checks):
            overall = HealthStatus.OK
        elif any(check.status == HealthStatus.ERROR for check in checks):
            overall = HealthStatus.ERROR
        else:
            overall = HealthStatus.DEGRADED
        return ReadinessResponse(status=overall, checks=checks)

    async def render_metrics(self, organization_id: UUID) -> str:
        metrics = {
            "eu_comply_cases_total": await self._count(
                select(func.count()).select_from(CaseRecord).where(
                    CaseRecord.organization_id == organization_id
                )
            ),
            "eu_comply_artifacts_total": await self._count(
                select(func.count())
                .select_from(ArtifactRecord)
                .join(CaseRecord, ArtifactRecord.case_id == CaseRecord.id)
                .where(CaseRecord.organization_id == organization_id)
            ),
            "eu_comply_assessment_runs_total": await self._count(
                select(func.count())
                .select_from(AssessmentRunRecord)
                .join(CaseRecord, AssessmentRunRecord.case_id == CaseRecord.id)
                .where(CaseRecord.organization_id == organization_id)
            ),
            "eu_comply_workflow_runs_total": await self._count(
                select(func.count())
                .select_from(WorkflowRunRecord)
                .join(CaseRecord, WorkflowRunRecord.case_id == CaseRecord.id)
                .where(CaseRecord.organization_id == organization_id)
            ),
            "eu_comply_workflows_pending_review_total": await self._count(
                select(func.count())
                .select_from(WorkflowRunRecord)
                .join(CaseRecord, WorkflowRunRecord.case_id == CaseRecord.id)
                .where(
                    CaseRecord.organization_id == organization_id,
                    WorkflowRunRecord.review_required.is_(True),
                )
            ),
            "eu_comply_review_decisions_total": await self._count(
                select(func.count())
                .select_from(ReviewDecisionRecord)
                .join(CaseRecord, ReviewDecisionRecord.case_id == CaseRecord.id)
                .where(CaseRecord.organization_id == organization_id)
            ),
            "eu_comply_connectors_total": await self._count(
                select(func.count()).select_from(ConnectorRecord).where(
                    ConnectorRecord.organization_id == organization_id
                )
            ),
            "eu_comply_connector_sync_runs_total": await self._count(
                select(func.count()).select_from(ConnectorSyncRunRecord).where(
                    ConnectorSyncRunRecord.organization_id == organization_id
                )
            ),
            "eu_comply_connector_sync_failures_total": await self._count(
                select(func.count()).select_from(ConnectorSyncRunRecord).where(
                    ConnectorSyncRunRecord.organization_id == organization_id,
                    ConnectorSyncRunRecord.status == "failed",
                )
            ),
            "eu_comply_reassessment_triggers_total": await self._count(
                select(func.count())
                .select_from(ReassessmentTriggerRecord)
                .join(CaseRecord, ReassessmentTriggerRecord.case_id == CaseRecord.id)
                .where(CaseRecord.organization_id == organization_id)
            ),
            "eu_comply_reassessment_pending_total": await self._count(
                select(func.count())
                .select_from(ReassessmentTriggerRecord)
                .join(CaseRecord, ReassessmentTriggerRecord.case_id == CaseRecord.id)
                .where(
                    CaseRecord.organization_id == organization_id,
                    ReassessmentTriggerRecord.status == "pending",
                )
            ),
        }

        lines = [
            "# HELP eu_comply_cases_total Total cases for the current organization.",
            "# TYPE eu_comply_cases_total gauge",
        ]
        for name, value in metrics.items():
            if name != "eu_comply_cases_total":
                lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        return "\n".join(lines) + "\n"

    async def _database_check(self) -> ReadinessCheck:
        try:
            await self._session.execute(text("SELECT 1"))
        except Exception as exc:
            return ReadinessCheck(
                name="database",
                status=HealthStatus.ERROR,
                detail=str(exc),
            )
        return ReadinessCheck(
            name="database",
            status=HealthStatus.OK,
            detail="Database connectivity verified.",
        )

    async def _bootstrap_org_check(self) -> ReadinessCheck:
        organization = await self._session.scalar(
            select(OrganizationRecord).where(
                OrganizationRecord.slug == self._settings.bootstrap_default_org_slug
            )
        )
        if organization is None:
            return ReadinessCheck(
                name="bootstrap_organization",
                status=HealthStatus.ERROR,
                detail="Default bootstrap organization is missing.",
            )
        return ReadinessCheck(
            name="bootstrap_organization",
            status=HealthStatus.OK,
            detail=f"Resolved bootstrap org '{organization.slug}'.",
        )

    async def _policy_snapshot_check(self) -> ReadinessCheck:
        snapshot_count = await self._count(select(func.count()).select_from(PolicySnapshotRecord))
        if snapshot_count == 0:
            return ReadinessCheck(
                name="policy_snapshots",
                status=HealthStatus.ERROR,
                detail="No policy snapshots are loaded.",
            )
        return ReadinessCheck(
            name="policy_snapshots",
            status=HealthStatus.OK,
            detail=f"{snapshot_count} policy snapshot(s) available.",
        )

    def _artifact_storage_check(self) -> ReadinessCheck:
        path = Path(self._settings.artifact_storage_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return ReadinessCheck(
                name="artifact_storage",
                status=HealthStatus.ERROR,
                detail=str(exc),
            )
        return ReadinessCheck(
            name="artifact_storage",
            status=HealthStatus.OK,
            detail=str(path.resolve()),
        )

    async def _count(self, statement) -> int:
        return int((await self._session.scalar(statement)) or 0)
