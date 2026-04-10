# Verification

## Verified Commands

```powershell
uv run --directory apps/api ruff check .
uv run --directory apps/api pytest
npm run lint
npm run build
$env:EU_COMPLY_DATABASE_URL='sqlite+aiosqlite:///D:/Mehul-Projects/AI Act Risk Classifier Agent with MCP + LangGraph/apps/api/alembic-verify.db'
uv run --directory apps/api alembic upgrade head
uv run --directory apps/api python -m eu_comply_api.tools.seed_policy
```

## Current Verification State

- API lint passes.
- API tests pass: `32 passed`.
- Web lint passes in `apps/web`.
- The Next.js analyst console builds cleanly in production mode.
- Alembic upgrades cleanly through `009_connector_reassessment_foundation` on a fresh verification database.
- Policy fixture synchronization CLI runs successfully against a migrated database.
- The live analyst console review and export code passes both lint and production build validation.
- Mounted MCP server tests now pass against the FastAPI app using streamable HTTP transport.
- Connector sync and reassessment route tests pass, including auto-processed workflow creation and unsupported-event rejection paths.

## Notes

- SQLite verification now runs cleanly through the connector and reassessment migration path.
