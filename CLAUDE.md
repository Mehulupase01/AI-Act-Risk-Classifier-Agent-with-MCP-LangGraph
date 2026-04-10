# EU-Comply Working Memory

## Project Identity

- Project: `A1 EU-Comply`
- Product shape: enterprise AI governance and EU AI Act assessment platform
- Repo mode: flagship, production-grade, phase-wise delivery

## Current Commands

```powershell
docker compose up -d
uv run --directory apps/api pytest
uv run --directory apps/api uvicorn eu_comply_api.main:app --reload --app-dir src
npm --prefix apps/web run dev
npm run check
```

## Active Decisions

- Legal decisioning must stay deterministic and policy-driven.
- LLM usage must remain provider-agnostic.
- `Ollama` is first-class for local/self-host deployments.
- `OpenRouter` is first-class for hosted deployments.
- RAG is helper-only and never the legal source of truth.

## Update Rule

Update this file after each verified phase closure together with:

- `docs/HANDOFF.md`
- `docs/PROGRESS.md`
- `docs/DECISIONS.md`
- `docs/architecture.md`
- `docs/verification.md`
