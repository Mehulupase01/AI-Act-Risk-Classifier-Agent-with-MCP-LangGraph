# Decisions

## Architecture

- Build as a hybrid platform: control plane API + analyst workbench + MCP interfaces.
- Keep the legal decision path deterministic and traceable.
- Separate `binding_law`, `official_guidance`, `proposal`, and `voluntary_code`.

## Runtime

- Use a dedicated LLM gateway instead of calling providers directly from workflows.
- Support `OpenRouter` for hosted inference and `Ollama` for local/self-host inference.
- Use native Ollama APIs for chat and embeddings.

## Delivery

- Close phases only when code, tests, docs, and verification notes agree.
