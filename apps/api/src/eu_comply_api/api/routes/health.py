from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import (
    AuthContext,
    get_session_dependency,
    get_settings_dependency,
    require_auth_context,
)
from eu_comply_api.config import Settings
from eu_comply_api.domain.models import (
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
)
from eu_comply_api.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("/health/liveness", response_model=LivenessResponse)
async def liveness(settings: Settings = Depends(get_settings_dependency)) -> LivenessResponse:
    return LivenessResponse(
        status=HealthStatus.OK,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/health/readiness", response_model=ReadinessResponse)
async def readiness(
    settings: Settings = Depends(get_settings_dependency),
    session: AsyncSession = Depends(get_session_dependency),
) -> ReadinessResponse:
    return await MonitoringService(session, settings).readiness()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics(
    auth: AuthContext = Depends(require_auth_context),
    settings: Settings = Depends(get_settings_dependency),
    session: AsyncSession = Depends(get_session_dependency),
) -> PlainTextResponse:
    payload = await MonitoringService(session, settings).render_metrics(auth.organization_id)
    return PlainTextResponse(
        content=payload,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
