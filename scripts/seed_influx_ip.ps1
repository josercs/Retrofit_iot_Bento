param(
  [string]$HostUrl = "http://localhost:8086",
  [string]$OrgName = "planta",
  [string]$BucketName = "processo",
  [string]$Ip = "192.168.0.121",
  [int]$Db = 1
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

# Write a minimal point so tagValues picks up ip/db
$ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$line = "s7_db500,ip=$Ip,db=$Db seed=1i $($ts*1000000000)"

$headers = @{ Authorization = "Token $token" }
$writeUri = "$HostUrl/api/v2/write?org=$OrgName&bucket=$BucketName&precision=ns"
$resp = Invoke-WebRequest -Method Post -Uri $writeUri -Headers $headers -Body $line -ContentType 'text/plain'
Write-Host "Seed write status: $($resp.StatusCode)" -ForegroundColor Cyan
Write-Host "OK: ip=$Ip db=$Db" -ForegroundColor Green
