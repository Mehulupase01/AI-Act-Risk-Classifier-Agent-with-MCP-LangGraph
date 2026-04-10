from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import AuthContext, get_session_dependency, require_auth_context
from eu_comply_api.domain.models import (
    ReassessmentTriggerCreateRequest,
    ReassessmentTriggerDetail,
    ReassessmentTriggerSummary,
)
from eu_comply_api.services.reassessment_service import ReassessmentService

router = APIRouter(prefix="/cases/{case_id}/reassessments")


@router.get("", response_model=list[ReassessmentTriggerSummary])
async def list_reassessments(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[ReassessmentTriggerSummary]:
    service = ReassessmentService(session)
    try:
        return await service.list_triggers(auth.organization_id, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=ReassessmentTriggerDetail, status_code=status.HTTP_201_CREATED)
async def create_reassessment(
    case_id: UUID,
    payload: ReassessmentTriggerCreateRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ReassessmentTriggerDetail:
    service = ReassessmentService(session)
    try:
        return await service.create_manual_trigger(
            auth.organization_id,
            case_id,
            payload,
            auth.subject,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
