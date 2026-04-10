$ErrorActionPreference = "Stop"

Write-Host "Installing API dependencies..."
uv sync --directory apps/api --extra dev

Write-Host "Running API tests..."
uv run --directory apps/api pytest

Write-Host "Linting web..."
npm --prefix apps/web run lint

Write-Host "Building web..."
npm --prefix apps/web run build

Write-Host "Validating API import..."
uv run --directory apps/api python -c "import eu_comply_api"
