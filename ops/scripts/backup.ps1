$ErrorActionPreference = "Stop"

param(
  [string]$ComposeFile = "ops/docker/compose.full.yml",
  [string]$OutputDir = "backups"
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$targetDir = Join-Path $OutputDir $timestamp
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

Write-Host "Backing up Postgres database..."
docker compose -f $ComposeFile exec -T postgres pg_dump -U eu_comply -d eu_comply |
  Set-Content -Path (Join-Path $targetDir "eu_comply.sql")

Write-Host "Backing up MinIO object data..."
docker compose -f $ComposeFile exec -T minio sh -c "tar -C /data -cf - ." |
  Set-Content -Encoding Byte -Path (Join-Path $targetDir "minio-data.tar")

Write-Host "Backup completed at $targetDir"
