from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.db.base import utc_now
from eu_comply_api.db.models import CaseRecord, ReassessmentTriggerRecord
from eu_comply_api.domain.models import (
    ReassessmentReason,
    ReassessmentSource,
    ReassessmentStatus,
    ReassessmentTriggerCreateRequest,
    ReassessmentTriggerDetail,
    ReassessmentTriggerSummary,
)
from eu_comply_api.services.workflow_service import WorkflowService


class ReassessmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_triggers(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[ReassessmentTriggerSummary]:
        await self._get_case(organization_id, case_id)
        triggers = list(
            (
                await self._session.scalars(
                    select(ReassessmentTriggerRecord)
                    .where(ReassessmentTriggerRecord.case_id == case_id)
                    .order_by(ReassessmentTriggerRecord.created_at.desc())
                )
            ).all()
        )
        return [self._to_summary(trigger) for trigger in triggers]

    async def create_manual_trigger(
        self,
        organization_id: UUID,
        case_id: UUID,
        payload: ReassessmentTriggerCreateRequest,
        requested_by: str,
    ) -> ReassessmentTriggerDetail:
        await self._get_case(organization_id, case_id)
        trigger = await self.register_connector_trigger(
            organization_id=organization_id,
            case_id=case_id,
            reason=payload.reason,
            title=payload.title,
            detail=payload.detail,
            payload=payload.payload,
            requested_by=requested_by,
            source=ReassessmentSource.MANUAL,
            auto_process=payload.auto_process,
            commit=False,
        )
        await self._session.commit()
        return self._to_detail(trigger)

    async def register_connector_trigger(
        self,
        organization_id: UUID,
        case_id: UUID,
        reason: ReassessmentReason,
        title: str,
        detail: str | None,
        payload: dict[str, object],
        requested_by: str,
        source: ReassessmentSource,
        auto_process: bool,
        connector_id: UUID | None = None,
        sync_run_id: UUID | None = None,
        commit: bool = False,
    ) -> ReassessmentTriggerRecord:
        await self._get_case(organization_id, case_id)
        trigger = ReassessmentTriggerRecord(
            case_id=case_id,
            connector_id=connector_id,
            sync_run_id=sync_run_id,
            workflow_run_id=None,
            reason=reason.value,
            source=source.value,
            status=ReassessmentStatus.PENDING.value,
            title=title,
            detail=detail,
            requested_by=requested_by,
            payload_json=payload,
            processed_at=None,
        )
        self._session.add(trigger)
        await self._session.flush()

        if auto_process:
            await self._process_trigger(organization_id, trigger)

        if commit:
            await self._session.commit()
        return trigger

    async def _process_trigger(
        self,
        organization_id: UUID,
        trigger: ReassessmentTriggerRecord,
    ) -> None:
        try:
            workflow = await WorkflowService(self._session).run_governed_assessment(
                organization_id,
                trigger.case_id,
            )
        except Exception:
            trigger.status = ReassessmentStatus.FAILED.value
            trigger.processed_at = utc_now()
            raise

        trigger.workflow_run_id = workflow.id
        trigger.status = ReassessmentStatus.PROCESSED.value
        trigger.processed_at = utc_now()

    async def _get_case(self, organization_id: UUID, case_id: UUID) -> CaseRecord:
        case = await self._session.scalar(
            select(CaseRecord).where(
                CaseRecord.organization_id == organization_id,
                CaseRecord.id == case_id,
            )
        )
        if case is None:
            raise LookupError(f"Case '{case_id}' was not found.")
        return case

    def _to_summary(self, trigger: ReassessmentTriggerRecord) -> ReassessmentTriggerSummary:
        return ReassessmentTriggerSummary(
            id=trigger.id,
            case_id=trigger.case_id,
            connector_id=trigger.connector_id,
            sync_run_id=trigger.sync_run_id,
            workflow_run_id=trigger.workflow_run_id,
            reason=ReassessmentReason(trigger.reason),
            source=ReassessmentSource(trigger.source),
            status=ReassessmentStatus(trigger.status),
            title=trigger.title,
            detail=trigger.detail,
            requested_by=trigger.requested_by,
            created_at=trigger.created_at,
            processed_at=trigger.processed_at,
        )

    def _to_detail(self, trigger: ReassessmentTriggerRecord) -> ReassessmentTriggerDetail:
        return ReassessmentTriggerDetail(
            **self._to_summary(trigger).model_dump(),
            payload=trigger.payload_json,
        )
