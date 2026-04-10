from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import AuthContext, get_session_dependency, require_auth_context
from eu_comply_api.domain.models import WorkflowRunDetail
from eu_comply_api.services.workflow_service import WorkflowService

router = APIRouter(prefix="/cases/{case_id}/workflow-runs")


@router.get("", response_model=list[WorkflowRunDetail])
async def list_workflows(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[WorkflowRunDetail]:
    service = WorkflowService(session)
    try:
        return await service.list_workflows(auth.organization_id, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=WorkflowRunDetail, status_code=status.HTTP_201_CREATED)
async def run_workflow(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> WorkflowRunDetail:
    service = WorkflowService(session)
    try:
        return await service.run_governed_assessment(auth.organization_id, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{workflow_id}", response_model=WorkflowRunDetail)
async def get_workflow(
    case_id: UUID,
    workflow_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> WorkflowRunDetail:
    service = WorkflowService(session)
    try:
        return await service.get_workflow(auth.organization_id, case_id, workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
