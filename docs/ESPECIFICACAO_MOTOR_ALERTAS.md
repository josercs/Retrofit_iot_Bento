# Especificação do Motor de Alertas

## 1. Objetivo
Detectar condições críticas ou anômalas em métricas de processo e infraestrutura, gerando notificações confiáveis e rápidas por locatário.

## 2. Tipos de Alertas (MVP)
| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| limiar (threshold) | Valor acima/abaixo de limite por janela | vib_mean_1m > 12.5 |
| ausência (absence) | Falta de atualização (heartbeat) | edge_up ausente > 30s |
| variação (rate_change) | Mudança brusca (derivada) | corrente_derivada < -5 A/min |
| porcentagem (percentage) | Proporção fora de faixa | qualidade_pct < 0.92 |

Futuro: padrão (sequência de eventos), anomalia (z‑score/IQR), composta (combinação de regras).

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

Ausência:
```json
{
  "type": "absence",
  "metric": "edge_up",
  "missing_for_seconds": 30,
  "severity": "critical"
}
```

Variação:
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
1. Carregar regras ativas por locatário (cache em memória).
2. Obter lote de métricas recentes (consulta Influx ou stream).
3. Avaliar cada regra:
   - threshold: manter contador do tempo em condição.
   - absence: verificar timestamp do último ponto.
   - rate_change: calcular derivada (último vs anterior / tempo).
4. Gerar evento de alerta se condição satisfeita e fora do cooldown.
5. Persistir evento (bucket `alert_events` ou DB relacional).

## 5. Estado & Cooldown
- Máquina de estados por regra: OK -> DISPARANDO -> RESFRIANDO -> OK.
- RESFRIANDO impede disparos repetidos durante `cooldown_seconds`.

## 6. Notificações
Canal mínimo: email + webhook.
Formato webhook POST JSON:
```json
{
  "alert_id": "uuid",
  "locatario": "plantaA",
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
| alerts_fired_total | Total de disparos |
| alerts_active | Número atual em estado disparando |
| evaluation_duration_ms | Tempo de avaliação do ciclo |
| rules_loaded | Quantidade de regras ativas |
| notifications_failed_total | Falhas de envio |

## 8. Armazenamento
- Regras: tabela `alert_rules` (DB relacional) ou bucket de configuração.
- Eventos: bucket `alert_events` (tags: locatario_id, severity, rule_id).

## 9. Escalabilidade
- Pool de workers avaliando regras em paralelo (shard por locatário).
- Se > N regras por locatário, dividir avaliação em janelas.
- Fila interna para eventos (RabbitMQ / Redis Streams futuramente) se volume alto.

## 10. Precisão & Deduplicação
- Hash do evento (rule_id + started_at arredondado) evita duplicados.
- Comparar último valor enviado para decidir re‑notificação (se delta > x%).

## 11. API de Gestão de Regras (Futuro)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/alerts/rules | Criar regra |
| GET | /v1/alerts/rules?tenant_id= | Listar regras |
| PATCH | /v1/alerts/rules/{id} | Atualizar |
| DELETE | /v1/alerts/rules/{id} | Remover |
| GET | /v1/alerts/events?tenant_id= | Listar eventos |

## 12. Segurança
- Regras acessíveis somente ao locatário proprietário.
- Sanitização de entradas (nomes de métricas) para evitar injeção em consultas.
- Rate limit para criação/alteração de regras.

## 13. Testes & Qualidade
- Teste unitário limiar (disparo após tempo).
- Teste ausência (não dispara antes do limite).
- Teste cooldown (não dispara repetido).
- Teste variação (derivada negativa aciona).

## 14. Roadmap de Extensões
| Fase | Item |
|------|------|
| F1 | Regras compostas (AND/OR) |
| F2 | Anomalia IQR / z‑score automática |
| F2 | Escalonamento multi‑severidade |
| F3 | Aprendizado sazonal (estilo Prometheus) |

## 15. Próximos Passos
1. Implementar protótipo limiar + ausência.
2. Persistir eventos e expor /metrics.
3. Integrar webhook básico.
4. Criar dashboards de estatísticas de alertas.

(Referências cruzadas: PLANO_VIABILIDADE.md (roadmap), MODELO_MULTI_LOCATARIOS.md (escopo), OPERACOES.md (monitoramento), ESTRATEGIA_RETENCAO_DADOS.md (granularidade), ESPECIFICACAO_API_PROVISIONAMENTO.md (API futura).)