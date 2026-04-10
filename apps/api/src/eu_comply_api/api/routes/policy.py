from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import (
    AuthContext,
    get_session_dependency,
    require_auth_context,
)
from eu_comply_api.domain.models import (
    PolicySnapshotDetail,
    PolicySnapshotSummary,
    PolicySourceSummary,
)
from eu_comply_api.services.policy_service import PolicyService

router = APIRouter()


@router.get("/policy-sources", response_model=list[PolicySourceSummary])
async def list_policy_sources(
    _: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[PolicySourceSummary]:
    service = PolicyService(session)
    return await service.list_sources()


@router.get("/policy-snapshots", response_model=list[PolicySnapshotSummary])
async def list_policy_snapshots(
    _: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[PolicySnapshotSummary]:
    service = PolicyService(session)
    return await service.list_snapshots()


@router.get("/policy-snapshots/{snapshot_slug}", response_model=PolicySnapshotDetail)
async def get_policy_snapshot(
    snapshot_slug: str,
    _: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> PolicySnapshotDetail:
    service = PolicyService(session)
    snapshot = await service.get_snapshot(snapshot_slug)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy snapshot '{snapshot_slug}' was not found.",
        )
    return snapshot
