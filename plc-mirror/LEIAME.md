# Plataforma Edge PLC (snap7 + MQTT + Telegraf + InfluxDB + Grafana)

## 1. Visão Geral
Projeto para ler dados de PLC Siemens (S7) via DB (ex.: DB500), publicar medições JSON multi‑locatários em MQTT com TLS e ingestão por Telegraf para InfluxDB/Grafana. Inclui:
* Agente Edge resiliente com store‑and‑forward, métricas Prometheus e heartbeat.
* Pipeline multi‑locatários (tópico `plc/<locatario>/<plc>` com derivação de tags quando ausentes no payload).
* Observabilidade (Prometheus -> Influx -> Grafana) e painel de depuração.
* Suporte a espelhamento bruto de DB para outro PLC.

## 2. Arquitetura de Alto Nível
```
PLC (S7) --> Agente Edge (Python snap7) --> Broker MQTT (Mosquitto TLS) --> Telegraf (json_v2) --> InfluxDB (processo/processo_raw) --> Grafana (Flux dashboards)
                                                               |--> Prometheus /metrics (latência, contadores)
                                                               |--> Store SQLite (falhas de publish)
```

### Componentes
| Componente | Função |
|------------|--------|
| `src/agent.py` | Leitura cíclica DB, publicação MQTT/HTTP/stdout, métricas, heartbeat e store‑forward |
| `src/db500_reader.py` | Extração estruturada dos campos (bool/real/int) em DB fixo (layout 14 bytes) |
| `src/store.py` | Fila persistente SQLite para garantias em caso de falha temporária de rede |
| `src/metrics.py` | Exposição de métricas Prometheus e mini dashboard HTML `/` e `/api/last` |
| `infra/mosquitto/*` | Broker MQTT com TLS, ACLs e senhas (multi‑locatários por tópico) |
| `infra/telegraf/telegraf.conf` | Ingestão MQTT (json_v2), derivação de tags locatario/plc, escrita InfluxDB |
| `infra/grafana/*` | Datasource e dashboards Flux provisionados |
| `docker-compose.yml` | Orquestração dos serviços (edge, broker, telegraf, influx, grafana) |
| `src/mirror.py` | Espelhamento bruto DB: lê bytes de um PLC e replica em outro PLC |
| `src/exporter.py` | Versão simplificada de exportador de valores DB500 (modo legado) |
| `src/config_loader.py` | Carregamento e normalização da configuração (YAML + env) |
| `src/cfg_schema.py` | Modelos Pydantic auxiliares para schema |

## 3. Fluxo de Dados
1. Edge lê DB (snap7) e monta payload JSON.
2. Publica em tópico MQTT resolvido: `plc/<locatario>/<plc>`.
3. Telegraf consome `plc/#`, parseia JSON (measurement `s7_db1`), promove `ip` e `db` a tags.
4. Se `locatario_id` e `plc_id` não vierem como fields, regex deriva do tópico e converte para tags.
5. Escreve em buckets InfluxDB (`processo`, `processo_raw`).
6. Grafana (Flux) exibe contadores, latência e derivadas.

### 3.1 Schema do Payload (Edge -> MQTT)
...existing code...

### 3.2 Exemplo de Heartbeat de Falha
...existing code...

## 4. Estrutura de Diretórios
...existing code...

## 5. Descrição dos Arquivos Principais
...existing code...

## 6. Multi‑Locatários MQTT
Formato de tópico: `plc/<locatario>/<plc>`.
...existing code...

## 7. Pipeline de Ingestão
...existing code...

## 8. Métricas & Observabilidade
...existing code...

## 9. Store & Forward
...existing code...

## 10. Segurança
...existing code...

## 11. Testes
...existing code...

## 12. Execução Rápida (Local / Docker)
...existing code...

## 13. Configuração (`config.yaml`)
...existing code...

## 14. Downsampling (Futuro)
...existing code...

## 15. Próximos Passos / Melhorias
...existing code...

## 16. Troubleshooting Rápido
...existing code...

## 17. Licença / Uso
Uso interno industrial. Ajuste conforme políticas da empresa.

---
Documentação complementar:
* `docs/PLANO_VIABILIDADE.md` – Viabilidade & roadmap SaaS
* `docs/MODELO_MULTI_LOCATARIOS.md` – Isolamento e quotas
* `docs/ESPECIFICACAO_API_PROVISIONAMENTO.md` – Endpoints control‑plane
* `docs/ESTRATEGIA_RETENCAO_DADOS.md` – Políticas de retenção/downsampling
* `docs/ESPECIFICACAO_MOTOR_ALERTAS.md` – Regras e motor de alertas
* `docs/ANALISE_GAPS.md` – Prioridades de evolução
* `OPERACOES.md` – Rotinas operacionais
* `scripts/*.ps1` – Scripts para diagnóstico e tokens
* `docs/CHECKLIST_EDGE_BOX.md` – Checklist marcável para entrega de Edge Box
* `docs/DB500_LAYOUT.md` – Como configurar e ampliar DB500 multi‑máquinas

---
> Última atualização: arquivo traduzido e alinhado ao conjunto de documentos em português.