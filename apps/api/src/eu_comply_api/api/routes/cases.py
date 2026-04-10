from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import (
    AuthContext,
    get_session_dependency,
    require_auth_context,
)
from eu_comply_api.domain.models import (
    CaseCreateRequest,
    CaseDetail,
    CaseSummary,
    CaseUpdateRequest,
)
from eu_comply_api.services.case_service import CaseService

router = APIRouter(prefix="/cases")


@router.get("", response_model=list[CaseSummary])
async def list_cases(
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[CaseSummary]:
    service = CaseService(session)
    return await service.list_cases(auth.organization_id)


@router.post("", response_model=CaseDetail, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreateRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> CaseDetail:
    service = CaseService(session)
    return await service.create_case(auth.organization_id, payload)


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> CaseDetail:
    service = CaseService(session)
    try:
        return await service.get_case(auth.organization_id, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{case_id}", response_model=CaseDetail)
async def update_case(
    case_id: UUID,
    payload: CaseUpdateRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> CaseDetail:
    service = CaseService(session)
    try:
        return await service.update_case(auth.organization_id, case_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
