from __future__ import annotations

from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.db.models import CaseRecord, WorkflowRunRecord
from eu_comply_api.domain.models import (
    AssessmentOutcome,
    WorkflowRunDetail,
    WorkflowRunStatus,
)
from eu_comply_api.services.assessment_service import AssessmentService


class WorkflowState(TypedDict, total=False):
    organization_id: str
    case_id: str
    workflow_run_id: str
    assessment_run_id: str
    assessment_outcome: str
    assessment_status: str
    conflict_fields: list[str]
    review_required: bool
    review_reason: str | None


class WorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_workflows(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[WorkflowRunDetail]:
        await self._get_case(organization_id, case_id)
        runs = list(
            (
                await self._session.scalars(
                    select(WorkflowRunRecord)
                    .where(WorkflowRunRecord.case_id == case_id)
                    .order_by(WorkflowRunRecord.created_at.desc())
                )
            ).all()
        )
        return [self._to_workflow_detail(run) for run in runs]

    async def get_workflow(
        self,
        organization_id: UUID,
        case_id: UUID,
        workflow_id: UUID,
    ) -> WorkflowRunDetail:
        await self._get_case(organization_id, case_id)
        run = await self._session.scalar(
            select(WorkflowRunRecord).where(
                WorkflowRunRecord.case_id == case_id,
                WorkflowRunRecord.id == workflow_id,
            )
        )
        if run is None:
            raise ValueError(f"Workflow run '{workflow_id}' was not found.")
        return self._to_workflow_detail(run)

    async def run_governed_assessment(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> WorkflowRunDetail:
        await self._get_case(organization_id, case_id)
        run = WorkflowRunRecord(
            case_id=case_id,
            status=WorkflowRunStatus.RUNNING.value,
            review_required=False,
            state_json={},
        )
        self._session.add(run)
        await self._session.commit()

        graph = self._build_graph()
        final_state = await graph.ainvoke(
            WorkflowState(
                organization_id=str(organization_id),
                case_id=str(case_id),
                workflow_run_id=str(run.id),
            )
        )

        run.assessment_run_id = (
            UUID(final_state["assessment_run_id"])
            if final_state.get("assessment_run_id")
            else None
        )
        run.review_required = bool(final_state.get("review_required", False))
        run.review_reason = final_state.get("review_reason")
        run.status = (
            WorkflowRunStatus.PENDING_REVIEW.value
            if run.review_required
            else WorkflowRunStatus.COMPLETED.value
        )
        run.state_json = dict(final_state)
        await self._session.commit()
        return self._to_workflow_detail(run)

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("run_assessment", self._run_assessment_node)
        graph.add_node("review_gate", self._review_gate_node)
        graph.add_edge(START, "run_assessment")
        graph.add_edge("run_assessment", "review_gate")
        graph.add_edge("review_gate", END)
        return graph.compile()

    async def _run_assessment_node(self, state: WorkflowState) -> WorkflowState:
        assessment_service = AssessmentService(self._session)
        assessment = await assessment_service.run_assessment(
            UUID(state["organization_id"]),
            UUID(state["case_id"]),
        )
        return WorkflowState(
            **state,
            assessment_run_id=str(assessment.id),
            assessment_outcome=assessment.primary_outcome.value,
            assessment_status=assessment.status.value,
            conflict_fields=assessment.conflict_fields,
        )

    async def _review_gate_node(self, state: WorkflowState) -> WorkflowState:
        outcome = AssessmentOutcome(state["assessment_outcome"])
        review_required = outcome in {
            AssessmentOutcome.NEEDS_MORE_INFORMATION,
            AssessmentOutcome.PROHIBITED,
        }
        review_reason = None
        if outcome == AssessmentOutcome.NEEDS_MORE_INFORMATION:
            review_reason = "Conflicting or insufficient facts require human review."
        elif outcome == AssessmentOutcome.PROHIBITED:
            review_reason = "Prohibited outcomes require human review before closure."

        return WorkflowState(
            **state,
            review_required=review_required,
            review_reason=review_reason,
        )

    async def _get_case(self, organization_id: UUID, case_id: UUID) -> CaseRecord:
        case = await self._session.scalar(
            select(CaseRecord).where(
                CaseRecord.organization_id == organization_id,
                CaseRecord.id == case_id,
            )
        )
        if case is None:
            raise ValueError(f"Case '{case_id}' was not found.")
        return case

    def _to_workflow_detail(self, run: WorkflowRunRecord) -> WorkflowRunDetail:
        return WorkflowRunDetail(
            id=run.id,
            case_id=run.case_id,
            assessment_run_id=run.assessment_run_id,
            status=WorkflowRunStatus(run.status),
            review_required=run.review_required,
            review_reason=run.review_reason,
            created_at=run.created_at,
            state=run.state_json,
        )
