param(
  [string]$Ip = '192.168.0.121'
)
$ErrorActionPreference='Stop'
Write-Host "[PING] $Ip" -ForegroundColor Cyan
try {
  $null = ping.exe -n 2 $Ip 2>$null
  if ($LASTEXITCODE -eq 0) {
    Write-Host "Ping OK" -ForegroundColor Green
  } else {
    Write-Host "Ping sem resposta" -ForegroundColor Yellow
  }
} catch { Write-Host "Ping falhou: $_" -ForegroundColor Red }

Write-Host "[TCP:102] Testando porta S7" -ForegroundColor Cyan
try {
  $client = New-Object System.Net.Sockets.TcpClient
  $iar = $client.BeginConnect($Ip,102,$null,$null)
  if(-not $iar.AsyncWaitHandle.WaitOne(3000)) { throw 'Timeout 3s' }
  $client.EndConnect($iar)
  Write-Host 'Porta 102 conectou (possível S7 disponível).' -ForegroundColor Green
  $client.Close()
} catch { Write-Host "Falha porta 102: $_" -ForegroundColor Yellow }

Write-Host "Concluído." -ForegroundColor Cyan
