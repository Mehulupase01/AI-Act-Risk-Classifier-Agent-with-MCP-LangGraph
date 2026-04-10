# EU-Comply

EU-Comply is a production-grade AI governance and EU AI Act assessment platform.
It is being built phase-by-phase from this repository as a flagship compendium
project, with deterministic policy logic, governed review workflows, first-party
MCP servers, and provider-agnostic LLM support for both OpenRouter and Ollama.

## Current Focus

The repository is under active implementation. The initial execution slice covers:

1. Monorepo foundation and local developer platform
2. Persistence, auth, tenancy, and audit foundations
3. Provider-agnostic LLM runtime control with OpenRouter and Ollama adapters

## Planned Structure

```text
apps/
  api/
  web/
packages/
  contracts/
  evaluation/
  mcp/
  policy/
fixtures/
ops/
docs/
```

## Short-Term Commands

```powershell
npm --prefix apps/web run dev
uv run --directory apps/api uvicorn eu_comply_api.main:app --reload --app-dir src
uv run --directory apps/api pytest
```
