param(
  [string]$HostUrl = "http://localhost:8086",
  [string]$Username = "admin",
  [string]$Password = "admin123",
  [string]$OrgName = "planta",
  [string]$BucketName = "processo",
  [string]$Since = "-10m",
  [int]$Limit = 10
)

$ErrorActionPreference = 'Stop'

function Get-InfluxSession($hostUrl, $user, $pass) {
  $basic = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$user`:$pass"))
  $headers = @{ Authorization = "Basic $basic" }
  $null = Invoke-WebRequest -Method Post -Uri "$hostUrl/api/v2/signin" -Headers $headers -SessionVariable websession
  return $websession
}

$session = Get-InfluxSession -hostUrl $HostUrl -user $Username -pass $Password

$flux = @"
from(bucket: \"$BucketName\")
  |> range(start: $Since)
  |> limit(n: $Limit)
"@

$headers = @{ 
  Accept = 'application/csv'
  'Content-Type' = 'application/vnd.flux'
}

$uri = "$HostUrl/api/v2/query?org=$OrgName"
$resp = Invoke-WebRequest -Method Post -Uri $uri -Headers $headers -Body $flux -WebSession $session

$lines = $resp.Content -split "`n" | Where-Object { $_ -and -not ($_ -like '#*') }
Write-Host "--- Amostra ($Limit linhas) ---" -ForegroundColor Cyan
$lines | Select-Object -First $Limit | ForEach-Object { Write-Host $_ }
Write-Host "--- Total linhas (sem comentários): $($lines.Count) ---" -ForegroundColor Cyan
