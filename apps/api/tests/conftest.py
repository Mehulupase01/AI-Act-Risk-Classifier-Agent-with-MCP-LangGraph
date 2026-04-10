from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from eu_comply_api.config import get_settings
from eu_comply_api.db.session import reset_session_state
from eu_comply_api.main import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    db_path = tmp_path / "eu_comply_test.db"
    monkeypatch.setenv("EU_COMPLY_DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("EU_COMPLY_AUTO_CREATE_SCHEMA", "true")
    monkeypatch.setenv("EU_COMPLY_OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("EU_COMPLY_BOOTSTRAP_ADMIN_PASSWORD", "change-me-now")
    monkeypatch.setenv("EU_COMPLY_BOOTSTRAP_API_CLIENT_SECRET", "eu-comply-dev-secret")
    monkeypatch.setenv("EU_COMPLY_ARTIFACT_STORAGE_PATH", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    reset_session_state()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    reset_session_state()
