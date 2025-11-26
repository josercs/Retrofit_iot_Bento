$ErrorActionPreference = 'Stop'
Write-Host "Grafana PS:" -ForegroundColor Cyan
$ps = docker compose ps
$ps
Write-Host "--- Health API ---" -ForegroundColor Cyan
try {
  $resp = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -TimeoutSec 5 -UseBasicParsing
  Write-Host "Health: $($resp.StatusCode)" -ForegroundColor Green
  Write-Host $resp.Content
} catch {
  Write-Host "Health check falhou: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host "--- Recent logs ---" -ForegroundColor Cyan
try { docker compose logs grafana --tail 200 } catch {}
