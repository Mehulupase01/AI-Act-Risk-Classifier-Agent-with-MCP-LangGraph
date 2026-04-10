from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import AuthContext, get_session_dependency, require_auth_context
from eu_comply_api.domain.models import (
    ConnectorConfigCreateRequest,
    ConnectorConfigDetail,
    ConnectorConfigSummary,
    ConnectorConfigUpdateRequest,
    ConnectorSyncDetail,
    ConnectorSyncRequest,
    ConnectorSyncResponse,
)
from eu_comply_api.services.connector_service import ConnectorService

router = APIRouter(prefix="/connectors")


@router.get("", response_model=list[ConnectorConfigSummary])
async def list_connectors(
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[ConnectorConfigSummary]:
    return await ConnectorService(session).list_connectors(auth.organization_id)


@router.post("", response_model=ConnectorConfigDetail, status_code=status.HTTP_201_CREATED)
async def create_connector(
    payload: ConnectorConfigCreateRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ConnectorConfigDetail:
    service = ConnectorService(session)
    try:
        return await service.create_connector(auth.organization_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{connector_id}", response_model=ConnectorConfigDetail)
async def get_connector(
    connector_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ConnectorConfigDetail:
    service = ConnectorService(session)
    try:
        return await service.get_connector(auth.organization_id, connector_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{connector_id}", response_model=ConnectorConfigDetail)
async def update_connector(
    connector_id: UUID,
    payload: ConnectorConfigUpdateRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ConnectorConfigDetail:
    service = ConnectorService(session)
    try:
        return await service.update_connector(auth.organization_id, connector_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{connector_id}/sync-runs", response_model=list[ConnectorSyncDetail])
async def list_connector_sync_runs(
    connector_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[ConnectorSyncDetail]:
    service = ConnectorService(session)
    try:
        return await service.list_sync_runs(auth.organization_id, connector_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{connector_id}/sync", response_model=ConnectorSyncResponse)
async def run_connector_sync(
    connector_id: UUID,
    payload: ConnectorSyncRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ConnectorSyncResponse:
    service = ConnectorService(session)
    try:
        return await service.run_sync(auth.organization_id, connector_id, payload, auth.subject)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{connector_id}/events", response_model=ConnectorSyncResponse)
async def receive_connector_events(
    connector_id: UUID,
    payload: ConnectorSyncRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ConnectorSyncResponse:
    service = ConnectorService(session)
    try:
        return await service.run_sync(auth.organization_id, connector_id, payload, auth.subject)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
