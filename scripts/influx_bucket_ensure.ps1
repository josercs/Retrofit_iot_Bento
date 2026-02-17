param(
  [string]$HostUrl = "http://localhost:8086",
  [string]$Username = "admin",
  [string]$Password = "admin123",
  [string]$OrgName = "planta",
  [string]$BucketName = "processo",
  [string]$Retention = "30d"
)

$ErrorActionPreference = 'Stop'

function Get-Session {
  $basic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$Username`:$Password"))
  $headers = @{ Authorization = "Basic $basic" }
  $null = Invoke-WebRequest -Method Post -Uri "$HostUrl/api/v2/signin" -Headers $headers -SessionVariable session
  return $session
}

function Get-OrgId($session, $orgName) {
  $resp = Invoke-WebRequest -Method Get -Uri "$HostUrl/api/v2/orgs?org=$orgName" -WebSession $session
  $json = $resp.Content | ConvertFrom-Json
  if (-not $json.orgs -or $json.orgs.Count -eq 0) { throw "Org '$orgName' não encontrada" }
  return $json.orgs[0].id
}

function Get-Bucket($session, $bucketName, $orgId) {
  $resp = Invoke-WebRequest -Method Get -Uri "$HostUrl/api/v2/buckets?name=$bucketName&orgID=$orgId" -WebSession $session
  $json = $resp.Content | ConvertFrom-Json
  if (-not $json.buckets) { return $null }
  return ($json.buckets | Where-Object { $_.name -eq $bucketName } | Select-Object -First 1)
}

function Create-Bucket($session, $bucketName, $orgId, $retention) {
  $retentionRules = @()
  if ($retention -and $retention -ne "0") {
    # Convert retention like 30d to seconds (rough approximation: d->86400, h->3600, m->60)
    if ($retention -match '^(\d+)d$') { $secs = [int]$Matches[1] * 86400 }
    elseif ($retention -match '^(\d+)h$') { $secs = [int]$Matches[1] * 3600 }
    elseif ($retention -match '^(\d+)m$') { $secs = [int]$Matches[1] * 60 }
    else { $secs = 0 }
    if ($secs -gt 0) { $retentionRules = @(@{ type = "expire"; everySeconds = $secs }) }
  }
  $body = @{ name = $bucketName; orgID = $orgId; retentionRules = $retentionRules } | ConvertTo-Json -Depth 5
  $resp = Invoke-WebRequest -Method Post -Uri "$HostUrl/api/v2/buckets" -WebSession $session -ContentType 'application/json' -Body $body
  return $resp.Content | ConvertFrom-Json
}

Write-Host "[1/3] Autenticando no InfluxDB..." -ForegroundColor Cyan
$session = Get-Session

Write-Host "[2/3] Verificando Org e Bucket..." -ForegroundColor Cyan
$orgId = Get-OrgId -session $session -orgName $OrgName
$bucket = Get-Bucket -session $session -bucketName $BucketName -orgId $orgId

if ($bucket) {
  Write-Host "Bucket '$BucketName' já existe (id=$($bucket.id))." -ForegroundColor Green
} else {
  Write-Host "Bucket '$BucketName' não existe. Criando..." -ForegroundColor Yellow
  $created = Create-Bucket -session $session -bucketName $BucketName -orgId $orgId -retention $Retention
  Write-Host "Criado bucket: id=$($created.id) name=$($created.name)" -ForegroundColor Green
}

Write-Host "[3/3] Concluído." -ForegroundColor Green
