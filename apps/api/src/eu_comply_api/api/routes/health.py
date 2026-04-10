from fastapi import APIRouter, Depends

from eu_comply_api.api.deps import get_settings_dependency
from eu_comply_api.config import Settings
from eu_comply_api.domain.models import (
    HealthStatus,
    LivenessResponse,
    ReadinessCheck,
    ReadinessResponse,
)

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
async def readiness(settings: Settings = Depends(get_settings_dependency)) -> ReadinessResponse:
    checks = [
        ReadinessCheck(
            name="configuration",
            status=HealthStatus.OK,
            detail=(
                "Runtime defaults: "
                f"chat={settings.llm_default_provider}, "
                f"embeddings={settings.embedding_default_provider}"
            ),
        )
    ]
    return ReadinessResponse(status=HealthStatus.OK, checks=checks)
