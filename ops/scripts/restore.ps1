$ErrorActionPreference = "Stop"

param(
  [string]$ComposeFile = "ops/docker/compose.full.yml",
  [Parameter(Mandatory = $true)][string]$BackupDir
)

$sqlPath = Join-Path $BackupDir "eu_comply.sql"
$minioPath = Join-Path $BackupDir "minio-data.tar"

if (-not (Test-Path $sqlPath)) {
  throw "SQL backup not found at $sqlPath"
}

if (-not (Test-Path $minioPath)) {
  throw "MinIO backup not found at $minioPath"
}

Write-Host "Restoring Postgres database..."
Get-Content -Path $sqlPath |
  docker compose -f $ComposeFile exec -T postgres psql -U eu_comply -d eu_comply

Write-Host "Restoring MinIO object data..."
Get-Content -Encoding Byte -Path $minioPath |
  docker compose -f $ComposeFile exec -T minio sh -c "tar -C /data -xf -"

Write-Host "Restore completed from $BackupDir"
