# Especificação Mecanismo de Alertas

## 1. Objetivo
Detectar condições críticas ou anômalas em métricas de processo e infraestrutura, gerando notificações confiáveis e rápidas por tenant.

## 2. Tipos de Alertas (MVP)
| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| threshold | Valor acima/abaixo de limite por janela | vib_mean_1m > 12.5 |
| absence | Falta de atualização (heartbeat) | edge_up ausente > 30s |
| rate_change | Variação brusca (derivada) | corrente_derivada < -5 A/min |
| percentage | Proporção fora de faixa | qualidade_pct < 0.92 |

Fase futura: pattern (sequência eventos), anomaly (z-score/IQR), composite (combinação regras).

## 3. Modelo de Regra
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "name": "Vibração Alta",
  "enabled": true,
  "type": "threshold",
  "metric": "vib_mean_1m",
  "condition": ">",
  "value": 12.5,
  "for_seconds": 60,
  "severity": "high",
  "notify_channels": ["email", "webhook"],
  "cooldown_seconds": 300,
  "created_at": "2025-01-10T12:00:00Z"
}
```

Absence:
```json
{
  "type": "absence",
  "metric": "edge_up",
  "missing_for_seconds": 30,
  "severity": "critical"
}
```

Rate Change:
```json
{
  "type": "rate_change",
  "metric": "corrente",
  "delta_condition": "<",
  "delta_value": -5.0,
  "window_seconds": 120
}
```

## 4. Motor de Avaliação
Fluxo:
1. Carregar regras ativas por tenant (cache em memória).
2. Obter lote métricas recentes (consulta Influx / stream).
3. Avaliar cada regra:
   - threshold: manter contador tempo em condição.
   - absence: verificar timestamp último ponto.
   - rate_change: calcular derivada (último vs anterior / tempo).
4. Gerar evento alerta se condição satisfeita e fora cooldown.
5. Persistir evento (alert_events bucket ou DB relacional).

## 5. Estado & Cooldown
- State machine por regra: OK -> FIRING -> COOLING -> OK.
- COOLING impede disparos repetidos por `cooldown_seconds`.

## 6. Notificações
Canal mínimo: email + webhook.
Formato webhook POST JSON:
```json
{
  "alert_id": "uuid",
  "tenant": "plantaA",
  "name": "Vibração Alta",
  "severity": "high",
  "status": "firing",
  "started_at": "2025-01-10T12:10:00Z",
  "metric": "vib_mean_1m",
  "value": 13.2,
  "threshold": 12.5
}
```

## 7. Métricas Internas
| Métrica | Descrição |
|---------|-----------|
| alerts_fired_total | Contagem total disparos |
| alerts_active | Número atual firing |
| evaluation_duration_ms | Tempo avaliação ciclo |
| rules_loaded | Qtde regras ativas |
| notifications_failed_total | Falhas envio |

## 8. Armazenamento
- Regras: tabela `alert_rules` (DB relacional) ou bucket config.
- Eventos: bucket `alert_events` (tags: tenant_id, severity, rule_id).

## 9. Escalabilidade
- Worker pool avaliando regras em paralelo (shard por tenant).
- Se > N regras por tenant, dividir avaliação em janelas.
- Fila interna para eventos (RabbitMQ / Redis Streams futuramente) se volume alto.

## 10. Precisão & Deduplicação
- Hash evento (rule_id + started_at arredondado) evita duplicados.
- Comparar último valor enviado para decidir se notificar novamente (se delta > x%).

## 11. API Gestão de Regras (Futuro)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/alerts/rules | Criar regra |
| GET | /v1/alerts/rules?tenant_id= | Listar regras |
| PATCH | /v1/alerts/rules/{id} | Atualizar |
| DELETE | /v1/alerts/rules/{id} | Remover |
| GET | /v1/alerts/events?tenant_id= | Listar eventos |

## 12. Segurança
- Regras só acessíveis ao tenant proprietário.
- Sanitização de entradas (nomes métricas) para evitar injeção consultas.
- Rate limit criação/alteração regras.

## 13. Testes & Qualidade
- Teste unit threshold (disparo após tempo).
- Teste ausência (não dispara antes tempo limite).
- Teste cooldown (não dispara repetido).
- Teste rate_change (derivada negativa aciona).

## 14. Roadmap Extensões
| Fase | Item |
|------|------|
| F1 | Composite rules (AND/OR) |
| F2 | Anomalia IQR / z-score automático |
| F2 | Escalonamento multi-severity |
| F3 | Aprendizado modelo sazonal (Prometheus style) |

## 15. Próximos Passos
1. Implementar protótipo threshold + absence.
2. Persistir eventos e expor /metrics.
3. Integrar webhook básico.
4. Dashboards estatísticas alertas.

(Referências cruzadas: FEASIBILITY_PLAN.md (roadmap), TENANCY_MODEL.md (escopo por tenant), OPERATIONS.md (monitoramento), DATA_RETENTION_STRATEGY.md (granularidade métricas), PROVISIONING_API_SPEC.md (API regras futura).)
