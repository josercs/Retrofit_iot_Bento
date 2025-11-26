# Análise de Lacunas (Gaps) para Evolução SaaS IoT Industrial

## 1. Resumo Atual
| Área | Implementado | Observação |
|------|--------------|------------|
| Leitura PLC Edge | Sim (snap7 leitura DB, parser campos) | Layout fixo DB500 14 bytes |
| Publicação MQTT | Sim (TLS, tópico com placeholders) | Reconnect curto por ciclo (não persistente) |
| Multi‑locatários Básico | Sim (tópico plc/<locatario>/<plc>, derivação regex) | Duplica locatario/plc como field + tag |
| Store & Forward | Sim (SQLite, flush em lote) | Sem limite tamanho/estratégia limpeza |
| Métricas Edge | Sim (Prometheus + /metrics + dashboard HTML) | Falta métricas de idade do backlog |
| Ingestão | Sim (Telegraf mqtt_consumer json_v2) | Sem gateway próprio HTTP/Kafka ainda |
| TSDB | Sim (InfluxDB buckets processo/processo_raw) | Sem quotas por locatário |
| Visualização | Sim (Grafana dashboards Flux) | Painéis básicos de contadores |
| Segurança MQTT | TLS + ACL + usuário/senha | Sem mTLS, sem rotação automática |
| Configuração | YAML + env mapping | Sem provisionamento via API |
| Alertas | Básicos em Grafana (manual) | Sem motor dedicado |
| Downsampling | Planejado (arquivo Flux) | Não automatizado |
| IA Preditiva | Não | Roadmap futuro |
| Integrações ERP | Não | Planejar API externa |
| Faturamento | Não | Definir métricas de cobrança |
| Conformidade | Parcial (segregação lógica) | Falta política de retenção + exportação automática |

## 2. Categoria vs Objetivo SaaS
| Categoria | Meta SaaS | Estado | Lacuna |
|-----------|-----------|--------|-------|
| Resiliência Edge | Buffer offline, reconnect persistente, compressão | Parcial | Reconnect persistente + monitor idade backlog |
| Isolamento Multi‑Locatários | Buckets/schemas segregados, quotas | Parcial | Implementar quotas, remover duplicação tags/fields |
| Segurança | mTLS, rotação tokens, auditoria | Básico | Adicionar mTLS, trilha auditoria, rotação periódica |
| Observabilidade | Métricas ingest lag, parse errors | Parcial | Adicionar métricas de ingestão no pipeline (gateway) |
| Pipeline Ingestão | Gateway escalável (HTTP+MQTT), validação | Básico | Criar serviço de ingest dedicado |
| IA | Anomalias e manutenção preditiva | Ausente | Implementar pipeline agregação + features |
| Provisionamento | API para locatários/dispositivos | Ausente | Criar control‑plane (CRUD locatário/dispositivo) |
| Monetização | Planos, enforcement de quotas | Ausente | Medir uso e aplicar limites |
| Conformidade | Retenção configurável, export | Parcial | Downsampling + política de retenção por plano |
| Alertas | Motor próprio (limiares, regras) | Parcial | Construir motor com DSL simples |

## 3. Priorização (Curto / Médio / Longo Prazo)
### Curto (Q1)
- Reconnect MQTT persistente (sessão longa, redução overhead TLS).
- Remover duplicação locatario_id/plc_id como fields (manter só tags).
- Métrica idade backlog / limite máximo configurável.
- Script de downsampling automático 1m → 5m → 1h.
- API mínima de provisionamento (locatário CRUD + gerar token Influx limitado).
- Limpeza básica backlog (TTL ou tamanho máximo em MB).

### Médio (Q2)
- Quotas por locatário (mensagens/dia, retenção, dispositivos).
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
| Reconnect persistente MQTT | `src/agent.py` | Refatoração |
| Unificar tags locatario/plc | `infra/telegraf/telegraf.conf` | Ajuste config |
| Métrica idade backlog | `src/store.py` + `src/metrics.py` | Código |
| Downsampling job | `infra/influx/tasks/downsample_1m.flux` | Nova tarefa |
| API Provisionamento | Novo serviço (`svc/provisionamento/`) | Componente |
| Quotas | Control‑plane + TSDB measurement quota_usage | Backend + métricas |
| Motor Alertas | Novo módulo (`svc/alertas/`) | Servidor |
| Audit Log | Middleware API | Backend |
| Export Parquet | Job ETL (`jobs/export_parquet.py`) | Batch |
| Pipeline IA | `jobs/ia_features.py` + model store | Batch/Online |
| Firmware OTA | Edge + API | Edge + Control‑plane |

## 5. Métricas a Adicionar
- ingest_messages_total, ingest_lag_ms
- parse_error_total
- backlog_oldest_age_seconds
- publish_retry_total
- quota_usage_percent
- ai_inference_latency_ms (futuro)

## 6. Riscos & Mitigações
| Risco | Mitigação |
|-------|-----------|
| Crescimento rápido de dados | Downsampling, cold storage, compressão |
| Falhas intermitentes rede OT | Store-forward otimizado + persistência local |
| Complexidade drivers | Plugin modular por protocolo |
| Segurança credenciais hard-coded | Externalizar secrets para Vault/KMS |
| Sem visibilidade ingestão | Introduzir gateway com métricas detalhadas |

## 7. Checklist Preparar MVP SaaS
1. Refatorar agente para sessão persistente MQTT.
2. Ajustar Telegraf para não duplicar locatario/plc (somente tags derivadas ou no payload).
3. Implementar métrica idade backlog.
4. Adicionar tarefa Flux de downsampling.
5. Criar serviço mínimo de locatários + tabela dispositivos + geração de token.
6. Definir convenção de quotas iniciais (ex.: dispositivos <= 10 plano Free).
7. Documentar API (OpenAPI) e fluxo de onboarding.
8. Política de backup e restore testada.

## 8. Próximos Passos Imediatos
- Selecionar formato de token (JWT curto + refresh / chave estática inicial).
- Especificar schema de banco para control‑plane (locatários, dispositivos, quotas, tokens, auditoria).
- Planejar estratégia de migração: colocar gateway entre broker e Telegraf sem interromper fluxo.

_Documento gerado para apoiar planejamento de evolução._