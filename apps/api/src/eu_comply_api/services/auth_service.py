from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eu_comply_api.config import Settings
from eu_comply_api.core.security import create_access_token, verify_password
from eu_comply_api.db.models import ApiClientRecord, OrganizationRecord, UserRecord
from eu_comply_api.domain.models import ActorType, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def login_user(self, email: str, password: str) -> TokenResponse:
        user = await self._session.scalar(select(UserRecord).where(UserRecord.email == email))
        if user is None or not user.is_active:
            raise ValueError("Invalid user credentials.")
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid user credentials.")
        organization = await self._session.get(OrganizationRecord, user.organization_id)
        if organization is None:
            raise ValueError("User organization not found.")
        token, expires_in = create_access_token(
            self._settings,
            subject=str(user.id),
            actor_type=ActorType.USER,
            organization_id=organization.id,
            additional_claims={"email": user.email},
        )
        return TokenResponse(
            access_token=token,
            expires_in_seconds=expires_in,
            actor_type=ActorType.USER,
            organization={
                "id": organization.id,
                "slug": organization.slug,
                "name": organization.name,
            },
        )

    async def login_client(self, client_id: str, client_secret: str) -> TokenResponse:
        client = await self._session.scalar(
            select(ApiClientRecord).where(ApiClientRecord.client_id == client_id)
        )
        if client is None or not client.is_active:
            raise ValueError("Invalid client credentials.")
        if not verify_password(client_secret, client.client_secret_hash):
            raise ValueError("Invalid client credentials.")
        organization = await self._session.get(OrganizationRecord, client.organization_id)
        if organization is None:
            raise ValueError("Client organization not found.")
        token, expires_in = create_access_token(
            self._settings,
            subject=str(client.id),
            actor_type=ActorType.API_CLIENT,
            organization_id=organization.id,
            additional_claims={"client_id": client.client_id, "scopes": client.scopes},
        )
        return TokenResponse(
            access_token=token,
            expires_in_seconds=expires_in,
            actor_type=ActorType.API_CLIENT,
            organization={
                "id": organization.id,
                "slug": organization.slug,
                "name": organization.name,
            },
        )
