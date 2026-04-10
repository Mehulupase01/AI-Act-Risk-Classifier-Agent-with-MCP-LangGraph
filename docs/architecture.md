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
  - explicit review-decision APIs and approval-ledger persistence
  - exportable report generation across case, evidence, assessment, workflow, and review state
  - first-party MCP servers for policy, dossier, assessment, and reassessment access
  - tenant-scoped connector registry APIs with auditable sync-run history
  - case-linked reassessment triggers that can optionally auto-run governed workflows
  - ZIP audit-pack generation with manifest, workspace snapshot, policy snapshot, and referenced fragments
  - benchmark harness plus CLI-driven regression checks for deterministic rule behavior
  - authenticated org-scoped metrics and real readiness checks for runtime health
- The current frontend surface now includes:
  - sign-in against the live backend
  - case creation and selection
  - artifact upload and processing
  - assessment and workflow triggering
  - evidence and decision inspection in a single operator console
  - human review actions with approved outcome capture
  - JSON and Markdown report export from the live backend
  - ZIP audit-pack export from the live backend

## Immediate Architecture Focus

- finish release packaging and deployment guidance without weakening the deterministic core
- keep broadening benchmark, adversarial, and operations coverage as part of release validation
