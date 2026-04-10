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
  - case-level assessment run endpoints
  - workflow-run endpoints driven by LangGraph
  - org-scoped runtime configuration
  - provider discovery and model discovery plumbing
  - seeded policy source access
  - policy snapshot listing and snapshot detail access
  - normalized legal fragment storage tied to snapshots and sources
  - rule-pack list/detail APIs and deterministic service-level evaluation
  - extracted fact persistence and conflict marking
  - persisted assessment runs with obligation mapping
  - review-required workflow states for conflicted or prohibited outcomes
- The current frontend surface now includes:
  - sign-in against the live backend
  - case creation and selection
  - artifact upload and processing
  - assessment and workflow triggering
  - evidence and decision inspection in a single operator console
- The current frontend surface includes the branded landing page and the first analyst-console route skeleton.

## Immediate Architecture Focus

- add explicit reviewer actions and approval flows
- prepare reporting and export surfaces on top of persisted runs and approvals
- keep the operator console aligned with the expanding governance backend
