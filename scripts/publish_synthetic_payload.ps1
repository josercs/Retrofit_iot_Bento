param(
  [string]$Ip = '192.168.0.121',
  [int]$Db = 1
)
$ErrorActionPreference='Stop'
$payload = [ordered]@{ ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); ip=$Ip; db=$Db; values = @{ contador_bom = 0; contador_ruim = 0; maquina_ligada = 0 } } | ConvertTo-Json -Depth 5
Write-Host "Publicando payload sintético com ip=$Ip db=$Db" -ForegroundColor Cyan
docker compose exec -T collector sh -lc @"
python - <<'PY'
import json, time
import paho.mqtt.client as m
payload = json.loads('''$payload''')
c=m.Client(); c.username_pw_set('edge_agent','EdgeAgent!2025'); c.tls_set('/app/ca.crt'); c.connect('mosquitto',8883,60); c.loop_start();
c.publish('plc/db500', json.dumps(payload), qos=0)
time.sleep(0.4); c.loop_stop(); c.disconnect()
print('OK')
PY
"@
Write-Host "Concluído." -ForegroundColor Green
