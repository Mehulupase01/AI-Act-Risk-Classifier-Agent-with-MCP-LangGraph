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
- API tests pass: `36 passed`.
- Web lint passes in `apps/web`.
- The Next.js analyst console builds cleanly in production mode.
- Alembic upgrades cleanly through `009_connector_reassessment_foundation` on a fresh verification database.
- Policy fixture synchronization CLI runs successfully against the migrated SQLite verification database.
- The benchmark CLI runs successfully against the in-repo golden fixture with `accuracy = 1.0`.
- The live analyst console review and export code passes both lint and production build validation.
- The full-stack compose file resolves successfully with `docker compose ... config`.
- Mounted MCP server tests now pass against the FastAPI app using streamable HTTP transport.
- Connector sync and reassessment route tests pass, including auto-processed workflow creation and unsupported-event rejection paths.
- Audit-pack export tests now pass, including ZIP manifest validation and bundled workspace/report artifacts.
- Readiness and metrics tests now pass, including org-scoped Prometheus-style output.

## Notes

- SQLite verification now runs cleanly through the connector and reassessment migration path.
- Direct Docker image builds could not be executed in this session because the local Docker daemon was unavailable.
