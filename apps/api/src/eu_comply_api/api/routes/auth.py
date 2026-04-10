from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.api.deps import get_session_dependency, get_settings_dependency
from eu_comply_api.config import Settings
from eu_comply_api.domain.models import ClientTokenRequest, LoginRequest, TokenResponse
from eu_comply_api.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    service = AuthService(session, settings)
    try:
        return await service.login_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/token", response_model=TokenResponse)
async def issue_client_token(
    payload: ClientTokenRequest,
    session: AsyncSession = Depends(get_session_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    service = AuthService(session, settings)
    try:
        return await service.login_client(payload.client_id, payload.client_secret)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
