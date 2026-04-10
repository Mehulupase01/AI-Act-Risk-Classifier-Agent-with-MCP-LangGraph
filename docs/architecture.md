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

- Foundation scaffolding is being built.
- Runtime abstraction is being implemented before any provider-specific logic is allowed into workflows.

## Immediate Architecture Focus

- org-scoped persistence
- auth and audit foundations
- runtime control service
- OpenRouter + Ollama adapters
