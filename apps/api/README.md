# EU-Comply API

FastAPI control plane for the EU-Comply platform.

## Commands

```powershell
uv sync --extra dev
uv run alembic upgrade head
uv run python -m eu_comply_api.tools.seed_policy
uv run python -m eu_comply_api.tools.run_benchmarks
uv run uvicorn eu_comply_api.main:app --reload --app-dir src
uv run pytest
```

## Container

Build from the repo root:

```powershell
docker build -f apps/api/Dockerfile .
```
