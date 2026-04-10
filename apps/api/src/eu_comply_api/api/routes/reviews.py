from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import AuthContext, get_session_dependency, require_auth_context
from eu_comply_api.domain.models import ReviewDecisionCreateRequest, ReviewDecisionSummary
from eu_comply_api.services.review_service import ReviewService

router = APIRouter(prefix="/cases/{case_id}/reviews")


@router.get("", response_model=list[ReviewDecisionSummary])
async def list_reviews(
    case_id: UUID,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> list[ReviewDecisionSummary]:
    service = ReviewService(session)
    try:
        return await service.list_reviews(auth.organization_id, case_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=ReviewDecisionSummary, status_code=status.HTTP_201_CREATED)
async def create_review(
    case_id: UUID,
    payload: ReviewDecisionCreateRequest,
    auth: AuthContext = Depends(require_auth_context),
    session: AsyncSession = Depends(get_session_dependency),
) -> ReviewDecisionSummary:
    service = ReviewService(session)
    try:
        return await service.create_review(
            auth.organization_id,
            case_id,
            reviewer_identifier=f"{auth.actor_type.value}:{auth.subject}",
            payload=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
