# EU-Comply Working Memory

## Project Identity

- Project: `A1 EU-Comply`
- Product shape: enterprise AI governance and EU AI Act assessment platform
- Repo mode: flagship, production-grade, phase-wise delivery
- Active branch: `main`

## Current Commands

```powershell
docker compose up -d
uv run --directory apps/api pytest
uv run --directory apps/api alembic upgrade head
uv run --directory apps/api uvicorn eu_comply_api.main:app --reload --app-dir src
uv run --directory apps/api python -m eu_comply_api.tools.seed_policy
uv run --directory apps/api python -m eu_comply_api.tools.run_benchmarks
npm --prefix apps/web run dev
npm --prefix apps/web run lint
npm --prefix apps/web run build
```

## Active Decisions

- Legal decisioning must stay deterministic and policy-driven.
- LLM usage must remain provider-agnostic.
- `Ollama` is first-class for local/self-host deployments.
- `OpenRouter` is first-class for hosted deployments.
- RAG is helper-only and never the legal source of truth.
- Phase closure requires code, tests, migrations, and continuity docs to agree.

## Current Execution Truth

- Phase 1 foundation is verified.
- Phase 2 persistence/auth/tenant/audit foundation is verified.
- Phase 3 runtime control with `OpenRouter` and `Ollama` adapters is verified.
- Phase 4 policy corpus work has started with seeded policy sources, a baseline policy snapshot, normalized norm fragments, policy detail APIs, tests, and Alembic migration support.
- Phase 5 deterministic rule-pack foundation is verified with fixture-backed packs, list/detail APIs, and service-level evaluation tests.
- Phase 6 case registry and dossier foundation is verified with CRUD APIs, migrations, and tests.
- Phase 7 artifact intake and document intelligence foundation is verified with upload/process APIs, parser and chunking flows, extracted fact persistence, and conflict marking.
- Phase 8 deterministic assessment and obligation engine foundation is verified with persisted assessment runs, case-level assessment APIs, fact merging, and obligation mapping.
- Phase 9 LangGraph workflow and governed review foundation is verified with workflow-run APIs, persisted workflow state, and review gating for sensitive or conflicted outcomes.
- Phase 10 operator interface foundation is verified with a live analyst console that can sign in, create cases, upload/process evidence, and trigger assessments and workflows.
- Phase 11 reviewer approval and reporting foundation is verified with approval-ledger persistence, review/report APIs, approval-aware case and workflow state updates, and live console actions for recording reviews and exporting reports.
- Phase 12 integration foundation is verified with first-party MCP servers, persisted connector registry APIs, auditable connector sync runs, and case-linked reassessment triggers that can optionally auto-run governed workflows.
- Phase 13 audit-pack expansion is verified with bundled ZIP audit exports, policy fragment inclusion, reassessment history in report artifacts, MCP audit-pack access, and a live console action for exporting the archive.
- Phase 14 evaluation and hardening is verified with a golden benchmark fixture and CLI, org-scoped metrics output, and readiness checks for database, bootstrap org, policy snapshots, and artifact storage.
- Phase 15 release packaging is fully verified with API/web Dockerfiles, full-stack compose, env templates, backup and restore scripts, deployment docs, and a flagship README. Direct API and web Docker image builds now pass, and the full compose build is verified against a live Docker daemon.
- Localhost deployment is now verified end to end with the compose stack running successfully. The current local run uses `EU_COMPLY_API_PORT=8001` because port `8000` is already occupied on the host.
- Browser access from the analyst console to the local API is now verified after adding explicit localhost CORS handling for `127.0.0.1:3000` and `localhost:3000`.
- The analyst console now normalizes host-only API base URLs such as `http://127.0.0.1:8001` to the correct `/api/v1` path automatically.
- The analyst console now probes localhost API candidates and repairs stale saved base URLs during hydration so older `8000` local storage values do not keep the UI pointed at a dead port.

## Update Rule

Update this file after each verified phase closure together with:

- `docs/HANDOFF.md`
- `docs/PROGRESS.md`
- `docs/DECISIONS.md`
- `docs/architecture.md`
- `docs/verification.md`
