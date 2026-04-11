# Deployment Guide

## Deployment Modes

EU-Comply currently supports two practical deployment modes:

- local development with the root `docker-compose.yml` plus local app processes
- containerized full-stack deployment with [compose.full.yml](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/ops/docker/compose.full.yml)

## Required Services

- Postgres
- Redis
- artifact storage path or object store
- optional hosted LLM provider through OpenRouter
- optional local LLM provider through Ollama

## API Container

Build from [apps/api/Dockerfile](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/apps/api/Dockerfile).

Important environment values:

- `EU_COMPLY_DATABASE_URL`
- `EU_COMPLY_REDIS_URL`
- `EU_COMPLY_ARTIFACT_STORAGE_PATH`
- `EU_COMPLY_BOOTSTRAP_ADMIN_PASSWORD`
- `EU_COMPLY_BOOTSTRAP_API_CLIENT_SECRET`
- `EU_COMPLY_OPENROUTER_API_KEY`
- `EU_COMPLY_OLLAMA_BASE_URL`

## Web Container

Build from [apps/web/Dockerfile](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/apps/web/Dockerfile).

The current analyst console lets operators point to the API URL from the UI, so no
mandatory runtime environment variable is required for basic use.

## Full Stack Compose

Run:

```powershell
docker compose -f ops/docker/compose.full.yml up --build
```

This starts:

- `postgres`
- `redis`
- `minio`
- `api`
- `web`

The API container applies Alembic migrations during startup before launching Uvicorn.

### Port Overrides

If default localhost ports are already in use, the compose file supports
environment-based overrides:

```powershell
$env:EU_COMPLY_API_PORT='8001'
$env:EU_COMPLY_WEB_PORT='3000'
docker compose -f ops/docker/compose.full.yml up -d
```

Supported overrides currently include:

- `EU_COMPLY_API_PORT`
- `EU_COMPLY_WEB_PORT`
- `EU_COMPLY_POSTGRES_PORT`
- `EU_COMPLY_REDIS_PORT`
- `EU_COMPLY_MINIO_PORT`
- `EU_COMPLY_MINIO_CONSOLE_PORT`

## Post-Deploy Validation

Run these checks after deployment:

```powershell
curl http://127.0.0.1:8000/api/v1/health/liveness
curl http://127.0.0.1:8000/api/v1/health/readiness
```

Then authenticate and confirm:

- case creation works
- artifact upload and processing works
- assessment and workflow runs work
- review recording works
- report and audit-pack exports work
- `/api/v1/metrics` returns data for an authenticated token

## Backup And Restore

- Backup: [backup.ps1](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/ops/scripts/backup.ps1)
- Restore: [restore.ps1](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/ops/scripts/restore.ps1)

Current backup coverage:

- Postgres SQL dump
- MinIO object-store tar archive

## Release Advice

- Set strong bootstrap secrets before non-local deployment.
- Disable `EU_COMPLY_AUTO_CREATE_SCHEMA` in long-running environments and rely on Alembic.
- Use API client tokens for automation and metrics scraping instead of user credentials.
- Keep OpenRouter optional so self-host deployments can run with Ollama only.
