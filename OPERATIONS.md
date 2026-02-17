# Operações do Pipeline Edge

## Buckets & Retenção
- processo: 30d (retenção configurada via compose).
- processo_raw: sem retenção (dados brutos).
- processo_1m: agregação 1m (365d).

## Criação de Buckets (executar dentro do container influxdb)
```powershell
# criar raw
docker compose exec influxdb influx bucket create --name processo_raw --org planta --retention 0
# criar 1m
docker compose exec influxdb influx bucket create --name processo_1m --org planta --retention 8760h
```

## Tarefa de Downsampling (Flux)
Exemplo para executar a cada 5m agregando últimos 5m:
```flux
option task = {name: "downsample_1m", every: 5m}
from(bucket: "processo_raw")
  |> range(start: -5m)
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> to(bucket: "processo_1m")
```
Criar tarefa:
```powershell
docker compose exec influxdb influx task create --org planta --file /tmp/downsample.flux
```
(Gravar o script em /tmp/downsample.flux dentro do container.)

## Alertas (conceitos)
1. Vibração Alta (AI_Vibracao > LIMIAR por 1m).
2. Corrente Fora de Faixa (AI_Corrente < MIN ou > MAX).
3. OEE Baixo (OEE < 60% por 5m).
4. Edge Off (edge_up ausente >30s).
5. Heartbeat Stale (sem novo heartbeat >2 intervalos de publicação).

## Escala
- Adicionar tag plc_id na publicação MQTT; Telegraf injeta se ausente.
- Manter tags restritas: ip, db, plc_id.
- Evitar booleanos como tags (manter como fields).

## Backup
- InfluxDB: snapshot do volume `influx-data` (VSS ou tar) semanal.
- Grafana: dashboards versionados (JSON no repositório).
- Tokens: guardar seguros em cofre (Vault/KMS).

## Segurança
- Rotação trimestral de INFLUX_TOKEN e TELEGRAF_MQTT_PASSWORD.
- Ativar TLS para Influx (reverse proxy caddy/nginx) se expor externamente.
- Menor privilégio: token somente escrita para Telegraf.

## Ajustes de Performance
- metric_batch_size: subir para 200 se volume >5k métricas/min.
- Intervalo Prometheus scrape: aumentar para 10s se CPU alta.
- Usar downsampling para consultas históricas (>7 dias).

## Monitorar
- `edge_up` e diferença entre timestamps para latência.
- Taxa de peças/min (derivative contador_bom).
- Qualidade: contador_bom/(contador_bom+contador_ruim).

## Rotina de Manutenção
- Segundas: verificar tarefas Flux (`influx task list`).
- Quartas: conferir crescimento de cardinalidade (`show series cardinality`).
- Sextas: testar restauração do snapshot recente.

## Próximos Melhoramentos
- Provisionar alertas via API do Grafana.
- Adicionar painel de latência de publicação (tempo entre leitura PLC e chegada no Influx).
- Exportar métricas para nuvem (opcional).

(Referências: PLANO_VIABILIDADE.md, MODELO_MULTI_LOCATARIOS.md, ESTRATEGIA_RETENCAO_DADOS.md, ESPECIFICACAO_API_PROVISIONAMENTO.md, ESPECIFICACAO_MOTOR_ALERTAS.md.)
