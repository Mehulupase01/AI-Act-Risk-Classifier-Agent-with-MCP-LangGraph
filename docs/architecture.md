# Architecture

## System Summary

EU-Comply is an AI governance and EU AI Act assessment platform with:

- FastAPI control plane
- Next.js analyst workbench
- deterministic policy engine
- LangGraph workflow orchestration
- provider-agnostic LLM gateway
- first-party MCP servers
- audit and export surfaces

## Current State

- Foundation, auth, and runtime scaffolding are implemented and verified.
- The current backend surface includes:
  - health and readiness endpoints
  - user and API-client auth flows
  - case registry and dossier CRUD endpoints
  - artifact upload, retrieval, and processing endpoints
  - org-scoped runtime configuration
  - provider discovery and model discovery plumbing
  - seeded policy source access
  - policy snapshot listing and snapshot detail access
  - normalized legal fragment storage tied to snapshots and sources
  - rule-pack list/detail APIs and deterministic service-level evaluation
  - extracted fact persistence and conflict marking
- The current frontend surface includes the branded landing page and the first analyst-console route skeleton.

## Immediate Architecture Focus

- connect dossier and extracted artifact facts into a deterministic assessment engine
- persist assessment runs, decisions, and obligations
- keep the next phase centered on explainable case-level decisions rather than transient evaluations
