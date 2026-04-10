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

## Delivery

- Close phases only when code, tests, docs, and verification notes agree.
