from __future__ import annotations

import base64
import json
import re
from io import BytesIO
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eu_comply_api.db.base import utc_now
from eu_comply_api.db.models import (
    ArtifactRecord,
    AssessmentRunRecord,
    CaseRecord,
    NormFragmentRecord,
    PolicySnapshotRecord,
    ReassessmentTriggerRecord,
    ReviewDecisionRecord,
    WorkflowRunRecord,
)
from eu_comply_api.domain.models import (
    AssessmentOutcome,
    AuditPackExportResponse,
    AuditPackFileSummary,
    AuditPackManifest,
    ReportExportRequest,
    ReportExportResponse,
    ReportFormat,
)


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def export_case_report(
        self,
        organization_id: UUID,
        case_id: UUID,
        payload: ReportExportRequest,
    ) -> ReportExportResponse:
        case = await self._get_case(organization_id, case_id)
        report_payload = self._build_report_payload(case)
        if payload.format == ReportFormat.JSON:
            content = json.dumps(report_payload, indent=2, default=str)
            extension = "json"
            media_type = "application/json"
        else:
            content = self._render_markdown(report_payload)
            extension = "md"
            media_type = "text/markdown"

        filename = f"{self._slugify(case.title)}-assessment-report.{extension}"
        return ReportExportResponse(
            case_id=case.id,
            format=payload.format,
            filename=filename,
            media_type=media_type,
            content=content,
        )

    async def export_audit_pack(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> AuditPackExportResponse:
        case = await self._get_case(organization_id, case_id)
        report_payload = self._build_report_payload(case)
        workspace_payload = self._build_workspace_payload(case)
        policy_payload = await self._build_policy_payload(case, report_payload)
        reassessment_payload = [
            self._serialize_reassessment(trigger) for trigger in case.reassessment_triggers
        ]

        file_payloads = {
            "reports/assessment-report.json": (
                self._to_json_bytes(report_payload),
                "application/json",
            ),
            "reports/assessment-report.md": (
                self._render_markdown(report_payload).encode("utf-8"),
                "text/markdown",
            ),
            "workspace/case-workspace.json": (
                self._to_json_bytes(workspace_payload),
                "application/json",
            ),
            "evidence/artifacts.json": (
                self._to_json_bytes(workspace_payload["artifacts"]),
                "application/json",
            ),
            "workflow/reviews.json": (
                self._to_json_bytes(workspace_payload["reviews"]),
                "application/json",
            ),
            "workflow/reassessments.json": (
                self._to_json_bytes(reassessment_payload),
                "application/json",
            ),
            "policy/policy-snapshot.json": (
                self._to_json_bytes(policy_payload["snapshot"]),
                "application/json",
            ),
            "policy/referenced-fragments.json": (
                self._to_json_bytes(policy_payload["referenced_fragments"]),
                "application/json",
            ),
        }

        manifest = AuditPackManifest(
            generated_at=utc_now(),
            case_id=case.id,
            case_title=case.title,
            policy_snapshot_slug=case.policy_snapshot_slug,
            latest_assessment_outcome=(
                AssessmentOutcome(report_payload["latest_assessment"]["primary_outcome"])
                if report_payload["latest_assessment"]
                else None
            ),
            artifact_count=len(case.artifacts),
            review_count=len(case.reviews),
            reassessment_count=len(case.reassessment_triggers),
            referenced_citations=self._extract_referenced_citations(report_payload),
            files=[
                AuditPackFileSummary(
                    path=path,
                    media_type=media_type,
                    size_bytes=len(content),
                )
                for path, (content, media_type) in file_payloads.items()
            ],
        )

        buffer = BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", self._to_json_bytes(manifest.model_dump(mode="json")))
            for path, (content, _media_type) in file_payloads.items():
                archive.writestr(path, content)

        filename = f"{self._slugify(case.title)}-audit-pack.zip"
        return AuditPackExportResponse(
            case_id=case.id,
            filename=filename,
            media_type="application/zip",
            content_base64=base64.b64encode(buffer.getvalue()).decode("ascii"),
            manifest=manifest,
        )

    async def _get_case(self, organization_id: UUID, case_id: UUID) -> CaseRecord:
        case = await self._session.scalar(
            select(CaseRecord)
            .options(
                selectinload(CaseRecord.dossier),
                selectinload(CaseRecord.artifacts)
                .selectinload(ArtifactRecord.chunks),
                selectinload(CaseRecord.artifacts)
                .selectinload(ArtifactRecord.extracted_facts),
                selectinload(CaseRecord.assessment_runs),
                selectinload(CaseRecord.workflow_runs),
                selectinload(CaseRecord.reviews),
                selectinload(CaseRecord.reassessment_triggers),
            )
            .where(
                CaseRecord.organization_id == organization_id,
                CaseRecord.id == case_id,
            )
        )
        if case is None or case.dossier is None:
            raise LookupError(f"Case '{case_id}' was not found.")
        return case

    def _build_report_payload(self, case: CaseRecord) -> dict[str, object]:
        dossier = case.dossier
        if dossier is None:
            raise ValueError(f"Case '{case.id}' is missing its dossier.")

        latest_assessment = case.assessment_runs[0] if case.assessment_runs else None
        latest_workflow = case.workflow_runs[0] if case.workflow_runs else None
        latest_review = case.reviews[0] if case.reviews else None

        return {
            "case": {
                "id": str(case.id),
                "title": case.title,
                "description": case.description,
                "status": case.status,
                "owner_team": case.owner_team,
                "policy_snapshot_slug": case.policy_snapshot_slug,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
            },
            "dossier": self._serialize_dossier(dossier),
            "artifacts": [
                self._serialize_artifact_summary(artifact) for artifact in case.artifacts
            ],
            "latest_assessment": (
                self._serialize_assessment(latest_assessment) if latest_assessment else None
            ),
            "latest_workflow": (
                self._serialize_workflow(latest_workflow) if latest_workflow else None
            ),
            "latest_review": self._serialize_review(latest_review) if latest_review else None,
            "review_history": [self._serialize_review(review) for review in case.reviews],
        }

    def _build_workspace_payload(self, case: CaseRecord) -> dict[str, object]:
        dossier = case.dossier
        if dossier is None:
            raise ValueError(f"Case '{case.id}' is missing its dossier.")

        return {
            "case": {
                "id": str(case.id),
                "title": case.title,
                "description": case.description,
                "status": case.status,
                "owner_team": case.owner_team,
                "policy_snapshot_slug": case.policy_snapshot_slug,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
            },
            "dossier": self._serialize_dossier(dossier),
            "artifacts": [self._serialize_artifact_detail(artifact) for artifact in case.artifacts],
            "assessments": [
                self._serialize_assessment(assessment) for assessment in case.assessment_runs
            ],
            "workflows": [self._serialize_workflow(workflow) for workflow in case.workflow_runs],
            "reviews": [self._serialize_review(review) for review in case.reviews],
            "reassessments": [
                self._serialize_reassessment(trigger) for trigger in case.reassessment_triggers
            ],
        }

    async def _build_policy_payload(
        self,
        case: CaseRecord,
        report_payload: dict[str, object],
    ) -> dict[str, object]:
        if case.policy_snapshot_slug is None:
            return {"snapshot": None, "referenced_fragments": []}

        snapshot = await self._session.scalar(
            select(PolicySnapshotRecord).where(
                PolicySnapshotRecord.slug == case.policy_snapshot_slug
            )
        )
        if snapshot is None:
            return {
                "snapshot": {"slug": case.policy_snapshot_slug, "status": "missing"},
                "referenced_fragments": [],
            }

        citations = self._extract_referenced_citations(report_payload)
        fragment_query = (
            select(NormFragmentRecord)
            .where(NormFragmentRecord.snapshot_id == snapshot.id)
            .order_by(NormFragmentRecord.order_index.asc())
        )
        if citations:
            fragment_query = fragment_query.where(NormFragmentRecord.citation.in_(citations))
        fragments = list((await self._session.scalars(fragment_query)).all())

        return {
            "snapshot": {
                "id": str(snapshot.id),
                "slug": snapshot.slug,
                "title": snapshot.title,
                "jurisdiction": snapshot.jurisdiction,
                "effective_from": snapshot.effective_from,
                "description": snapshot.description,
            },
            "referenced_fragments": [
                {
                    "id": str(fragment.id),
                    "citation": fragment.citation,
                    "heading": fragment.heading,
                    "body": fragment.body,
                    "tags": fragment.tags,
                    "actor_scope": fragment.actor_scope,
                }
                for fragment in fragments
            ],
        }

    def _serialize_dossier(self, dossier) -> dict[str, object]:
        return {
            "system_name": dossier.system_name,
            "actor_role": dossier.actor_role,
            "sector": dossier.sector,
            "intended_purpose": dossier.intended_purpose,
            "model_provider": dossier.model_provider,
            "model_name": dossier.model_name,
            "uses_generative_ai": dossier.uses_generative_ai,
            "affects_natural_persons": dossier.affects_natural_persons,
            "geographic_scope": dossier.geographic_scope,
            "deployment_channels": dossier.deployment_channels,
            "human_oversight_summary": dossier.human_oversight_summary,
        }

    def _serialize_artifact_summary(self, artifact: ArtifactRecord) -> dict[str, object]:
        return {
            "id": str(artifact.id),
            "filename": artifact.filename,
            "status": artifact.status,
            "parser_name": artifact.parser_name,
            "size_bytes": artifact.size_bytes,
            "updated_at": artifact.updated_at.isoformat(),
            "fact_count": len(artifact.extracted_facts),
            "conflict_count": len(
                [fact for fact in artifact.extracted_facts if fact.status == "conflict"]
            ),
        }

    def _serialize_artifact_detail(self, artifact: ArtifactRecord) -> dict[str, object]:
        return {
            **self._serialize_artifact_summary(artifact),
            "content_type": artifact.content_type,
            "sha256": artifact.sha256,
            "processing_error": artifact.processing_error,
            "chunks": [
                {
                    "id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                    "text_preview": chunk.text_content[:240],
                }
                for chunk in artifact.chunks
            ],
            "extracted_facts": [
                {
                    "id": str(fact.id),
                    "field_path": fact.field_path,
                    "value": fact.value_json.get("value"),
                    "confidence": fact.confidence,
                    "extraction_method": fact.extraction_method,
                    "status": fact.status,
                    "rationale": fact.rationale,
                    "source_chunk_indexes": fact.source_chunk_indexes,
                }
                for fact in artifact.extracted_facts
            ],
        }

    def _serialize_assessment(self, assessment: AssessmentRunRecord) -> dict[str, object]:
        return {
            "id": str(assessment.id),
            "rule_pack_id": assessment.rule_pack_id,
            "status": assessment.status,
            "primary_outcome": assessment.primary_outcome,
            "summary": assessment.summary,
            "facts": assessment.facts_json,
            "conflict_fields": assessment.conflict_fields,
            "obligations": assessment.obligations_json,
            "hits": assessment.hits_json,
            "created_at": assessment.created_at.isoformat(),
        }

    def _serialize_workflow(self, workflow: WorkflowRunRecord) -> dict[str, object]:
        return {
            "id": str(workflow.id),
            "assessment_run_id": str(workflow.assessment_run_id)
            if workflow.assessment_run_id
            else None,
            "status": workflow.status,
            "review_required": workflow.review_required,
            "review_reason": workflow.review_reason,
            "state": workflow.state_json,
            "created_at": workflow.created_at.isoformat(),
        }

    def _serialize_review(self, review: ReviewDecisionRecord) -> dict[str, object]:
        return {
            "id": str(review.id),
            "assessment_run_id": str(review.assessment_run_id)
            if review.assessment_run_id
            else None,
            "workflow_run_id": str(review.workflow_run_id) if review.workflow_run_id else None,
            "reviewer_identifier": review.reviewer_identifier,
            "decision": review.decision,
            "rationale": review.rationale,
            "approved_outcome": review.approved_outcome,
            "created_at": review.created_at.isoformat(),
        }

    def _serialize_reassessment(self, trigger: ReassessmentTriggerRecord) -> dict[str, object]:
        return {
            "id": str(trigger.id),
            "case_id": str(trigger.case_id),
            "connector_id": str(trigger.connector_id) if trigger.connector_id else None,
            "sync_run_id": str(trigger.sync_run_id) if trigger.sync_run_id else None,
            "workflow_run_id": str(trigger.workflow_run_id) if trigger.workflow_run_id else None,
            "reason": trigger.reason,
            "source": trigger.source,
            "status": trigger.status,
            "title": trigger.title,
            "detail": trigger.detail,
            "requested_by": trigger.requested_by,
            "payload": trigger.payload_json,
            "processed_at": trigger.processed_at.isoformat() if trigger.processed_at else None,
            "created_at": trigger.created_at.isoformat(),
        }

    def _extract_referenced_citations(self, report_payload: dict[str, object]) -> list[str]:
        latest_assessment = report_payload["latest_assessment"]
        if not latest_assessment:
            return []
        citations: list[str] = []
        for hit in latest_assessment["hits"]:
            for citation in hit["citation_refs"]:
                if citation not in citations:
                    citations.append(citation)
        return citations

    def _render_markdown(self, payload: dict[str, object]) -> str:
        case = payload["case"]
        dossier = payload["dossier"]
        artifacts = payload["artifacts"]
        latest_assessment = payload["latest_assessment"]
        latest_workflow = payload["latest_workflow"]
        latest_review = payload["latest_review"]

        lines = [
            f"# {case['title']} Assessment Report",
            "",
            "## Case Summary",
            f"- Case ID: `{case['id']}`",
            f"- Status: `{case['status']}`",
            f"- Owner Team: {case['owner_team']}",
            f"- Policy Snapshot: {case['policy_snapshot_slug'] or 'Not set'}",
            f"- Updated At: {case['updated_at']}",
            "",
            "## System Dossier",
            f"- System Name: {dossier['system_name']}",
            f"- Actor Role: {dossier['actor_role']}",
            f"- Sector: {dossier['sector']}",
            f"- Intended Purpose: {dossier['intended_purpose']}",
            f"- Geographic Scope: {', '.join(dossier['geographic_scope']) or 'None recorded'}",
            (
                f"- Deployment Channels: "
                f"{', '.join(dossier['deployment_channels']) or 'None recorded'}"
            ),
            "",
            "## Evidence Inventory",
        ]

        if artifacts:
            for artifact in artifacts:
                lines.append(
                    "- "
                    f"{artifact['filename']} "
                    f"(`{artifact['status']}`, "
                    f"facts={artifact['fact_count']}, "
                    f"conflicts={artifact['conflict_count']})"
                )
        else:
            lines.append("- No artifacts uploaded.")

        lines.extend(["", "## Latest Assessment"])
        if latest_assessment:
            lines.extend(
                [
                    f"- Outcome: `{latest_assessment['primary_outcome']}`",
                    f"- Status: `{latest_assessment['status']}`",
                    f"- Summary: {latest_assessment['summary']}",
                ]
            )
        else:
            lines.append("- No assessment run recorded.")

        lines.extend(["", "## Latest Workflow"])
        if latest_workflow:
            lines.extend(
                [
                    f"- Status: `{latest_workflow['status']}`",
                    f"- Review Required: `{latest_workflow['review_required']}`",
                    f"- Review Reason: {latest_workflow['review_reason'] or 'None'}",
                ]
            )
        else:
            lines.append("- No workflow run recorded.")

        lines.extend(["", "## Latest Review"])
        if latest_review:
            lines.extend(
                [
                    f"- Reviewer: `{latest_review['reviewer_identifier']}`",
                    f"- Decision: `{latest_review['decision']}`",
                    f"- Approved Outcome: `{latest_review['approved_outcome'] or 'n/a'}`",
                    f"- Rationale: {latest_review['rationale']}",
                ]
            )
        else:
            lines.append("- No review decision recorded.")

        return "\n".join(lines)

    def _to_json_bytes(self, payload: object) -> bytes:
        return json.dumps(payload, indent=2, default=str).encode("utf-8")

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "case"
