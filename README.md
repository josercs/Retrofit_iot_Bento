# Retrofit_iot_Bento

# PLC Mirror & Edge Ingestion (python-snap7 + MQTT + Telegraf + InfluxDB + Grafana)

## 1. Visão Geral
Projeto para ler dados de PLC Siemens (S7) via DB (ex.: DB500), publicar medições JSON multi-tenant em MQTT com TLS e ingestão por Telegraf para InfluxDB/Grafana. Inclui:
* Agente Edge resiliente com store-and-forward, métricas Prometheus e heartbeat.
* Pipeline multi-tenant (tópico `plc/<tenant>/<plc>` com derivação de tags quando ausentes no payload).
* Observabilidade (Prometheus -> Influx -> Grafana) e painel de depuração.
* Suporte a mirroring bruto de DB para outro PLC.

## 2. Arquitetura de Alto Nível
```
PLC (S7) --> Edge Agent (Python snap7) --> MQTT Broker (Mosquitto TLS) --> Telegraf (json_v2) --> InfluxDB (processo/processo_raw) --> Grafana (Flux dashboards)
																|--> Prometheus /metrics (latência, counters)
																|--> Store SQLite (falhas de publish)
```

### Componentes
| Componente | Função |
|------------|--------|
| `src/agent.py` | Leitura cíclica DB, publicação MQTT/HTTP/stdout, métricas, heartbeat e store-forward |
| `src/db500_reader.py` | Extração estruturada dos campos (bool/real/int) em DB fixo (layout 14 bytes) |
| `src/store.py` | Fila persistente SQLite para garantias em caso de falha temporária de rede |
| `src/metrics.py` | Exposição de métricas Prometheus e mini dashboard HTML `/` e `/api/last` |
| `infra/mosquitto/*` | Broker MQTT com TLS, ACLs e senhas (multi-tenant por tópico) |
| `infra/telegraf/telegraf.conf` | Ingestão MQTT (json_v2), derivação de tags tenant/plc, escrita InfluxDB |
| `infra/grafana/*` | Datasource e dashboards Flux provisionados |
| `docker-compose.yml` | Orquestração dos serviços (edge, broker, telegraf, influx, grafana) |
| `src/mirror.py` | Mirror bruto DB: lê bytes de um PLC e replica em outro PLC |
| `src/exporter.py` | Versão simplificada de exportador de valores DB500 (modo legado) |
| `src/config_loader.py` | Carregamento e normalização da configuração (YAML + env) |
| `src/cfg_schema.py` | Modelos Pydantic auxiliares para schema |

## 3. Fluxo de Dados (Detalhado)
1. Edge lê DB (snap7) e monta payload JSON:
```json
{
	"ts": 1731800000.123,
	"ip": "192.168.0.121",
	"db": 1,
	"tenant_id": "clienteA",
	"plc_id": "linha1_prensa",
	"values": {
		"pecas_boas": true,
		"contador_bom": 5014,
		...
	}
}
```
2. Publica em tópico MQTT resolvido: `plc/clienteA/linha1_prensa`.
3. Telegraf consome `plc/#`, parseia JSON (measurement `s7_db1`), promove `ip` e `db` a tags.
4. Se `tenant_id` e `plc_id` não vierem como fields, regex deriva do tópico e converte para tags.
5. Escreve em buckets InfluxDB:
	 * `processo` (operacional, retenção 30d)
	 * `processo_raw` (bruto, sem retenção para downsampling futuro)
6. Grafana (Flux) lê e exibe contadores, latência e derivadas.

### 3.1 Schema do Payload (Edge -> MQTT)
Campos fixos:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| ts | float (epoch) | Timestamp de coleta (segundos) |
| ip | string | IP do PLC fonte |
| db | int | Número do DB lido |
| tenant_id | string (opcional) | Identificador do cliente/tenant |
| plc_id | string (opcional) | Identificador lógico do PLC/linha |
| values | objeto | Sinais decodificados do DB |

Layout `values` atual (DB de 14 bytes):
| Nome | Tipo | Origem | Byte | Bit/Offset |
|------|------|--------|------|------------|
| pecas_ruim | bool | Byte0 Bit0 | 0 | 0 |
| pecas_boas | bool | Byte0 Bit1 | 0 | 1 |
| maquina_ligada | bool | Byte0 Bit2 | 0 | 2 |
| AI_Corrente | real | get_real | 2 | - |
| AI_Vibracao | real | get_real | 6 | - |
| contador_bom | int | get_int | 10 | - |
| contador_ruim | int | get_int | 12 | - |

Observações:
* Campos booleanos viram `true/false` no JSON e boolean nos fields Influx.
* Em caso de falha de leitura, payload de heartbeat inclui `read_failed=true` dentro de `values`.
* Heartbeat forçado inclui somente `{ "heartbeat":1 }` em `values`.

### 3.2 Exemplo de Heartbeat de Falha
```json
{
	"ts": 1731801111.456,
	"ip": "192.168.0.121",
	"db": 1,
	"tenant_id": "clienteA",
	"plc_id": "linha1_prensa",
	"values": {"heartbeat":1, "read_failed": true},
	"error": "timeout"
}
```

## 4. Estrutura de Diretórios
```
src/              Código do agente e utilitários
infra/mosquitto/  Config broker TLS + ACL
infra/telegraf/   Ingestão e processors
infra/grafana/    Provisionamento datasource + dashboards
data/             Persistência de Influx, Grafana, Mosquitto
scripts/          Scripts PowerShell utilitários (tokens, diagnóstico)
tests/            Testes Pytest
queue.sqlite      Fila store-forward
```

## 5. Descrição dos Arquivos Principais
### `src/agent.py`
Loop principal: lê DB via `read_values`, constrói payload, publica MQTT (resolvendo placeholders `${TENANT_ID}`/`${PLC_ID}`), expõe métricas, heartbeat a cada 30s, faz flush da fila (`StoreForward`). Inclui fallback para publicar heartbeat em falha de leitura.

### `src/db500_reader.py`
Define layout fixo (bools, floats, ints) e extrai valores de bytes crus do DB; conexão curta (abre, lê, fecha) para reduzir impacto.

### `src/store.py`
Implementa tabela SQLite `events(id, ts, payload)` com métodos `enqueue`, `dequeue`, `delete_ids`, `count` — garante durabilidade em falhas de rede/MQTT.

### `src/metrics.py`
Registra métricas (Counters/ Gauges) e fornece servidor HTTP simples com `/metrics` (Prometheus) e dashboard HTML para inspeção rápida.

### `src/mirror.py`
Ferramenta independente para copiar bytes de um DB origem para DB destino (útil em cenários de redundância ou laboratório).

### `src/exporter.py`
Exportador simplificado anterior (sem métricas/store-forward avançados) — pode ser usado para testes básicos ou comparação.

### `src/config_loader.py` / `src/cfg_schema.py`
Carregam YAML, aplicam variáveis de ambiente (mapas), corrigem erros de indentação, validam com Pydantic. Suporte a seções MQTT/HTTP.

### Infra:
* `infra/mosquitto/mosquitto.conf`: Listener TLS 8883, certificados, ACL e persistência.
* `infra/mosquitto/auth/aclfile`: Regras: `edge_agent` escreve `plc/#`; `telegraf` lê `plc/#`.
* `infra/telegraf/telegraf.conf`: mqtt_consumer + json_v2 + derivação condicional + conversão tags + outputs Influx/arquivo.
* Grafana (`infra/grafana/provisioning/*`): Datasource Flux (org `planta`, bucket default `processo`) e dashboards (ex.: `plc_status.json`).
* `docker-compose.yml`: Orquestra serviços com dependências e healthchecks.

## 6. Multi-Tenant MQTT
Formato de tópico: `plc/<tenant>/<plc>`.
* Agente substitui placeholders com env: `TENANT_ID` e `PLC_ID`.
* Telegraf deriva tags se ausentes (regex sobre tag `topic`).
* Precedência: se `tenant_id` ou `plc_id` vêm no JSON, não são sobrescritos.

### 6.1 Variáveis de Ambiente Suportadas
| Variável | Uso | Exemplo |
|----------|-----|---------|
| TENANT_ID | Identidade do tenant | clienteA |
| PLC_ID | Identidade do PLC | linha1_prensa |
| MQTT_BROKER / MQTT_PORT | Override broker/porta | mosquitto / 8883 |
| MQTT_TOPIC | Forçar tópico customizado | plc/${TENANT_ID}/${PLC_ID} |
| MQTT_USERNAME / MQTT_PASSWORD | Credenciais MQTT | edge_agent / **** |
| MQTT_TLS / MQTT_CA_FILE | TLS e CA | true / /app/ca.crt |
| METRICS_PORT | Porta servidor métricas | 9108 |

### 6.2 Placeholders
* `${TENANT_ID}` substituído por valor de `TENANT_ID`.
* `${PLC_ID}` substituído por valor de `PLC_ID`.
* Se qualquer placeholder não for resolvido → fallback `plc/db1`.

## 7. Pipeline de Ingestão
1. MQTT -> Telegraf (json_v2 parser) -> measurement `s7_db1`.
2. Processors: regex (deriva), converter (tags), override (fallback hostname).
3. Escrita dupla em buckets (operacional + bruto) para downsampling futuro (ex.: tarefa Flux em `infra/influx/tasks`).

## 8. Métricas & Observabilidade
Métricas principais:
* `plc_read_ok_total` / `plc_read_fail_total`
* `plc_publish_ok_total` / `plc_publish_fail_total` (label `mode`)
* `plc_last_value{name=...}`
* `plc_read_latency_ms`
* `edge_backlog_size`
* `edge_up`
Dashboard Grafana usa Flux (`range(start: v.timeRangeStart, stop: v.timeRangeStop)`), derivada de contador bom por minuto.

### 8.1 Exemplos de Queries Flux
Últimos valores de contadores:
```flux
from(bucket: "processo")
	|> range(start: -15m)
	|> filter(fn: (r) => r._measurement == "s7_db1")
	|> filter(fn: (r) => r._field =~ /contador_(bom|ruim)/)
	|> last()
```
Produção por minuto (não-negativa):
```flux
from(bucket: "processo")
	|> range(start: -6h)
	|> filter(fn: (r) => r._measurement == "s7_db1" and r._field == "contador_bom")
	|> derivative(unit: 1m, nonNegative: true)
	|> aggregateWindow(every: 5m, fn: mean)
```
Latência média de leitura:
```flux
from(bucket: "processo")
	|> range(start: -1h)
	|> filter(fn: (r) => r._measurement == "prometheus" and r._field == "plc_read_latency_ms")
	|> aggregateWindow(every: 1m, fn: mean)
```

### 8.2 Painel HTML Local
* Acessível em `http://<edge>:9108/` para inspeção rápida dos últimos sinais (sem Grafana).

### 8.3 Alertas (Sugestão)
Configure regras Grafana para:
* Ausência de novos pontos `s7_db1` por > 2 ciclos.
* Crescimento de `edge_backlog_size`.
* Latência > limiar (ex.: 250 ms).

## 9. Store & Forward
Falha em publicar → payload é enfileirado em `queue.sqlite`. Após publicação bem-sucedida de ciclo normal, o agente tenta flush em lote (200 eventos) deletando IDs processados.

### 9.1 Estratégia de Recuperação
1. Em falha MQTT/HTTP → `enqueue`.
2. Em ciclo subsequente com sucesso → tenta reenviar backlog em ordem (FIFO) até 200 itens.
3. Itens reenviados removidos via `delete_ids`.

### 9.2 Limitações Atuais
* Sem limite máximo de tamanho do arquivo (pode crescer). Monitorar e adotar TTL futura.
* Reenvio interrompido no primeiro erro após iniciar flush (parcial). Melhorar para continuar com próximos.

### 9.3 Melhorias Futuras
* Compressão de payloads antigos.
* Reagendamento exponencial.
* Métrica para idade máxima do backlog.

## 10. Segurança
* MQTT TLS (CA própria) + autenticação por usuário/senha + ACL restritiva.
* Variáveis sensíveis via ambiente (tokens Influx / senhas) — evite commitar segredos.
* Fallback `tls_insecure` desabilitado por padrão (ver `config.yaml`).

### 10.1 Hardening Adicional (Recomendado)
| Área | Ação |
|------|------|
| MQTT | Rotacionar senhas periodicamente; considerar mTLS (client cert) |
| InfluxDB | Criar token somente de escrita para Telegraf; usar politicas de retenção e downsampling |
| Grafana | Habilitar provisioning de alertas + password vault |
| Secrets | Usar `.env` fora de versão e secret manager (Vault, AWS SM) |
| Host | Limitar portas expostas (apenas 8883, 9108, 8086, 3000) |

### 10.2 Logs e Privacidade
* Logs não exibem senha; tópico resolvido exibido apenas para debug.
* Evitar incluir dados sensíveis no payload (ex.: nomes de operadores) — usar IDs abstratos.

### 10.3 ACLs MQTT
* Escrita: apenas `edge_agent` em `plc/#`.
* Leitura: `telegraf` em `plc/#`.
* Negar todos os outros usuários (não definidos).

## 11. Testes
`pytest -q` executa testes (ex.: `tests/test_mirror.py`). Para isolamento, snap7 pode ser mockado.

### 11.1 Áreas a Cobrir (Sugestão)
| Teste | Objetivo |
|-------|----------|
| Mirror bytes | Verificar tamanho e integridade após round-trip |
| Leitura DB parse | Conferir valores retornados em layout simulado |
| StoreForward enqueue/dequeue | Garantir ordem e remoção correta |
| MQTT publish placeholder | Validar substituição topic quando TENANT_ID/PLC_ID presentes |
| Fallback topic | Confirmar uso de `plc/db1` quando placeholders faltam |
| Regex derivação | Testar strings de tópico edge cases |

### 11.2 Mock snap7
Criar fixture que emula `client.db_read` retornando bytes predefinidos para testar parsing sem hardware.

## 12. Execução Rápida (Local / Docker)
### Python local
```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -r requirements-optional.txt  # para snap7 real
copy config.yaml.example config.yaml
python -m src.agent --config config.yaml
```
### Docker Compose
```powershell
docker compose up -d --build
```
Verifique:
* http://localhost:9108/metrics
* http://localhost:3000 (Grafana)

### 12.1 Healthchecks / Observabilidade Docker
* `collector` possui healthcheck HTTP simples `/metrics`.
* Adicionar healthcheck para Mosquitto (ex.: script que testa TLS handshake) — melhoria futura.
* Telegraf depende de serviços saudáveis antes de iniciar (reduz erros iniciais de token).

### 12.2 Escalabilidade
* Múltiplos agentes (1 por PLC / célula) → todos publicando em padrão de tópico.
* Telegraf escala horizontal replicando serviço (cada instância consome o mesmo tópico causando duplicação). Para evitar duplicação, usar partição por tenant ou adotar broker com filas distribuídas (ex.: Kafka) em evolução futura.

### 12.3 Performance Estimada
* Ciclo de leitura ~70–90 ms (latência medida) para DB pequeno.
* Payload ~150 bytes; QOS=1 possível para garantia de entrega (atualmente 0 para menor latência).
* ~1 leitura/s → ~8.6k mensagens/dia/PLC; escala linear com número de PLCs.

## 13. Configuração (`config.yaml`)
```yaml
source:
	ip: "192.168.0.121"
	db_number: 1
	db_size: 14
output:
	mode: mqtt
	mqtt:
		broker: mosquitto
		port: 8883
		topic: "plc/${TENANT_ID}/${PLC_ID}"
		tls: true
		ca_file: "/app/ca.crt"
```
Placeholders resolvidos pelo agente; se não houver env, fallback para `plc/db1`.

## 14. Downsampling (Futuro)
* Criar tarefas Flux em `infra/influx/tasks` (exemplo: `downsample_1m.flux`) para reduzir cardinalidade.

## 15. Próximos Passos / Melhorias
* Adicionar autenticação mTLS opcional para MQTT.
* Implementar reconexão persistente MQTT (atualmente publish curto por ciclo).
* Remover duplicação de tenant_id/plc_id como field + tag (manter só tags).
* Adicionar testes para falha de publish e flush de backlog.
* Painel Grafana adicional para latência e backlog.
* Implementar plugin de detecção de anomalias (ex.: EWMA sobre produção).
* Adicionar export para OPC UA (gateway futuro).
* Rate limiting / Circuit breaker para falhas repetidas de publish.
* Modo buffered MQTT com reconexão persistente.

## 16. Troubleshooting Rápido
| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| Sem dados `s7_db1` no Grafana | Tópico errado ou derivação falhou | Checar log agente “MQTT publish topic resolved” |
| Tags tenant/plc ausentes | Payload não tinha campos e regex não aplicou | Verificar `topic_tag` + padrão regex |
| Backlog crescendo | Falha de rede/MQTT | Checar métricas `plc_publish_fail_total`, logs e ACL |
| Latência alta | Rede/PLC lento | Ver `plc_read_latency_ms` e ajustar `poll_interval` |

### 16.1 Passo-a-Passo Diagnóstico Sem Dados
1. Ver log do agente: `MQTT publish topic resolved to:` (confirma tópico).
2. Inspecionar arquivo `/tmp/telegraf_out.lp` dentro do container Telegraf.
3. Conferir ACL no broker e se usuário tem permissão `plc/#`.
4. Executar consulta Flux direta (CLI) em `processo_raw` para `_measurement == "s7_db1"` últimos 5m.
5. Verificar relógio do host (diferença grande pode ocultar dados no range do Grafana).
6. Checar token Influx expirado ou variável de ambiente ausente.

### 16.2 Sintomas Adicionais
| Sintoma | Causa | Mitigação |
|---------|-------|-----------|
| Duplicação de pontos | Dois Telegraf consumindo mesmo tópico | Limitar a uma instância ou separar por tenant |
| Heartbeat mas sem valores | PLC offline | Revisar cabeamento / ping / firewall |
| Contadores não aumentam | DB layout mudou | Atualizar offsets em `FIELDS` |
| Erros TLS no agent | CA inválida | Regenerar CA/cert e atualizar volume |

### 16.3 Coleta Manual MQTT
Publicar mensagem sintética para teste:
```bash
mosquitto_pub -h <broker> -p 8883 --cafile ca.crt -u edge_agent -P 'SENHA' -t 'plc/teste/plc1' -m '{"ts":1731802000,"ip":"192.168.0.50","db":1,"values":{"heartbeat":1}}'
```

### 16.4 Consulta Flux Básica
```flux
from(bucket: "processo_raw")
	|> range(start: -5m)
	|> filter(fn: (r) => r._measurement == "s7_db1")
	|> limit(n: 10)
```

## 17. Licença / Uso
Uso interno industrial. Ajuste conforme políticas da empresa (adicionar arquivo LICENSE se necessário).

---
Documentação complementar:
* `docs/ARQUITETURA_SAAS.md` – Viabilidade SaaS industrial
* `scripts/*.ps1` – Scripts para diagnóstico e tokens Influx/MQTT

---
> Última atualização: Gerado automaticamente para descrever cada parte do projeto.
> Versão estendida com detalhes operacionais, segurança e troubleshooting.

## Licença
Este projeto está licenciado sob a Licença MIT. Consulte o arquivo `LICENSE` na raiz do repositório para o texto completo da licença.
