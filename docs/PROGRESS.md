# Progress

## Completed

- Master plan defined for flagship execution.
- Monorepo directory structure created.
- Root repo foundation completed: workspace scripts, Docker Compose, CI, continuity docs, and baseline README.
- Next.js analyst workbench foundation completed with a branded landing page and initial `/cases` route.
- FastAPI control plane foundation completed with health, auth, and runtime endpoints.
- Persistence/auth/tenant/audit foundation completed with SQLAlchemy models, session handling, bootstrap defaults, and Alembic migration `001_foundation`.
- Provider-agnostic runtime gateway completed for `OpenRouter` and `Ollama`.
- Policy corpus and snapshot foundation completed with seeded sources, snapshots, normalized norm fragments, detail APIs, reusable loader service, and migrations through `003_norm_fragments`.
- Deterministic rule-pack foundation completed with fixture-backed rule definitions, list/detail APIs, and service-level evaluation tests.
- Case registry and dossier foundation completed with CRUD APIs and Alembic migration `004_cases_and_dossiers`.

## In Progress

- Document and artifact intake foundation

## Verified

- `uv run --directory apps/api ruff check .`
- `uv run --directory apps/api pytest` -> `16 passed`
- `npm run check`
- `uv run --directory apps/api alembic upgrade head` against a clean SQLite verification database through `004_cases_and_dossiers`
- `uv run --directory apps/api python -m eu_comply_api.tools.seed_policy`

## Pending

- Artifact upload and document intake
- Extraction pipeline
- Deterministic assessment core
- LangGraph workflow
- MCP servers
- Reporting, benchmarks, hardening, release
