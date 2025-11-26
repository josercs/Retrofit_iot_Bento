# Diagnóstico: Sem dados no Grafana

Este guia ajuda a identificar e corrigir rapidamente problemas quando os dashboards mostram "No data".

## 1) Verificar serviços

- Listar status

```powershell
# Na pasta plc-mirror
docker compose ps
```

Esperado: `influxdb (healthy)`, `collector (healthy)`, `mosquitto (Up)`, `telegraf (Up)`, `grafana (Up)`.

## 2) Conferir Telegraf

- Logs recentes
```powershell
docker logs telegraf --tail 80
```

Sem erros. Se houver mensagens como "error loading config" ou 404 para bucket ausente, siga os próximos passos.

- Arquivo de saída (debug) para ver o que está sendo gerado:
```powershell
docker exec telegraf sh -lc "tail -n 20 /tmp/telegraf_out.lp"
```
Deve aparecer `s7_db1` e `prometheus` com tags `ip`, `db` e `topic`.

## 3) Buckets do InfluxDB

- Listar buckets:
```powershell
docker exec influxdb influx bucket list --org planta --token $Env:INFLUX_TOKEN
```
Deve existir `processo` e `processo_raw`.

- Se `processo_raw` não existir, criar:
```powershell
docker exec influxdb influx bucket create -n processo_raw -o planta --token $Env:INFLUX_TOKEN
```

## 4) Teste de dados recentes

- Verifique rapidamente se há escrita (o Telegraf logará `Wrote batch of 32 metrics`).
- No Grafana, garanta range de tempo em "Last 15 minutes" e variáveis (ip/db) em "All".

## 5) Identidade (tenant/plc)

- O agente publica no tópico definido em `config.yaml` (ex.: `plc/${TENANT_ID}/${PLC_ID}`).
- Se placeholders não forem resolvidos, o agente usa `plc/db1` e o Telegraf não derivará `tenant_id`/`plc_id` do tópico.
- Para forçar, defina no Compose (já provisionado):
  - `TENANT_ID=tenant01`
  - `PLC_ID=linha1_prensa`

## 6) Erros comuns e soluções

- Telegraf reiniciando: sintaxe de `processors.override` ou `regex` — já corrigido no repo.
- `the path "tenant_id" doesn't exist`: agora tratado como campo opcional; não é erro.
- `bucket \"processo_raw\" not found`: criar o bucket (passo 3).
- Sem dados nos painéis: aguarde ~30s, ajuste o período do dashboard e confirme variáveis em "All".

## 7) Comandos úteis

```powershell
# Logs dos principais serviços
docker logs telegraf --tail 120
docker logs influxdb --tail 120
docker logs grafana --tail 120

# Buckets e org
docker exec influxdb influx org list --token $Env:INFLUX_TOKEN
docker exec influxdb influx bucket list --org planta --token $Env:INFLUX_TOKEN

# Reiniciar apenas o Telegraf após mudanças
docker compose restart telegraf
```

## 8) Onde ficam as configs

- Telegraf: `infra/telegraf/telegraf.conf`
- Datasource Grafana: `infra/grafana/provisioning/datasources/ds.yml`
- Dashboards Grafana: `infra/grafana/provisioning/dashboards/`
- Agente/Config: `src/agent.py`, `config.yaml`
