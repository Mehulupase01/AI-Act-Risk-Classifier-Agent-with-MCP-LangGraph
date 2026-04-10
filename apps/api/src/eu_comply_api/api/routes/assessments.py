from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import AuthContext, get_session_dependency, require_auth_context
from eu_comply_api.domain.models import AssessmentRunDetail
from eu_comply_api.services.assessment_service import AssessmentService

router = APIRouter(prefix="/cases/{case_id}/assessments")


@router.get("", response_model=list[AssessmentRunDetail])
async def list_assessments(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[AssessmentRunDetail]:
    service = AssessmentService(session)
    try:
        return await service.list_assessments(auth.organization_id, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=AssessmentRunDetail, status_code=status.HTTP_201_CREATED)
async def run_assessment(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> AssessmentRunDetail:
    service = AssessmentService(session)
    try:
        return await service.run_assessment(auth.organization_id, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{assessment_id}", response_model=AssessmentRunDetail)
async def get_assessment(
    case_id: UUID,
    assessment_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> AssessmentRunDetail:
    service = AssessmentService(session)
    try:
        return await service.get_assessment(auth.organization_id, case_id, assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
