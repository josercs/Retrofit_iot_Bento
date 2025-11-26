# Modelo de Multi-Tenancy

## 1. Objetivo
Definir como dados, recursos e limites são isolados e gerenciados entre múltiplos clientes (tenants) na plataforma SaaS, garantindo segurança, previsibilidade de custos e escalabilidade.

## 2. Identidade de Tenant
- Identificador interno: UUID (chave primária).
- Slug público: string curta (ex: `plantaA`, `linhaX`).
- Nome amigável: descrição livre.
- Status: active | suspended | closed.

## 3. Dispositivos / PLCs
| Campo | Descrição |
|-------|-----------|
| device_id | UUID interno |
| plc_id | Slug curto (ex: prensa1) |
| tipo | Categoria (siemens_s7, modbus_tcp, opcua) |
| tags | Metadados auxiliares (ex: setor=embalagem) |
| ativo | booleano |

## 4. Tópicos MQTT
Formato: `plc/<tenant_slug>/<plc_id>`
- Segurança via ACL por prefixo `plc/<tenant_slug>/#`.
- Username padrão: `t_<tenant_slug>_<plc_id>` (Edge Agent) ou `t_<tenant_slug>_svc` (serviços internos).
- Placeholders resolvidos no Edge; Telegraf deriva se ausente (precedence: JSON > tópico).

## 5. Isolamento de Dados
MVP:
- Buckets Influx compartilhados: `processo_raw`, `processo`, `processo_1m`.
- Tag obrigatória: `tenant_id`.
- Consultas Grafana sempre filtram `tenant_id`.

Evolução Enterprise:
- Buckets dedicados por tenant crítico (alto volume ou requisitos regulatórios).
- Possível segregação por organização Influx (org por grupo empresarial).

## 6. Convenções de Nomes
| Recurso | Convenção |
|---------|-----------|
| tenant_slug | [a-z0-9-_]{3,32} |
| plc_id | [a-z0-9-_]{3,32} |
| bucket enterprise | `<tenant_slug>_raw`, `<tenant_slug>_proc` |
| usernames | `t_<tenant_slug>_<suffix>` |
| tokens description | `tenant:<slug>:<uso>` |

## 7. Quotas (Planos)
| Plano | Dispositivos | Pontos/min (ingest) | Retenção raw | Retenção agregada | Alertas ativos | Dashboards |
|-------|--------------|--------------------|--------------|-------------------|---------------|-----------|
| Free | 2 | 500 | 3d | 30d | 5 | 5 |
| Pro | 20 | 5k | 7d | 180d | 50 | 20 |
| Enterprise | 100+ | 50k | 30d | 365d | 200 | 100 |

Notas:
- Pontos/min = número de fields individuais ingestados por minuto.
- Retenção agregada refere-se a bucket downsample (1m ou 5m).

## 8. Enforcement das Quotas
- Coleta diária de métricas: pontos_total_dia, avg_pontos_min, dispositivos_ativos.
- Se >90% quota por 3 dias consecutivos: gerar alerta proativo upgrade.
- Hard cap: rejeitar ingest se >110% quota (configurável) via política Telegraf/Edge (feature futura).

## 9. Métricas por Tenant
Coletadas e armazenadas em bucket `platform_metrics`:
| Métrica | Descrição |
|---------|-----------|
| ingest_points_min | Média pontos por minuto |
| ingest_latency_p95 | Latência p95 edge->influx |
| devices_active | Qtde dispositivos ativos 24h |
| alerts_fired | Alertas disparados no período |
| storage_bytes | Estimativa tamanho séries |
| cardinality_series | Cardinalidade séries |

## 10. Segurança & Isolamento
- ACL MQTT restringe prefixo por tenant.
- Tokens Influx emitidos com escopo restrito a buckets compartilhados (filtragem via consultas) ou buckets dedicados.
- Auditoria: logs API (CRUD tenant/device/token).
- Sem dados sensíveis em tags (evitar expor nomes internos); usar fields para valores de processo.

## 11. Fluxo de Ciclo de Vida Tenant
| Etapa | Ação |
|-------|------|
| Criação | POST /tenants (define plano inicial) |
| Ativação | Criação device(s), emissão credenciais Edge |
| Operação | Monitoração quotas, alertas, dashboards |
| Suspensão | Disable tokens + bloquear ACL MQTT |
| Upgrade | Alterar plano + ajustar quotas |
| Encerramento | Export dados, revogar tokens |

## 12. Estratégia de Migração para Buckets Dedicados
Critérios:
- Cardinalidade > 1M séries.
- Latência consultas > 3s p95.
- Requisitos regulatórios (LGPD, auditoria separada).
Processo:
1. Criar novos buckets `<slug>_raw` e `<slug>_proc`.
2. Atualizar tokens e datasource Grafana para tenant.
3. Reconfigurar Telegraf (nova saída condicional por tenant).
4. Validar ingest simultânea (dual-write) por 24h.
5. Cortar escrita antiga e iniciar tarefa de arquivamento.

## 13. Faturamento Básico (Futuro)
- Cálculo MRR = plano_base + excedentes (pontos extras / dispositivos adicionais).
- Relatório mensal: uso vs quotas, recomendação upgrade.

## 14. Escalabilidade
- Partitionamento lógico via tag `tenant_id` inicialmente.
- Monitor cardinalidade e mover heavy tenants para buckets dedicados.
- Alerta cardinalidade (limite soft). Ferramenta de recomendação migração.

## 15. Próximos Passos
1. Integrar coleta métricas por tenant (job diário).
2. Implementar endpoint quotas /tenants/{id}/usage.
3. Adicionar processo migração bucket dedicado.
4. Integrar com billing (fase posterior).

(Referências: FEASIBILITY_PLAN.md (visão macro), OPERATIONS.md (rotinas), DATA_RETENTION_STRATEGY.md (retenção), PROVISIONING_API_SPEC.md (endpoints), ALERT_ENGINE_SPEC.md (alertas).)
