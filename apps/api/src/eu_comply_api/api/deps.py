from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.config import Settings, get_settings
from eu_comply_api.core.security import decode_access_token
from eu_comply_api.db.session import get_db_session
from eu_comply_api.domain.models import ActorType

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthContext:
    subject: str
    actor_type: ActorType
    organization_id: UUID


def get_settings_dependency() -> Settings:
    return get_settings()


async def get_session_dependency(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncIterator[AsyncSession]:
    yield session


def require_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings_dependency),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    try:
        payload = decode_access_token(settings, credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return AuthContext(
        subject=str(payload["sub"]),
        actor_type=ActorType(payload["actor_type"]),
        organization_id=UUID(str(payload["org_id"])),
    )
