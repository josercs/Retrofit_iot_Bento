# Modelo de Multi‑Locatários

## 1. Objetivo
Definir como dados, recursos e limites são isolados e gerenciados entre múltiplos clientes (locatários) na plataforma SaaS, garantindo segurança, previsibilidade de custos e escalabilidade.

## 2. Identidade do Locatário
- Identificador interno: UUID (chave primária).
- Slug público: string curta (ex: `plantaA`, `linhaX`).
- Nome amigável: descrição livre.
- Status: ativo | suspenso | encerrado.

## 3. Dispositivos / PLCs
| Campo | Descrição |
|-------|-----------|
| device_id | UUID interno |
| plc_id | Slug curto (ex: prensa1) |
| tipo | Categoria (siemens_s7, modbus_tcp, opcua) |
| tags | Metadados auxiliares (ex: setor=embalagem) |
| ativo | booleano |

## 4. Tópicos MQTT
Formato: `plc/<locatario_slug>/<plc_id>`
- Segurança via ACL por prefixo `plc/<locatario_slug>/#`.
- Username padrão: `t_<locatario_slug>_<plc_id>` (Agente Edge) ou `t_<locatario_slug>_svc` (serviços internos).
- Placeholders resolvidos no Edge; Telegraf deriva se ausente (precedência: JSON > tópico).

## 5. Isolamento de Dados
MVP:
- Buckets Influx compartilhados: `processo_raw`, `processo`, `processo_1m`.
- Tag obrigatória: `locatario_id` (originada de tenant_id).
- Consultas Grafana sempre filtram `locatario_id`.

Evolução Enterprise:
- Buckets dedicados por locatário crítico (alto volume ou requisitos regulatórios).
- Possível segregação por organização Influx (org por grupo empresarial).

## 6. Convenções de Nomes
| Recurso | Convenção |
|---------|-----------|
| locatario_slug | [a-z0-9-_]{3,32} |
| plc_id | [a-z0-9-_]{3,32} |
| bucket enterprise | `<locatario_slug>_raw`, `<locatario_slug>_proc` |
| usernames | `t_<locatario_slug>_<sufixo>` |
| tokens descrição | `locatario:<slug>:<uso>` |

## 7. Quotas (Planos)
| Plano | Dispositivos | Pontos/min (ingestão) | Retenção bruto | Retenção agregado | Alertas ativos | Dashboards |
|-------|--------------|----------------------|----------------|-------------------|---------------|-----------|
| Free | 2 | 500 | 3d | 30d | 5 | 5 |
| Pro | 20 | 5k | 7d | 180d | 50 | 20 |
| Enterprise | 100+ | 50k | 30d | 365d | 200 | 100 |

Notas:
- Pontos/min = número de fields individuais ingeridos por minuto.
- Retenção agregada refere‑se ao bucket de downsampling (1m ou 5m).

## 8. Aplicação das Quotas
- Coleta diária de métricas: pontos_total_dia, avg_pontos_min, dispositivos_ativos.
- Se >90% da quota por 3 dias consecutivos: gerar alerta proativo de upgrade.
- Hard cap: rejeitar ingestão se >110% quota (configurável) via política Telegraf/Edge (futuro).

## 9. Métricas por Locatário
Armazenadas no bucket `platform_metrics`:
| Métrica | Descrição |
|---------|-----------|
| ingest_points_min | Média de pontos por minuto |
| ingest_latency_p95 | Latência p95 edge->influx |
| devices_active | Quantidade dispositivos ativos 24h |
| alerts_fired | Alertas disparados no período |
| storage_bytes | Estimativa tamanho séries |
| cardinality_series | Cardinalidade séries |

## 10. Segurança & Isolamento
- ACL MQTT restringe prefixo por locatário.
- Tokens Influx emitidos com escopo restrito a buckets compartilhados ou dedicados.
- Auditoria: logs da API (CRUD locatário/dispositivo/token).
- Sem dados sensíveis em tags; usar fields para valores de processo.

## 11. Ciclo de Vida do Locatário
| Etapa | Ação |
|-------|------|
| Criação | POST /tenants (define plano inicial) |
| Ativação | Criação de dispositivos, emissão credenciais Edge |
| Operação | Monitorar quotas, alertas, dashboards |
| Suspensão | Revogar tokens + bloquear ACL MQTT |
| Upgrade | Alterar plano + ajustar quotas |
| Encerramento | Exportar dados, revogar tokens |

## 12. Migração para Buckets Dedicados
Critérios:
- Cardinalidade > 1M séries.
- Latência de consultas > 3s p95.
- Requisitos regulatórios (LGPD, auditoria separada).
Processo:
1. Criar novos buckets `<slug>_raw` e `<slug>_proc`.
2. Atualizar tokens e datasource Grafana do locatário.
3. Reconfigurar Telegraf (nova saída condicional por locatário).
4. Validar ingestão simultânea (dual‑write) por 24h.
5. Encerrar escrita antiga e iniciar arquivamento.

## 13. Faturamento Básico (Futuro)
- Cálculo MRR = plano_base + excedentes (pontos extras / dispositivos adicionais).
- Relatório mensal: uso vs quotas, recomendação de upgrade.

## 14. Escalabilidade
- Particionamento lógico inicial via tag `locatario_id`.
- Monitorar cardinalidade e migrar locatários pesados para buckets dedicados.
- Alerta de cardinalidade (limite soft) e ferramenta de recomendação de migração.

## 15. Próximos Passos
1. Integrar coleta de métricas por locatário (job diário).
2. Implementar endpoint de quotas /tenants/{id}/usage.
3. Adicionar processo de migração para bucket dedicado.
4. Integrar com faturamento (fase posterior).

(Referências: PLANO_VIABILIDADE.md (visão macro), OPERACOES.md (rotinas), ESTRATEGIA_RETENCAO_DADOS.md (retenção), ESPECIFICACAO_API_PROVISIONAMENTO.md (endpoints), ESPECIFICACAO_MOTOR_ALERTAS.md (alertas).)