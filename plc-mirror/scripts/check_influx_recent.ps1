param(
  [string]$HostUrl = "http://localhost:8086",
  [string]$OrgName = "planta",
  [string]$BucketName = "processo",
  [string]$Since = "-10m"
)

$ErrorActionPreference = 'Stop'

function Get-EnvVarFromDotEnv($name) {
  $envPath = Join-Path (Get-Location) ".env"
  if (-not (Test-Path $envPath)) { throw ".env não encontrado" }
  $line = (Get-Content $envPath | Where-Object { $_ -match "^$name\s*=" } | Select-Object -First 1)
  if (-not $line) { return $null }
  return ($line -replace '^.+?=','').Trim()
}

$token = Get-EnvVarFromDotEnv -name 'INFLUX_TOKEN'
if (-not $token) { throw "INFLUX_TOKEN não encontrado no .env" }

$flux = @"
from(bucket: \"$BucketName\")
  |> range(start: $Since)
  |> limit(n: 10)
"@

$headers = @{ 
  Authorization = "Token $token"
  Accept = 'application/csv'
  'Content-Type' = 'application/vnd.flux'
}

$uri = "$HostUrl/api/v2/query?org=$OrgName"
$response = Invoke-WebRequest -Method Post -Uri $uri -Headers $headers -Body $flux

# Show a compact summary
$lines = $response.Content -split "`n" | Where-Object { $_ -and -not ($_ -like '#*') }
$sample = $lines | Select-Object -First 15
Write-Host "--- Amostra de 10 linhas ---" -ForegroundColor Cyan
$sample | ForEach-Object { Write-Host $_ }
Write-Host "--- Total linhas (sem comentários): $($lines.Count) ---" -ForegroundColor Cyan
