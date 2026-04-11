# Decisions

## Architecture

- Build as a hybrid platform: control plane API + analyst workbench + MCP interfaces.
- Keep the legal decision path deterministic and traceable.
- Separate `binding_law`, `official_guidance`, `proposal`, and `voluntary_code`.

## Runtime

- Use a dedicated LLM gateway instead of calling providers directly from workflows.
- Support `OpenRouter` for hosted inference and `Ollama` for local/self-host inference.
- Use native Ollama APIs for chat and embeddings.

## Persistence And Verification

- Keep Alembic migrations in place even while local development also supports schema auto-create.
- Treat migration verification as part of phase closure, not an optional extra.
- Seed a baseline policy registry during bootstrap so later policy and rule-engine work has a stable foundation.
- Model policy knowledge as snapshots plus normalized fragments so later rule packs can use structured citations instead of raw retrieval alone.
- Introduce a reusable policy-loader service and CLI so policy synchronization is not trapped inside application startup.

## Product Structure

- Model case registry and system dossier storage as first-class backend entities before building extraction or assessment workflows on top.
- Keep the rule-pack substrate separate from case persistence so deterministic policy logic can evolve independently of intake UX.
- Keep artifact storage and parsing behind services so the storage backend can evolve without rewriting the API layer.
- Persist extracted facts and mark cross-artifact conflicts early so later review workflows have explicit disagreement signals.
- Persist assessment runs as first-class records with facts, hits, conflicts, and obligations so case history remains explainable.
- Prefer conservative `needs_more_information` outcomes when fact conflicts would undermine deterministic decision quality.
- Persist workflow runs separately from assessment runs so orchestration state and decision state remain distinguishable.
- Route prohibited and conflict-heavy outcomes into explicit review-required workflow states instead of pretending the machine run can close the case autonomously.
- Build the analyst console against live backend endpoints rather than inventing a separate frontend-only mock state model.
- Persist review decisions separately from machine-run records so the platform can distinguish human approval from machine output without mutating the underlying assessment history.
- Let approved reviews update case and workflow closure state while keeping the original machine assessment immutable for auditability.
- Generate exportable reports from persisted case, evidence, workflow, and review records rather than from transient frontend state.
- Mount first-party MCP servers inside the main FastAPI application and explicitly run their session managers from the root lifespan so streamable HTTP transport works reliably in tests and local development.
- Model enterprise integrations as tenant-scoped connector records plus auditable sync-run history instead of hiding external changes behind ad hoc webhook handlers.
- Persist reassessment triggers separately from workflow runs so external change events, manual requests, and workflow execution history remain distinguishable.
- Allow connector-driven reassessments to auto-run governed workflows, but keep review approval actions outside the MCP write surface.
- Generate audit packs as ZIP bundles with a manifest plus stable JSON/Markdown artifacts so reviews, evidence, and policy context can be shipped together without depending on live API state.
- Include referenced policy fragments and reassessment history in the audit archive so exported governance records stay traceable after external system changes.
- Keep benchmark fixtures in-repo and executable through a CLI so rule regressions can be checked without needing a live frontend or manual API exercise.
- Expose metrics as org-scoped authenticated Prometheus-style text instead of a public global endpoint so operational visibility does not leak cross-tenant counts.
- Make readiness checks exercise real dependencies such as database connectivity, seeded policy presence, and artifact storage writability rather than returning static configuration-only status.
- Package the web application with Next.js standalone output so the runtime container can stay small and deployment wiring remains straightforward.
- Keep Docker build context at the repo root so API fixtures, benchmark data, and shared assets remain available during image builds.
- Keep flagship documentation ambitious in depth but honest about baseline legal coverage so README quality never depends on inflated product claims.
- Keep Alembic revision identifiers within PostgreSQL-safe length bounds so containerized deployments do not fail on the default version-table column size.

## Delivery

- Close phases only when code, tests, docs, and verification notes agree.
