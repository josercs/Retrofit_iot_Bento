param(
  [string]$HostUrl = "http://localhost:3000"
)
$ErrorActionPreference = 'Stop'
try {
  $resp = Invoke-WebRequest -Uri "$HostUrl/api/health" -UseBasicParsing -TimeoutSec 5
  Write-Host "Grafana: $($resp.StatusCode) $($resp.StatusDescription)" -ForegroundColor Green
  Write-Host $resp.Content
} catch {
  Write-Host "Falha ao acessar $HostUrl/api/health: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}
