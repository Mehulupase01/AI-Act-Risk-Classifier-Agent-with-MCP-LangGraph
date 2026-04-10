from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import AuthContext, get_session_dependency, require_auth_context
from eu_comply_api.domain.models import ReportExportRequest, ReportExportResponse
from eu_comply_api.services.report_service import ReportService

router = APIRouter(prefix="/cases/{case_id}/reports")


@router.post("/export", response_model=ReportExportResponse)
async def export_report(
    case_id: UUID,
    payload: ReportExportRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ReportExportResponse:
    service = ReportService(session)
    try:
        return await service.export_case_report(auth.organization_id, case_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
