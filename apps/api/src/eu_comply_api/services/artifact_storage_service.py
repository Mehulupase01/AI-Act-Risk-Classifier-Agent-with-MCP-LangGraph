from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

from anyio import Path as AsyncPath

from eu_comply_api.config import Settings


class ArtifactStorageService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def write_artifact(
        self,
        organization_id: UUID,
        case_id: UUID,
        filename: str,
        payload: bytes,
    ) -> tuple[str, str]:
        sanitized_filename = self._sanitize_filename(filename)
        extension = Path(sanitized_filename).suffix
        stored_name = f"{uuid4().hex}{extension}"
        relative_path = os.path.join(str(organization_id), str(case_id), stored_name)
        absolute_path = self._resolve_absolute_path(relative_path)
        await absolute_path.parent.mkdir(parents=True, exist_ok=True)
        await absolute_path.write_bytes(payload)
        return relative_path.replace("\\", "/"), self._hash_payload(payload)

    async def read_artifact(self, relative_path: str) -> bytes:
        absolute_path = self._resolve_absolute_path(relative_path)
        return await absolute_path.read_bytes()

    def _resolve_absolute_path(self, relative_path: str) -> AsyncPath:
        root = Path(self._settings.artifact_storage_path).expanduser()
        if not root.is_absolute():
            root = (Path.cwd() / root).resolve()
        return AsyncPath(root / relative_path)

    def _sanitize_filename(self, filename: str) -> str:
        name = Path(filename).name.strip()
        return name or "artifact.bin"

    def _hash_payload(self, payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()
