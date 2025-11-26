# Especificação da API de Provisionamento

## 1. Objetivo
Fornecer endpoints REST para gerenciar locatários, dispositivos e credenciais necessárias à ingestão (MQTT + Influx), suportando automação e integração com portais internos.

## 2. Princípios
- Stateless (JWT ou API Key para autenticação administrativa).
- Versionada: prefixo /v1.
- JSON consistente (snake_case).
- Erros padronizados com código e mensagem.

## 3. Autenticação & Autorização
- Header: `Authorization: Bearer <token>` (admin / ops).
- Futuro: RBAC para permitir admin do locatário gerenciar seus próprios dispositivos.
- Rate limit: 100 requisições / minuto por chave.

## 4. Modelos
### Locatário
```json
{
  "id": "uuid",
  "slug": "plantaA",
  "name": "Planta A",
  "plan": "pro",
  "status": "active",
  "created_at": "2025-01-10T12:00:00Z"
}
```
### Dispositivo
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "plc_id": "prensa1",
  "type": "siemens_s7",
  "tags": {"setor": "embalagem"},
  "active": true,
  "created_at": "2025-01-10T12:05:00Z"
}
```
### Credencial / Token
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "device_id": "uuid",
  "kind": "mqtt" | "influx" | "grafana",
  "username": "t_plantaA_prensa1",
  "secret": "(não retornado após criação)",
  "scopes": ["publish:plc/plantaA/prensa1"],
  "created_at": "2025-01-10T12:06:00Z",
  "expires_at": null
}
```
### Erro
```json
{ "error": { "code": "TENANT_NOT_FOUND", "message": "Locatário id inválido" }}
```

## 5. Endpoints
### Locatários
| Método | Rota | Descrição | Código Sucesso |
|--------|------|-----------|---------------|
| POST | /v1/tenants | Criar locatário | 201 |
| GET | /v1/tenants | Listar locatários (pagina) | 200 |
| GET | /v1/tenants/{id} | Obter locatário | 200 |
| PATCH | /v1/tenants/{id} | Atualizar (name, plan, status) | 200 |
| DELETE | /v1/tenants/{id} | Encerrar (status=closed) | 204 |

### Dispositivos
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/devices | Criar dispositivo (tenant_id, plc_id, type) |
| GET | /v1/devices?tenant_id= | Listar dispositivos por locatário |
| GET | /v1/devices/{id} | Obter dispositivo |
| PATCH | /v1/devices/{id} | Atualizar (tags, active) |
| DELETE | /v1/devices/{id} | Remover (soft delete / active=false) |

### Credenciais / Tokens
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/credentials | Criar credencial (tenant_id, device_id, kind) |
| GET | /v1/credentials?tenant_id= | Listar credenciais |
| DELETE | /v1/credentials/{id} | Revogar credencial |

### Uso / Quotas
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | /v1/tenants/{id}/usage | Dados agregados de uso e quotas |
| GET | /v1/tenants/{id}/metrics | Métricas operacionais recentes |

### Ações Especiais
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/tenants/{id}/rotate-credentials | Rotacionar credenciais (mqtt/influx) |
| POST | /v1/devices/{id}/reissue-config | Reemitir arquivo de configuração Edge |

## 6. Regras de Validação
- `slug` único global, regex: ^[a-z0-9-_]{3,32}$.
- `plc_id` único por locatário.
- `type` em enum suportado.
- `plan` em {free, pro, enterprise}.
- Limite de dispositivos conforme plano (bloquear criação acima da quota).

## 7. Paginação & Filtros
- Query params: `page`, `page_size` (padrão 50, máx 200).
- Filtros: status (locatários), active (dispositivos).
- Resposta inclui `total_items` e `next_page`.

## 8. Erros Padronizados
| Código | HTTP | Mensagem Exemplo |
|--------|------|------------------|
| VALIDATION_ERROR | 400 | Campo plan inválido |
| TENANT_NOT_FOUND | 404 | Locatário id inválido |
| DEVICE_NOT_FOUND | 404 | Dispositivo não encontrado |
| QUOTA_EXCEEDED | 409 | Limite de dispositivos atingido |
| CREDENTIAL_NOT_FOUND | 404 | Credencial não existe |
| UNAUTHORIZED | 401 | Token inválido |
| FORBIDDEN | 403 | Sem permissão |

## 9. Segurança
- Rate limit por IP e por token.
- Segredos retornados somente na criação.
- Hash + salt para senhas MQTT (compatível mosquitto).
- Revogação imediata atualiza ACL.

## 10. Auditoria
- Tabela audit_log: timestamp, actor, resource, action, before, after.
- Exportação mensal para bucket audit.

## 11. Fluxo de Onboarding Automático
1. POST /tenants (plan=pro).
2. POST /devices (lista plc_id).
3. POST /credentials (mqtt + influx para cada dispositivo ou nível locatário).
4. Gerar arquivo YAML de configuração do agente edge.
5. Registrar dashboards iniciais via API Grafana.

## 12. Exemplo Resposta /usage
```json
{
  "tenant_id": "uuid",
  "plan": "pro",
  "devices": 12,
  "devices_quota": 20,
  "points_per_min_avg": 2100,
  "points_quota": 5000,
  "storage_estimate_gb": 12.4,
  "alerts_active": 14,
  "alerts_quota": 50,
  "cardinality_series": 180000
}
```

## 13. Extensões Futuras
- Webhooks para eventos de provisionamento.
- RBAC granular (papéis por locatário).
- Suporte a chaves de API temporárias.

## 14. Saúde & Observabilidade
- Endpoint /v1/health (status básico).
- Métricas Prometheus: http_requests_total, histogramas de latência, provision_actions_total, quota_exceeded_total.

## 15. Próximos Passos
1. Definir contrato OpenAPI (swagger.yaml).
2. Implementar protótipo em FastAPI.
3. Integrar geração de credenciais MQTT (atualizar aclfile).
4. Automatizar import de dashboards Grafana por locatário.

(Referências cruzadas: MODELO_MULTI_LOCATARIOS.md (modelagem), PLANO_VIABILIDADE.md (roadmap), OPERACOES.md (procedimentos), ESPECIFICACAO_MOTOR_ALERTAS.md (uso de métricas), ESTRATEGIA_RETENCAO_DADOS.md (impacto quotas).)