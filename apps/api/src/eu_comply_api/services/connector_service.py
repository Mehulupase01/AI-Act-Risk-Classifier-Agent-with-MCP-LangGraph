from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.db.base import utc_now
from eu_comply_api.db.models import ConnectorRecord, ConnectorSyncRunRecord
from eu_comply_api.domain.models import (
    ConnectorConfigCreateRequest,
    ConnectorConfigDetail,
    ConnectorConfigSummary,
    ConnectorConfigUpdateRequest,
    ConnectorEventInput,
    ConnectorKind,
    ConnectorStatus,
    ConnectorSyncDetail,
    ConnectorSyncRequest,
    ConnectorSyncResponse,
    ConnectorSyncStatus,
    ReassessmentReason,
    ReassessmentSource,
)
from eu_comply_api.services.reassessment_service import ReassessmentService

CONNECTOR_REASON_SUPPORT: dict[ConnectorKind, tuple[ReassessmentReason, ...]] = {
    ConnectorKind.MODEL_REGISTRY: (
        ReassessmentReason.MODEL_CHANGED,
        ReassessmentReason.DEPLOYMENT_CHANGED,
    ),
    ConnectorKind.DOCUMENT_REPOSITORY: (ReassessmentReason.EVIDENCE_UPDATED,),
    ConnectorKind.GRC_TICKETING: (
        ReassessmentReason.POLICY_UPDATED,
        ReassessmentReason.INCIDENT_REPORTED,
        ReassessmentReason.MANUAL_REQUEST,
    ),
    ConnectorKind.WEBHOOK: tuple(reason for reason in ReassessmentReason),
}


@dataclass(slots=True)
class NormalizedConnectorEvent:
    case_id: UUID
    reason: ReassessmentReason
    title: str
    detail: str | None
    payload: dict[str, object]
    external_reference: str | None


class ConnectorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_connectors(self, organization_id: UUID) -> list[ConnectorConfigSummary]:
        connectors = list(
            (
                await self._session.scalars(
                    select(ConnectorRecord)
                    .where(ConnectorRecord.organization_id == organization_id)
                    .order_by(ConnectorRecord.created_at.desc())
                )
            ).all()
        )
        return [self._to_summary(connector) for connector in connectors]

    async def create_connector(
        self,
        organization_id: UUID,
        payload: ConnectorConfigCreateRequest,
    ) -> ConnectorConfigDetail:
        existing = await self._session.scalar(
            select(ConnectorRecord).where(
                ConnectorRecord.organization_id == organization_id,
                ConnectorRecord.slug == payload.slug,
            )
        )
        if existing is not None:
            raise ValueError(
                f"Connector slug '{payload.slug}' is already registered in this organization."
            )

        connector = ConnectorRecord(
            organization_id=organization_id,
            slug=payload.slug,
            name=payload.name,
            kind=payload.kind.value,
            status=payload.status.value,
            description=payload.description,
            config_json=payload.config,
        )
        self._session.add(connector)
        await self._session.commit()
        return self._to_detail(connector)

    async def get_connector(
        self,
        organization_id: UUID,
        connector_id: UUID,
    ) -> ConnectorConfigDetail:
        connector = await self._get_connector(organization_id, connector_id)
        return self._to_detail(connector)

    async def update_connector(
        self,
        organization_id: UUID,
        connector_id: UUID,
        payload: ConnectorConfigUpdateRequest,
    ) -> ConnectorConfigDetail:
        connector = await self._get_connector(organization_id, connector_id)
        if payload.name is not None:
            connector.name = payload.name
        if payload.description is not None:
            connector.description = payload.description
        if payload.status is not None:
            connector.status = payload.status.value
        if payload.config is not None:
            connector.config_json = payload.config
        await self._session.commit()
        return self._to_detail(connector)

    async def list_sync_runs(
        self,
        organization_id: UUID,
        connector_id: UUID,
    ) -> list[ConnectorSyncDetail]:
        await self._get_connector(organization_id, connector_id)
        runs = list(
            (
                await self._session.scalars(
                    select(ConnectorSyncRunRecord)
                    .where(
                        ConnectorSyncRunRecord.organization_id == organization_id,
                        ConnectorSyncRunRecord.connector_id == connector_id,
                    )
                    .order_by(ConnectorSyncRunRecord.created_at.desc())
                )
            ).all()
        )
        return [self._to_sync_detail(run) for run in runs]

    async def run_sync(
        self,
        organization_id: UUID,
        connector_id: UUID,
        payload: ConnectorSyncRequest,
        initiated_by: str,
    ) -> ConnectorSyncResponse:
        connector = await self._get_connector(organization_id, connector_id)
        normalized_events, unmapped_events = self._normalize_events(
            ConnectorKind(connector.kind),
            payload,
        )

        sync_run = ConnectorSyncRunRecord(
            organization_id=organization_id,
            connector_id=connector.id,
            case_id=payload.case_id,
            initiated_by=initiated_by,
            status=ConnectorSyncStatus.COMPLETED.value,
            event_count=len(payload.events),
            trigger_count=0,
            processed_trigger_count=0,
            unmapped_event_count=len(unmapped_events),
            request_payload_json=payload.model_dump(mode="json"),
            result_json={},
            completed_at=None,
        )
        self._session.add(sync_run)
        await self._session.flush()

        reassessment_service = ReassessmentService(self._session)
        trigger_records = []
        mapped_events: list[dict[str, object]] = []
        try:
            for event in normalized_events:
                trigger = await reassessment_service.register_connector_trigger(
                    organization_id=organization_id,
                    case_id=event.case_id,
                    reason=event.reason,
                    title=event.title,
                    detail=event.detail,
                    payload={
                        **event.payload,
                        "external_reference": event.external_reference,
                        "connector_slug": connector.slug,
                    },
                    requested_by=initiated_by,
                    source=ReassessmentSource.CONNECTOR_SYNC,
                    auto_process=payload.auto_process_triggers,
                    connector_id=connector.id,
                    sync_run_id=sync_run.id,
                    commit=False,
                )
                trigger_records.append(trigger)
                mapped_events.append(
                    {
                        "case_id": str(event.case_id),
                        "reason": event.reason.value,
                        "title": event.title,
                    }
                )

            processed_count = sum(
                1 for trigger in trigger_records if trigger.workflow_run_id is not None
            )
            sync_run.trigger_count = len(trigger_records)
            sync_run.processed_trigger_count = processed_count
            sync_run.completed_at = utc_now()
            sync_run.result_json = {
                "connector_slug": connector.slug,
                "mapped_events": mapped_events,
                "unmapped_events": unmapped_events,
                "auto_process_triggers": payload.auto_process_triggers,
            }
            await self._session.commit()
        except Exception as exc:
            sync_run.status = ConnectorSyncStatus.FAILED.value
            sync_run.completed_at = utc_now()
            sync_run.result_json = {
                "error": str(exc),
                "unmapped_events": unmapped_events,
            }
            await self._session.commit()
            raise

        return ConnectorSyncResponse(
            sync_run=self._to_sync_detail(sync_run),
            triggers=[
                reassessment_service._to_summary(trigger)
                for trigger in trigger_records
            ],
        )

    async def _get_connector(
        self,
        organization_id: UUID,
        connector_id: UUID,
    ) -> ConnectorRecord:
        connector = await self._session.scalar(
            select(ConnectorRecord).where(
                ConnectorRecord.organization_id == organization_id,
                ConnectorRecord.id == connector_id,
            )
        )
        if connector is None:
            raise LookupError(f"Connector '{connector_id}' was not found.")
        return connector

    def _normalize_events(
        self,
        kind: ConnectorKind,
        payload: ConnectorSyncRequest,
    ) -> tuple[list[NormalizedConnectorEvent], list[dict[str, object]]]:
        supported_reasons = set(CONNECTOR_REASON_SUPPORT[kind])
        normalized: list[NormalizedConnectorEvent] = []
        unmapped: list[dict[str, object]] = []
        for event in payload.events:
            if event.reason not in supported_reasons:
                raise ValueError(
                    f"Connector kind '{kind.value}' does not support "
                    f"reassessment reason '{event.reason.value}'."
                )
            resolved_case_id = event.case_id or payload.case_id
            if resolved_case_id is None:
                unmapped.append(self._serialize_event(event))
                continue
            normalized.append(
                NormalizedConnectorEvent(
                    case_id=resolved_case_id,
                    reason=event.reason,
                    title=event.title,
                    detail=event.detail,
                    payload=event.payload,
                    external_reference=event.external_reference,
                )
            )
        return normalized, unmapped

    def _serialize_event(self, event: ConnectorEventInput) -> dict[str, object]:
        payload = event.model_dump(mode="json")
        if payload.get("case_id") is not None:
            payload["case_id"] = str(payload["case_id"])
        return payload

    def _to_summary(self, connector: ConnectorRecord) -> ConnectorConfigSummary:
        return ConnectorConfigSummary(
            id=connector.id,
            name=connector.name,
            slug=connector.slug,
            kind=ConnectorKind(connector.kind),
            status=ConnectorStatus(connector.status),
            description=connector.description,
            created_at=connector.created_at,
            updated_at=connector.updated_at,
        )

    def _to_detail(self, connector: ConnectorRecord) -> ConnectorConfigDetail:
        return ConnectorConfigDetail(
            **self._to_summary(connector).model_dump(),
            config=connector.config_json,
            supported_reasons=list(CONNECTOR_REASON_SUPPORT[ConnectorKind(connector.kind)]),
        )

    def _to_sync_detail(self, run: ConnectorSyncRunRecord) -> ConnectorSyncDetail:
        return ConnectorSyncDetail(
            id=run.id,
            connector_id=run.connector_id,
            case_id=run.case_id,
            status=ConnectorSyncStatus(run.status),
            initiated_by=run.initiated_by,
            event_count=run.event_count,
            trigger_count=run.trigger_count,
            processed_trigger_count=run.processed_trigger_count,
            unmapped_event_count=run.unmapped_event_count,
            created_at=run.created_at,
            completed_at=run.completed_at,
            request_payload=run.request_payload_json,
            result=run.result_json,
        )
