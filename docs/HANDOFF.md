# Handoff

## Current Status

- Phase 1 foundation is complete and verified.
- Phase 2 persistence/auth/tenant/audit spine is complete and verified.
- Phase 3 runtime control and LLM gateway foundation is complete and verified.
- Phase 4 policy corpus and snapshot foundation is complete at the current foundation layer.
- Phase 5 rule-pack foundation is complete and verified.
- Phase 6 case registry and dossier foundation is complete and verified.
- Phase 7 artifact intake and document intelligence foundation is complete and verified.
- Phase 8 deterministic assessment and obligation engine foundation is complete and verified.
- Phase 9 LangGraph workflow and governed review foundation is complete and verified.
- Phase 10 operator interface foundation is complete and verified.
- Phase 11 reviewer approval and reporting foundation is complete and verified.
- Phase 12 integration foundation is complete and verified.
- Phase 13 audit-pack expansion is complete and verified.
- Phase 14 evaluation and hardening foundation is complete and verified.
- Phase 15 release packaging is complete and verified end to end.

## Next Critical Steps

1. Expand the deterministic rule library beyond the current baseline coverage and keep the policy snapshot fixtures in step with that growth.
2. Grow the benchmark and adversarial corpus beyond the current five-case golden set before making broader legal-performance claims.
3. Keep deployment, release, and architecture docs aligned with any future product-depth work.

## Active Local Deployment

- The compose stack is currently running locally.
- Web: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8001`
- The API port is overridden because host port `8000` is already occupied on this machine.
- Browser-origin requests from the analyst console are now allowed by the API's localhost CORS configuration.
- The analyst console now accepts either a host-only API URL or a full `/api/v1` URL.

## Last Verified Commands

```powershell
uv run --directory apps/api ruff check .
uv run --directory apps/api pytest
npm run lint
npm run build
$env:EU_COMPLY_DATABASE_URL='sqlite+aiosqlite:///D:/Mehul-Projects/AI Act Risk Classifier Agent with MCP + LangGraph/apps/api/alembic-verify.db'
uv run --directory apps/api alembic upgrade head
uv run --directory apps/api python -m eu_comply_api.tools.seed_policy
uv run --directory apps/api python -m eu_comply_api.tools.run_benchmarks
docker build -f apps/api/Dockerfile -t eu-comply-api:verify .
docker build -f apps/web/Dockerfile -t eu-comply-web:verify .
docker compose -f ops/docker/compose.full.yml build
docker compose -f ops/docker/compose.full.yml config
```
