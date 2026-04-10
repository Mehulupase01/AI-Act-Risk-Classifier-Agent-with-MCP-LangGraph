from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.db.models import (
    AssessmentRunRecord,
    CaseRecord,
    ReviewDecisionRecord,
    WorkflowRunRecord,
)
from eu_comply_api.domain.models import (
    AssessmentOutcome,
    CaseStatus,
    ReviewDecisionCreateRequest,
    ReviewDecisionStatus,
    ReviewDecisionSummary,
    WorkflowRunStatus,
)


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_reviews(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[ReviewDecisionSummary]:
        await self._get_case(organization_id, case_id)
        reviews = list(
            (
                await self._session.scalars(
                    select(ReviewDecisionRecord)
                    .where(ReviewDecisionRecord.case_id == case_id)
                    .order_by(ReviewDecisionRecord.created_at.desc())
                )
            ).all()
        )
        return [self._to_summary(review) for review in reviews]

    async def create_review(
        self,
        organization_id: UUID,
        case_id: UUID,
        reviewer_identifier: str,
        payload: ReviewDecisionCreateRequest,
    ) -> ReviewDecisionSummary:
        case = await self._get_case(organization_id, case_id)
        if payload.assessment_run_id is None and payload.workflow_run_id is None:
            raise ValueError("A review must reference an assessment run or workflow run.")

        assessment: AssessmentRunRecord | None = None
        if payload.assessment_run_id is not None:
            assessment = await self._session.scalar(
                select(AssessmentRunRecord).where(
                    AssessmentRunRecord.case_id == case_id,
                    AssessmentRunRecord.id == payload.assessment_run_id,
                )
            )
            if assessment is None:
                raise LookupError(
                    f"Assessment run '{payload.assessment_run_id}' was not found."
                )

        workflow: WorkflowRunRecord | None = None
        if payload.workflow_run_id is not None:
            workflow = await self._session.scalar(
                select(WorkflowRunRecord).where(
                    WorkflowRunRecord.case_id == case_id,
                    WorkflowRunRecord.id == payload.workflow_run_id,
                )
            )
            if workflow is None:
                raise LookupError(f"Workflow run '{payload.workflow_run_id}' was not found.")

        if (
            assessment is not None
            and workflow is not None
            and workflow.assessment_run_id is not None
            and workflow.assessment_run_id != assessment.id
        ):
            raise ValueError(
                "The supplied assessment run does not match the workflow run assessment."
            )

        approved_outcome = payload.approved_outcome
        if payload.decision == ReviewDecisionStatus.NEEDS_CHANGES and approved_outcome is not None:
            raise ValueError("An approved outcome can only be set when the review is approved.")

        if payload.decision == ReviewDecisionStatus.APPROVED and approved_outcome is None:
            approved_outcome = self._resolve_default_approved_outcome(assessment, workflow)

        review = ReviewDecisionRecord(
            case_id=case_id,
            assessment_run_id=payload.assessment_run_id,
            workflow_run_id=payload.workflow_run_id,
            reviewer_identifier=reviewer_identifier,
            decision=payload.decision.value,
            rationale=payload.rationale,
            approved_outcome=approved_outcome.value if approved_outcome else None,
        )
        self._session.add(review)
        case.status = (
            CaseStatus.APPROVED.value
            if payload.decision == ReviewDecisionStatus.APPROVED
            else CaseStatus.NEEDS_CHANGES.value
        )
        if workflow is not None and payload.decision == ReviewDecisionStatus.APPROVED:
            workflow.status = WorkflowRunStatus.COMPLETED.value
            workflow.review_required = False
        await self._session.commit()
        return self._to_summary(review)

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

    def _resolve_default_approved_outcome(
        self,
        assessment: AssessmentRunRecord | None,
        workflow: WorkflowRunRecord | None,
    ) -> AssessmentOutcome | None:
        if assessment is not None:
            return AssessmentOutcome(assessment.primary_outcome)
        if workflow is not None:
            outcome = workflow.state_json.get("assessment_outcome")
            if isinstance(outcome, str):
                return AssessmentOutcome(outcome)
        return None

    def _to_summary(self, review: ReviewDecisionRecord) -> ReviewDecisionSummary:
        return ReviewDecisionSummary(
            id=review.id,
            case_id=review.case_id,
            assessment_run_id=review.assessment_run_id,
            workflow_run_id=review.workflow_run_id,
            reviewer_identifier=review.reviewer_identifier,
            decision=ReviewDecisionStatus(review.decision),
            rationale=review.rationale,
            approved_outcome=(
                AssessmentOutcome(review.approved_outcome)
                if review.approved_outcome
                else None
            ),
            created_at=review.created_at,
        )
