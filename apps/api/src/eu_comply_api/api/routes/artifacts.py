from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import (
    AuthContext,
    get_session_dependency,
    get_settings_dependency,
    require_auth_context,
)
from eu_comply_api.config import Settings
from eu_comply_api.domain.models import ArtifactDetail, ArtifactProcessResponse, ArtifactSummary
from eu_comply_api.services.artifact_service import ArtifactService

router = APIRouter(prefix="/cases/{case_id}/artifacts")


@router.get("", response_model=list[ArtifactSummary])
async def list_artifacts(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> list[ArtifactSummary]:
    service = ArtifactService(session, settings)
    try:
        return await service.list_artifacts(auth.organization_id, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=ArtifactDetail, status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    case_id: UUID,
    file: UploadFile = File(...),
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> ArtifactDetail:
    service = ArtifactService(session, settings)
    try:
        return await service.upload_artifact(auth.organization_id, case_id, file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{artifact_id}", response_model=ArtifactDetail)
async def get_artifact(
    case_id: UUID,
    artifact_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> ArtifactDetail:
    service = ArtifactService(session, settings)
    try:
        return await service.get_artifact(auth.organization_id, case_id, artifact_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{artifact_id}/process", response_model=ArtifactProcessResponse)
async def process_artifact(
    case_id: UUID,
    artifact_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> ArtifactProcessResponse:
    service = ArtifactService(session, settings)
    try:
        return await service.process_artifact(auth.organization_id, case_id, artifact_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
