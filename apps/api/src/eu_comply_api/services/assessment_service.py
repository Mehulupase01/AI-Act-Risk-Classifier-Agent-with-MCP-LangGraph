from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eu_comply_api.db.models import (
    ArtifactRecord,
    AssessmentRunRecord,
    CaseRecord,
    ExtractedFactRecord,
)
from eu_comply_api.domain.models import (
    AssessmentOutcome,
    AssessmentRunDetail,
    AssessmentRunStatus,
    ExtractedFactStatus,
    ObligationItem,
    RuleHit,
)
from eu_comply_api.services.rule_pack_service import RulePackService

OBLIGATION_LIBRARY: dict[str, ObligationItem] = {
    "stop_deployment": ObligationItem(
        tag="stop_deployment",
        title="Stop deployment",
        description="Suspend deployment or use until the prohibited-practice issue is resolved.",
    ),
    "legal_review": ObligationItem(
        tag="legal_review",
        title="Escalate for legal review",
        description="Escalate the case to legal and compliance stakeholders for immediate review.",
    ),
    "risk_management": ObligationItem(
        tag="risk_management",
        title="Risk management system",
        description="Maintain a documented risk-management process for the AI system lifecycle.",
    ),
    "human_oversight": ObligationItem(
        tag="human_oversight",
        title="Human oversight controls",
        description="Ensure documented human oversight is designed, assigned, and operational.",
    ),
    "logging": ObligationItem(
        tag="logging",
        title="Logging and traceability",
        description=(
            "Preserve logs and decision traces needed for oversight, monitoring, and audit."
        ),
    ),
    "disclosure_notice": ObligationItem(
        tag="disclosure_notice",
        title="Transparency disclosure",
        description=(
            "Inform affected persons when they are interacting with AI in covered scenarios."
        ),
    ),
    "resolve_conflict": ObligationItem(
        tag="resolve_conflict",
        title="Resolve evidence conflict",
        description=(
            "Resolve conflicting dossier or artifact facts before relying on the assessment."
        ),
    ),
}


class AssessmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._rule_pack_service = RulePackService()

    async def list_assessments(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[AssessmentRunDetail]:
        await self._get_case(organization_id, case_id)
        runs = list(
            (
                await self._session.scalars(
                    select(AssessmentRunRecord)
                    .where(AssessmentRunRecord.case_id == case_id)
                    .order_by(AssessmentRunRecord.created_at.desc())
                )
            ).all()
        )
        return [self._to_assessment_detail(run) for run in runs]

    async def get_assessment(
        self,
        organization_id: UUID,
        case_id: UUID,
        assessment_id: UUID,
    ) -> AssessmentRunDetail:
        await self._get_case(organization_id, case_id)
        run = await self._session.scalar(
            select(AssessmentRunRecord).where(
                AssessmentRunRecord.case_id == case_id,
                AssessmentRunRecord.id == assessment_id,
            )
        )
        if run is None:
            raise ValueError(f"Assessment '{assessment_id}' was not found.")
        return self._to_assessment_detail(run)

    async def run_assessment(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> AssessmentRunDetail:
        case = await self._get_case(organization_id, case_id)
        facts, conflict_fields = await self._build_case_facts(case)
        rule_pack = await self._select_rule_pack(case.policy_snapshot_slug)
        if rule_pack is None:
            raise ValueError("No rule pack is available for the case policy snapshot.")

        hits: list[RuleHit] = []
        obligations: list[ObligationItem] = []
        summary: str
        status: AssessmentRunStatus
        primary_outcome: AssessmentOutcome

        if conflict_fields:
            primary_outcome = AssessmentOutcome.NEEDS_MORE_INFORMATION
            status = AssessmentRunStatus.NEEDS_REVIEW
            obligations = [OBLIGATION_LIBRARY["resolve_conflict"]]
            summary = (
                "The case contains conflicting extracted facts that must be resolved before "
                "a deterministic assessment can be trusted."
            )
        else:
            evaluation = await self._rule_pack_service.evaluate(rule_pack.pack_id, facts)
            hits = evaluation.hits
            primary_outcome = evaluation.primary_outcome or AssessmentOutcome.MINIMAL_RISK
            status = AssessmentRunStatus.COMPLETED
            obligations = self._map_obligations(hits)
            summary = self._summarize_outcome(primary_outcome, hits)

        run = AssessmentRunRecord(
            case_id=case.id,
            rule_pack_id=rule_pack.pack_id,
            status=status.value,
            primary_outcome=primary_outcome.value,
            summary=summary,
            facts_json=facts,
            conflict_fields=conflict_fields,
            hits_json=[hit.model_dump() for hit in hits],
            obligations_json=[obligation.model_dump() for obligation in obligations],
        )
        self._session.add(run)
        await self._session.commit()
        return self._to_assessment_detail(run, hits=hits)

    async def _get_case(self, organization_id: UUID, case_id: UUID) -> CaseRecord:
        case = await self._session.scalar(
            select(CaseRecord)
            .options(
                selectinload(CaseRecord.dossier),
                selectinload(CaseRecord.artifacts).selectinload(ArtifactRecord.extracted_facts),
            )
            .where(
                CaseRecord.organization_id == organization_id,
                CaseRecord.id == case_id,
            )
        )
        if case is None or case.dossier is None:
            raise ValueError(f"Case '{case_id}' was not found.")
        return case

    async def _build_case_facts(self, case: CaseRecord) -> tuple[dict[str, object], list[str]]:
        dossier = case.dossier
        if dossier is None:
            raise ValueError(f"Case '{case.id}' is missing its dossier.")

        facts: dict[str, object] = {}
        conflict_fields: set[str] = set()
        self._set_nested_value(facts, "use_case.domain", dossier.sector)
        self._set_nested_value(facts, "use_case.activities", [])
        self._set_nested_value(
            facts,
            "deployment.interacts_with_natural_persons",
            dossier.affects_natural_persons,
        )
        self._set_nested_value(facts, "system.uses_generative_ai", dossier.uses_generative_ai)
        self._set_nested_value(facts, "system.modalities", [])

        extracted_facts = list(
            (
                await self._session.scalars(
                    select(ExtractedFactRecord).where(ExtractedFactRecord.case_id == case.id)
                )
            ).all()
        )
        for fact in extracted_facts:
            if fact.status == ExtractedFactStatus.CONFLICT.value:
                conflict_fields.add(fact.field_path)
                continue
            candidate_value = fact.value_json.get("value")
            had_conflict = self._merge_nested_value(facts, fact.field_path, candidate_value)
            if had_conflict:
                conflict_fields.add(fact.field_path)

        return facts, sorted(conflict_fields)

    async def _select_rule_pack(self, snapshot_slug: str | None):
        packs = await self._rule_pack_service.list_rule_packs()
        if snapshot_slug is not None:
            for pack in packs:
                if pack.snapshot_slug == snapshot_slug:
                    return await self._rule_pack_service.get_rule_pack(pack.pack_id)
        if packs:
            return await self._rule_pack_service.get_rule_pack(packs[0].pack_id)
        return None

    def _map_obligations(self, hits: list[RuleHit]) -> list[ObligationItem]:
        tags: list[str] = []
        for hit in hits:
            for tag in hit.obligation_tags:
                if tag not in tags:
                    tags.append(tag)
        return [OBLIGATION_LIBRARY[tag] for tag in tags if tag in OBLIGATION_LIBRARY]

    def _summarize_outcome(self, outcome: AssessmentOutcome, hits: list[RuleHit]) -> str:
        if hits:
            return (
                f"Assessment completed with outcome '{outcome.value}' based on "
                f"{len(hits)} matching rule(s)."
            )
        return (
            "Assessment completed with no matching high-priority rules; "
            "defaulting to minimal risk."
        )

    def _to_assessment_detail(
        self,
        run: AssessmentRunRecord,
        hits: list[RuleHit] | None = None,
    ) -> AssessmentRunDetail:
        hydrated_hits = hits or [RuleHit.model_validate(payload) for payload in run.hits_json]
        obligations = [
            ObligationItem.model_validate(payload) for payload in run.obligations_json
        ]
        return AssessmentRunDetail(
            id=run.id,
            case_id=run.case_id,
            rule_pack_id=run.rule_pack_id,
            status=AssessmentRunStatus(run.status),
            primary_outcome=AssessmentOutcome(run.primary_outcome),
            created_at=run.created_at,
            summary=run.summary,
            facts=run.facts_json,
            conflict_fields=run.conflict_fields,
            hits=hydrated_hits,
            obligations=obligations,
        )

    def _set_nested_value(self, payload: dict[str, object], field_path: str, value: object) -> None:
        current: dict[str, object] = payload
        segments = field_path.split(".")
        for segment in segments[:-1]:
            next_value = current.get(segment)
            if not isinstance(next_value, dict):
                next_value = {}
                current[segment] = next_value
            current = next_value
        current[segments[-1]] = value

    def _merge_nested_value(
        self,
        payload: dict[str, object],
        field_path: str,
        value: object,
    ) -> bool:
        current: dict[str, object] = payload
        segments = field_path.split(".")
        for segment in segments[:-1]:
            next_value = current.get(segment)
            if not isinstance(next_value, dict):
                next_value = {}
                current[segment] = next_value
            current = next_value

        leaf = segments[-1]
        existing = current.get(leaf)
        if existing is None:
            current[leaf] = value
            return False
        if isinstance(existing, list) and isinstance(value, list):
            merged = list(dict.fromkeys([*existing, *value]))
            current[leaf] = merged
            return False
        if existing == value:
            return False
        return True
