# Verification

## Verified Commands

```powershell
uv run --directory apps/api ruff check .
uv run --directory apps/api pytest
npm run check
$env:EU_COMPLY_DATABASE_URL='sqlite+aiosqlite:///D:/Mehul-Projects/AI Act Risk Classifier Agent with MCP + LangGraph/apps/api/.tmp/alembic-verify.db'
$env:EU_COMPLY_AUTO_CREATE_SCHEMA='false'
uv run --directory apps/api alembic upgrade head
uv run --directory apps/api python -m eu_comply_api.tools.seed_policy
```

## Current Verification State

- API lint passes.
- API tests pass: `22 passed`.
- Root `npm run check` passes, including web lint/build and API import.
- Alembic upgrades cleanly through `007_workflow_runs` on a fresh verification database.
- Policy fixture synchronization CLI runs successfully against a migrated database.

## Notes

- A transient `aiosqlite` deprecation warning appears during test execution in this environment but does not currently fail the suite.
