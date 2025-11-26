param(
  [string]$HostUrl = "http://localhost:8086",
  [string]$Username = "admin",
  [string]$Password = "admin123",
  [string]$OrgName = "planta",
  [string]$BucketName = "processo",
  [string]$Description = "telegraf-write"
)

$ErrorActionPreference = 'Stop'

function Get-SessionCookie {
  $basic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$Username`:$Password"))
  $headers = @{ Authorization = "Basic $basic" }
  $resp = Invoke-WebRequest -Method Post -Uri "$HostUrl/api/v2/signin" -Headers $headers -SessionVariable websession
  return $websession
}

function Get-OrgId($session, $orgName) {
  $resp = Invoke-WebRequest -Method Get -Uri "$HostUrl/api/v2/orgs?org=$orgName" -WebSession $session
  $json = $resp.Content | ConvertFrom-Json
  if (-not $json.orgs -or $json.orgs.Count -eq 0) { throw "Org '$orgName' não encontrada" }
  return $json.orgs[0].id
}

function Get-BucketId($session, $bucketName, $orgId) {
  $resp = Invoke-WebRequest -Method Get -Uri "$HostUrl/api/v2/buckets?name=$bucketName&orgID=$orgId" -WebSession $session
  $json = $resp.Content | ConvertFrom-Json
  if (-not $json.buckets -or $json.buckets.Count -eq 0) { throw "Bucket '$bucketName' não encontrado" }
  return $json.buckets[0].id
}

function Create-WriteToken($session, $orgId, $bucketId, $desc) {
  $body = @{ description = $desc; orgID = $orgId; permissions = @(@{ action = "write"; resource = @{ type = "buckets"; orgID = $orgId; id = $bucketId } }) } | ConvertTo-Json -Depth 6
  $resp = Invoke-WebRequest -Method Post -Uri "$HostUrl/api/v2/authorizations" -WebSession $session -ContentType 'application/json' -Body $body
  $json = $resp.Content | ConvertFrom-Json
  return $json.token
}

function Update-DotEnv($token) {
  $envPath = Join-Path (Get-Location) ".env"
  if (Test-Path $envPath) { Copy-Item $envPath "$envPath.bak" -Force }
  $lines = @()
  if (Test-Path $envPath) { $lines = Get-Content $envPath }
  $found = $false
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^INFLUX_TOKEN\s*=') {
      $lines[$i] = "INFLUX_TOKEN=$token"
      $found = $true
    }
  }
  if (-not $found) { $lines += "INFLUX_TOKEN=$token" }
  Set-Content -Path $envPath -Value $lines -Encoding UTF8
}

Write-Host "[1/4] Autenticando no InfluxDB..." -ForegroundColor Cyan
$session = Get-SessionCookie

Write-Host "[2/4] Coletando IDs de org e bucket..." -ForegroundColor Cyan
$orgId = Get-OrgId -session $session -orgName $OrgName
$bucketId = Get-BucketId -session $session -bucketName $BucketName -orgId $orgId

Write-Host "[3/4] Criando token de escrita..." -ForegroundColor Cyan
$token = Create-WriteToken -session $session -orgId $orgId -bucketId $bucketId -desc $Description
if (-not $token) { throw "Falha ao criar token" }
$masked = $token.Substring(0,6) + '...' + $token.Substring($token.Length-4)
Write-Host "Token criado: $masked" -ForegroundColor Green

Write-Host "[4/4] Atualizando .env (INFLUX_TOKEN)" -ForegroundColor Cyan
Update-DotEnv -token $token

Write-Host "Concluído. Reinicie Telegraf e Grafana para aplicar o token." -ForegroundColor Green
