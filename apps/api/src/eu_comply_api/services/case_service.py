from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eu_comply_api.db.models import CaseRecord, SystemDossierRecord
from eu_comply_api.domain.models import (
    ActorRole,
    CaseCreateRequest,
    CaseDetail,
    CaseStatus,
    CaseSummary,
    CaseUpdateRequest,
    SystemDossierResponse,
)


class CaseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_cases(self, organization_id: UUID) -> list[CaseSummary]:
        cases = list(
            (
                await self._session.scalars(
                    select(CaseRecord)
                    .options(selectinload(CaseRecord.dossier))
                    .where(CaseRecord.organization_id == organization_id)
                    .order_by(CaseRecord.updated_at.desc())
                )
            ).all()
        )
        return [self._to_case_summary(case) for case in cases if case.dossier is not None]

    async def create_case(self, organization_id: UUID, payload: CaseCreateRequest) -> CaseDetail:
        case = CaseRecord(
            organization_id=organization_id,
            title=payload.title,
            description=payload.description,
            status=CaseStatus.DRAFT.value,
            owner_team=payload.owner_team,
            policy_snapshot_slug=payload.policy_snapshot_slug,
        )
        self._session.add(case)
        await self._session.flush()

        dossier = SystemDossierRecord(
            case_id=case.id,
            system_name=payload.dossier.system_name,
            actor_role=payload.dossier.actor_role.value,
            sector=payload.dossier.sector,
            intended_purpose=payload.dossier.intended_purpose,
            model_provider=payload.dossier.model_provider,
            model_name=payload.dossier.model_name,
            uses_generative_ai=payload.dossier.uses_generative_ai,
            affects_natural_persons=payload.dossier.affects_natural_persons,
            geographic_scope=payload.dossier.geographic_scope,
            deployment_channels=payload.dossier.deployment_channels,
            human_oversight_summary=payload.dossier.human_oversight_summary,
        )
        self._session.add(dossier)
        await self._session.commit()

        return await self.get_case(organization_id, case.id)

    async def get_case(self, organization_id: UUID, case_id: UUID) -> CaseDetail:
        case = await self._session.scalar(
            select(CaseRecord)
            .options(selectinload(CaseRecord.dossier))
            .where(
                CaseRecord.organization_id == organization_id,
                CaseRecord.id == case_id,
            )
        )
        if case is None or case.dossier is None:
            raise ValueError(f"Case '{case_id}' was not found.")
        return self._to_case_detail(case)

    async def update_case(
        self,
        organization_id: UUID,
        case_id: UUID,
        payload: CaseUpdateRequest,
    ) -> CaseDetail:
        case = await self._session.scalar(
            select(CaseRecord)
            .options(selectinload(CaseRecord.dossier))
            .where(
                CaseRecord.organization_id == organization_id,
                CaseRecord.id == case_id,
            )
        )
        if case is None or case.dossier is None:
            raise ValueError(f"Case '{case_id}' was not found.")

        if payload.title is not None:
            case.title = payload.title
        if payload.description is not None:
            case.description = payload.description
        if payload.owner_team is not None:
            case.owner_team = payload.owner_team
        if payload.status is not None:
            case.status = payload.status.value
        if payload.policy_snapshot_slug is not None:
            case.policy_snapshot_slug = payload.policy_snapshot_slug
        if payload.dossier is not None:
            case.dossier.system_name = payload.dossier.system_name
            case.dossier.actor_role = payload.dossier.actor_role.value
            case.dossier.sector = payload.dossier.sector
            case.dossier.intended_purpose = payload.dossier.intended_purpose
            case.dossier.model_provider = payload.dossier.model_provider
            case.dossier.model_name = payload.dossier.model_name
            case.dossier.uses_generative_ai = payload.dossier.uses_generative_ai
            case.dossier.affects_natural_persons = payload.dossier.affects_natural_persons
            case.dossier.geographic_scope = payload.dossier.geographic_scope
            case.dossier.deployment_channels = payload.dossier.deployment_channels
            case.dossier.human_oversight_summary = payload.dossier.human_oversight_summary

        await self._session.commit()
        return self._to_case_detail(case)

    def _to_case_summary(self, case: CaseRecord) -> CaseSummary:
        dossier = case.dossier
        if dossier is None:
            raise ValueError(f"Case '{case.id}' is missing its dossier.")
        return CaseSummary(
            id=case.id,
            title=case.title,
            status=CaseStatus(case.status),
            owner_team=case.owner_team,
            policy_snapshot_slug=case.policy_snapshot_slug,
            system_name=dossier.system_name,
            actor_role=ActorRole(dossier.actor_role),
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def _to_case_detail(self, case: CaseRecord) -> CaseDetail:
        dossier = case.dossier
        if dossier is None:
            raise ValueError(f"Case '{case.id}' is missing its dossier.")
        return CaseDetail(
            **self._to_case_summary(case).model_dump(),
            description=case.description,
            dossier=SystemDossierResponse(
                id=dossier.id,
                case_id=dossier.case_id,
                system_name=dossier.system_name,
                actor_role=ActorRole(dossier.actor_role),
                sector=dossier.sector,
                intended_purpose=dossier.intended_purpose,
                model_provider=dossier.model_provider,
                model_name=dossier.model_name,
                uses_generative_ai=dossier.uses_generative_ai,
                affects_natural_persons=dossier.affects_natural_persons,
                geographic_scope=dossier.geographic_scope,
                deployment_channels=dossier.deployment_channels,
                human_oversight_summary=dossier.human_oversight_summary,
                created_at=dossier.created_at,
                updated_at=dossier.updated_at,
            ),
        )
