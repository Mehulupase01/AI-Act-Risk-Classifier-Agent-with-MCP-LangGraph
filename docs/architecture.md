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
  - org-scoped runtime configuration
  - provider discovery and model discovery plumbing
  - seeded policy source access
  - policy snapshot listing and snapshot detail access
  - normalized legal fragment storage tied to snapshots and sources
  - rule-pack list/detail APIs and deterministic service-level evaluation
- The current frontend surface includes the branded landing page and the first analyst-console route skeleton.

## Immediate Architecture Focus

- begin artifact and document intake on top of the case registry foundation
- transform uploaded evidence into normalized facts for later rule execution
- connect the rule-pack substrate to real case data through a deterministic assessment service
