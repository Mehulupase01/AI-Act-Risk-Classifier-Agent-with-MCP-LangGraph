from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from eu_comply_api.config import Settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(value: str) -> str:
    return pwd_context.hash(value)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    settings: Settings,
    *,
    subject: str,
    actor_type: str,
    organization_id: UUID,
    additional_claims: dict[str, Any] | None = None,
) -> tuple[str, int]:
    expire_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = datetime.now(UTC) + expire_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "actor_type": actor_type,
        "org_id": str(organization_id),
        "exp": expires_at,
    }
    if additional_claims:
        payload.update(additional_claims)
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, int(expire_delta.total_seconds())


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid access token.") from exc
