# Execução somente do Agente (pt-BR)

Este compose sobe apenas o container do agente para testes locais.

## Pré-requisitos
- Defina as variáveis de ambiente conforme seu cenário:
  - `PLC_IP`, `DB_NUMBER`, `DB_SIZE`
  - `OUTPUT_MODE` (stdout|mqtt|http)
  - `METRICS_PORT` (ex.: 9108)
  - `TENANT_ID`, `PLC_ID` (opcionais)

## Subir o compose
```powershell
# Windows PowerShell
$env:PLC_IP="192.168.0.121"; $env:DB_NUMBER="500"; $env:DB_SIZE="14"; $env:OUTPUT_MODE="stdout"; $env:METRICS_PORT="9108"; $env:TENANT_ID="clienteA"; $env:PLC_ID="linha1_prensa"
docker compose -f compose.agent-only.yml up --build
```

O agente expõe o endpoint de métricas em `http://localhost:9108/metrics` e o dashboard simples em `http://localhost:9108/`.

## Roteamento por tópico MQTT
No `config.yaml`, você pode definir:
```
output:
  mode: mqtt
  mqtt:
    topic: "plc/${TENANT_ID}/${PLC_ID}"
```
O Telegraf está configurado para consumir `plc/#` e promover `tenant_id`/`plc_id` do JSON publicados pelo agente como tags no Influx.
Além disso, se o JSON não tiver essas chaves, o Telegraf deriva `tenant_id` e `plc_id` a partir do próprio tópico (`topic_tag` + `processors.regex`) quando o padrão do tópico for `plc/<tenant>/<plc>`.
