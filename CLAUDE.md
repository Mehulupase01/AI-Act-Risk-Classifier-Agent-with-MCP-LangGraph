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
npm --prefix apps/web run dev
npm run check
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

## Update Rule

Update this file after each verified phase closure together with:

- `docs/HANDOFF.md`
- `docs/PROGRESS.md`
- `docs/DECISIONS.md`
- `docs/architecture.md`
- `docs/verification.md`
