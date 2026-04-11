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
- Artifact intake and document intelligence foundation completed with upload/process APIs, local artifact storage, parser/chunking flows, extracted fact persistence, and Alembic migration `005_artifact_intelligence`.
- Deterministic assessment and obligation engine foundation completed with assessment persistence, case-level assessment APIs, fact merging, conflict-aware outcomes, and Alembic migration `006_assessment_runs`.
- LangGraph workflow and governed review foundation completed with workflow-run APIs, persisted workflow state, review routing, and Alembic migration `007_workflow_runs`.
- Operator interface foundation completed with a live analyst console wired to backend auth, cases, artifacts, assessments, and workflows.
- Reviewer approval and reporting foundation completed with review decision persistence, report export APIs, approval-driven case/workflow state updates, live console review actions, and Alembic migration `008_review_decisions`.
- MCP, connector, and reassessment foundation completed with mounted first-party MCP servers, connector registry APIs, auditable sync runs, reassessment trigger APIs, and Alembic migration `009_connector_reassessment`.
- Audit-pack expansion completed with ZIP audit bundles, manifest generation, policy fragment exports, reassessment history capture, MCP audit-pack tooling, and analyst-console export actions.
- Evaluation and hardening foundation completed with a golden-case benchmark fixture, benchmark CLI, real readiness checks, and org-scoped metrics export.
- Release packaging completed with API/web Dockerfiles, full-stack compose, env templates, backup/restore scripts, deployment docs, release checklist, verified Docker image builds, verified compose build, and a flagship-level rewritten README.
- Localhost deployment completed successfully with the compose stack live and verified on host ports `3000` and `8001`.

## In Progress

- No active implementation gaps are open in the current flagship baseline.

## Verified

- `uv run --directory apps/api ruff check .`
- `uv run --directory apps/api pytest` -> `36 passed`
- `npm run lint` in `apps/web`
- `npm run build` in `apps/web`
- `uv run --directory apps/api alembic upgrade head` against a clean SQLite verification database through `009_connector_reassessment`
- `uv run --directory apps/api python -m eu_comply_api.tools.seed_policy` against the SQLite verification database
- `uv run --directory apps/api python -m eu_comply_api.tools.run_benchmarks` -> `accuracy: 1.0`
- `docker build -f apps/api/Dockerfile -t eu-comply-api:verify .`
- `docker build -f apps/web/Dockerfile -t eu-comply-web:verify .`
- `docker compose -f ops/docker/compose.full.yml build`
- `docker compose -f ops/docker/compose.full.yml config`

## Pending

- Broader legal coverage, larger benchmark depth, and expanded adversarial validation beyond the current baseline fixture set.
