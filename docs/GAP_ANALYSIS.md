# Análise de Gaps para Evolução SaaS IoT Industrial

## 1. Resumo Atual
| Área | Implementado | Observação |
|------|--------------|------------|
| Edge Leitura PLC | Sim (snap7 leitura DB, parser campos) | Layout fixo DB500 14 bytes |
| Publicação MQTT | Sim (TLS, tópico com placeholders) | Reconnect curto por ciclo (não persistente) |
| Multi-tenant Básico | Sim (topic plc/<tenant>/<plc>, derivação regex) | Duplica tenant/plc como field + tag |
| Store & Forward | Sim (SQLite, flush em lote) | Sem limite tamanho/estratégia limpeza |
| Métricas Edge | Sim (Prometheus + /metrics + dashboard HTML) | Falta métricas de backlog idade |
| Ingestão | Sim (Telegraf mqtt_consumer json_v2) | Sem gateway próprio HTTP/Kafka ainda |
| TSDB | Sim (InfluxDB buckets processo/processo_raw) | Sem quotas por tenant |
| Visualização | Sim (Grafana dashboards Flux) | Painéis focados em contadores básicos |
| Segurança MQTT | TLS + ACL + usuário/senha | Sem mTLS, sem rotação automática |
| Configuração | YAML + env mapping | Sem provisioning via API |
| Alertas | Básicos em Grafana (manual) | Sem engine dedicada |
| Downsampling | Plano (arquivo Flux tarefa) | Não automatizado |
| IA Preditiva | Não | Roadmap futuro |
| Integrações ERP | Não | Planejar API externa |
| Billing | Não | Necessário definir métricas de cobrança |
| Compliance | Parcial (segregação lógica) | Falta política de retenção + exportação automatizada |

## 2. Categoria vs Objetivo SaaS
| Categoria | Meta SaaS | Estado | Gap |
|-----------|-----------|--------|-----|
| Edge Resiliência | Buffer offline, reconnect persistente, compressão | Parcial | Reconnect persistente + monitor idade backlog |
| Multi-Tenant Isolamento | Buckets/schemas segregados, quotas | Parcial | Implementar quotas, remover duplicação tags/fields |
| Segurança | mTLS, rotação tokens, audit | Básico | Adicionar mTLS, audit trail, rotação periódica |
| Observabilidade | Métricas ingest lag, parse errors | Parcial | Adicionar métricas ingest no pipeline (precisa gateway) |
| Ingest Pipeline | Gateway escalável (HTTP+MQTT), validação | Básico | Criar serviço ingest dedicado (fora Telegraf) |
| IA | Anomalias e manutenção preditiva | Ausente | Implementar pipeline agregação + features |
| Provisionamento | API para devices/tenants | Ausente | Criar control-plane (CRUD tenant/device) |
| Monetização | Planos, quotas enforcement | Ausente | Medir uso e aplicar limites |
| Compliance | Retenção configurável, export | Parcial | Downsampling + política retenção por plano |
| Alertas | Motor próprio (limiares, regras) | Parcial (Grafana) | Construir motor com DSL simples |

## 3. Priorização (Curto / Médio / Longo Prazo)
### Curto (Q1)
- Reconnect MQTT persistente (sessão longa, redução overhead TLS).
- Remover duplicação tenant_id/plc_id como fields (manter só tags).
- Métrica idade backlog / tamanho máximo configurável.
- Script de downsampling automático 1m → 5m → 1h.
- API mínima de provisionamento (tenant CRUD + gerar token Influx limitado).
- Limpeza básica backlog (TTL ou tamanho máximo em MB).

### Médio (Q2)
- Quotas por tenant (mensagens/dia, retenção, dispositivos).
- Motor de alertas: limiar dinâmico + ausência de dados.
- Audit log (alterações configs, alertas, tokens).
- Rotação programada de senhas/tokens.
- Integração export (CSV/Parquet) agendada.
- Gateway ingest custom (validação, normalização, métricas ingest lag).

### Longo (Q3+)
- IA anomalias (Isolation Forest / EWMA adaptativo).
- Manutenção preditiva supervisionada.
- OTA firmware seguro para gateway.
- Digital Twin simplificado.
- Prescriptive analytics (recomendação de ação).
- mTLS completo + provisionamento de certificados.

## 4. Ações Técnicas Concretas
| Ação | Arquivos/Serviços | Tipo |
|------|--------------------|------|
| Reconnect persistente MQTT | `src/agent.py` | Refactor |
| Unificar tags tenant/plc | `infra/telegraf/telegraf.conf` | Config ajuste |
| Métrica idade backlog | `src/store.py` + `src/metrics.py` | Código |
| Downsampling job | `infra/influx/tasks/downsample_1m.flux` | Nova tarefa |
| API Provisionamento | Novo serviço (ex.: `svc/provisioning/`) | Novo componente |
| Quotas | Control-plane + TSDB measurement quota_usage | Backend + métricas |
| Alert Engine | Novo módulo (ex.: `svc/alerts/`) | Servidor |
| Audit Log | Middleware API | Backend |
| Export Parquet | Job ETL (ex.: `jobs/export_parquet.py`) | Batch |
| IA Pipeline | `jobs/ai_features.py` + model store | Batch/Online |
| Firmware OTA | Edge + API | Edge + Control-plane |

## 5. Métricas a Adicionar
- ingest_messages_total, ingest_lag_ms
- parse_error_total
- backlog_oldest_age_seconds
- publish_retry_total
- quota_usage_percent
- ai_inference_latency_ms (futuro)

## 6. Riscos & Mitigações (Detalhados)
| Risco | Mitigação |
|-------|----------|
| Crescimento rápido de dados | Downsampling, cold storage, compressão | 
| Falhas intermitentes rede OT | Store-forward otimizando flush + persistência local | 
| Escalada complexidade driver | Plugin modular por protocolo | 
| Segurança credenciais hard-coded | Externalizar secrets para Vault/KMS | 
| Sem visibilidade ingest | Introduzir gateway com métricas detalhadas | 

## 7. Checklist Preparar MVP SaaS
1. Refatorar agente para sessão persistente MQTT.
2. Ajustar Telegraf para não duplicar tenant/plc (somente tags derivadas ou no payload).
3. Implementar métrica idade backlog.
4. Adicionar tarefa Flux de downsampling.
5. Criar serviço mínimo de tenants + tabela devices + geração token.
6. Definir convenção de quotas iniciais (ex.: dispositivos <= 10 free).
7. Documentar API (OpenAPI) e fluxo de onboarding.
8. Política de backup e restore testada.

## 8. Próximos Passos Imediatos
- Selecionar formato de token (JWT curto + refresh / chave estática inicial).
- Especificar schema de banco para control-plane (tenants, devices, quotas, tokens, audit).
- Planejar estratégia de migração: colocar gateway entre broker e Telegraf sem interromper fluxo.

_Arquivo gerado automaticamente para apoiar planejamento de evolução._
