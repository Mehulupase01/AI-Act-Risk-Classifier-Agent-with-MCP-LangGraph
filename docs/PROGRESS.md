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
- Artifact intake and document intelligence foundation completed with upload/process APIs, local artifact storage, parser/chunking flows, extracted fact persistence, and Alembic migration `005_artifact_intelligence_foundation`.
- Deterministic assessment and obligation engine foundation completed with assessment persistence, case-level assessment APIs, fact merging, conflict-aware outcomes, and Alembic migration `006_assessment_runs`.
- LangGraph workflow and governed review foundation completed with workflow-run APIs, persisted workflow state, review routing, and Alembic migration `007_workflow_runs`.

## In Progress

- Operator interfaces and review surfaces

## Verified

- `uv run --directory apps/api ruff check .`
- `uv run --directory apps/api pytest` -> `22 passed`
- `npm run check`
- `uv run --directory apps/api alembic upgrade head` against a clean SQLite verification database through `007_workflow_runs`
- `uv run --directory apps/api python -m eu_comply_api.tools.seed_policy`

## Pending

- MCP servers
- Reporting, benchmarks, hardening, release
