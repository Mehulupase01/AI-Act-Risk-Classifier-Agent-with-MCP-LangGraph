from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import (
    AuthContext,
    get_session_dependency,
    get_settings_dependency,
    require_auth_context,
)
from eu_comply_api.config import Settings
from eu_comply_api.domain.models import (
    ProviderKind,
    ProviderSummary,
    RuntimeConfigResponse,
    RuntimeConfigUpdate,
    RuntimeDiscoveryResponse,
)
from eu_comply_api.services.runtime_control_service import RuntimeControlService

router = APIRouter()


@router.get("/providers", response_model=list[ProviderSummary])
async def list_providers(
    _: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> list[ProviderSummary]:
    service = RuntimeControlService(session, settings)
    return await service.list_providers()


@router.get("/models", response_model=RuntimeDiscoveryResponse)
async def list_models(
    provider: ProviderKind = Query(...),
    _: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> RuntimeDiscoveryResponse:
    service = RuntimeControlService(session, settings)
    try:
        return await service.list_models(provider)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/config", response_model=RuntimeConfigResponse)
async def get_runtime_config(
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> RuntimeConfigResponse:
    service = RuntimeControlService(session, settings)
    try:
        return await service.get_runtime_config(auth.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/config", response_model=RuntimeConfigResponse)
async def update_runtime_config(
    payload: RuntimeConfigUpdate,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> RuntimeConfigResponse:
    service = RuntimeControlService(session, settings)
    try:
        return await service.update_runtime_config(auth.organization_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
