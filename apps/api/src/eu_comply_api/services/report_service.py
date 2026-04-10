from __future__ import annotations

import json
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eu_comply_api.db.models import (
    ArtifactRecord,
    AssessmentRunRecord,
    CaseRecord,
    ReviewDecisionRecord,
    WorkflowRunRecord,
)
from eu_comply_api.domain.models import (
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

    async def _get_case(self, organization_id: UUID, case_id: UUID) -> CaseRecord:
        case = await self._session.scalar(
            select(CaseRecord)
            .options(
                selectinload(CaseRecord.dossier),
                selectinload(CaseRecord.artifacts).selectinload(ArtifactRecord.extracted_facts),
                selectinload(CaseRecord.assessment_runs),
                selectinload(CaseRecord.workflow_runs),
                selectinload(CaseRecord.reviews),
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
            "dossier": {
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
            },
            "artifacts": [self._serialize_artifact(artifact) for artifact in case.artifacts],
            "latest_assessment": (
                self._serialize_assessment(latest_assessment) if latest_assessment else None
            ),
            "latest_workflow": (
                self._serialize_workflow(latest_workflow) if latest_workflow else None
            ),
            "latest_review": self._serialize_review(latest_review) if latest_review else None,
            "review_history": [self._serialize_review(review) for review in case.reviews],
        }

    def _serialize_artifact(self, artifact: ArtifactRecord) -> dict[str, object]:
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

    def _serialize_assessment(
        self,
        assessment: AssessmentRunRecord,
    ) -> dict[str, object]:
        return {
            "id": str(assessment.id),
            "rule_pack_id": assessment.rule_pack_id,
            "status": assessment.status,
            "primary_outcome": assessment.primary_outcome,
            "summary": assessment.summary,
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

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "case"
