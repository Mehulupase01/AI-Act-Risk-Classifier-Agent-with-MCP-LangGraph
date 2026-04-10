# Release Checklist

## Pre-Release

- Confirm `uv run --directory apps/api ruff check .` passes.
- Confirm `uv run --directory apps/api pytest` passes.
- Confirm `uv run --directory apps/api python -m eu_comply_api.tools.run_benchmarks` passes.
- Confirm `npm --prefix apps/web run lint` passes.
- Confirm `npm --prefix apps/web run build` passes.
- Confirm `uv run --directory apps/api alembic upgrade head` works on a clean verification database.
- Confirm `uv run --directory apps/api python -m eu_comply_api.tools.seed_policy` works on the verification database.

## Product Checks

- Create a case through the web console.
- Upload and process at least one artifact.
- Run an assessment and a governed workflow.
- Record a review decision.
- Export JSON report, Markdown report, and ZIP audit pack.
- Trigger reassessment manually and through a connector sync.
- Validate MCP endpoints for policy, dossier, and assessment surfaces.

## Operational Checks

- Confirm readiness is `ok`.
- Confirm `/api/v1/metrics` returns org-scoped counters with an authenticated token.
- Confirm backup script runs successfully.
- Confirm restore procedure is documented for the target environment.

## Release Artifacts

- Update [README.md](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/README.md).
- Update [docs/verification.md](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/docs/verification.md).
- Update [docs/HANDOFF.md](/D:/Mehul-Projects/AI%20Act%20Risk%20Classifier%20Agent%20with%20MCP%20+%20LangGraph/docs/HANDOFF.md).
- Update release notes or GitHub release summary with verified commit hashes and commands.
