# Especificação API de Provisionamento

## 1. Objetivo
Fornecer endpoints REST para gerenciar tenants, dispositivos e credenciais necessárias ao ingestion (MQTT + Influx), suportando automação e integração com portais internos.

## 2. Princípios
- Stateless (JWT ou API Key para autenticação admin).
- Versionada: prefixo /v1.
- JSON consistente (snake_case). 
- Erros padronizados com código e mensagem.

## 3. Autenticação & Autorização
- Header: `Authorization: Bearer <token>` (admin / ops).
- Futuro: RBAC para permitir tenant admin gerenciar próprios devices.
- Rate limit: 100 requisições / min por chave.

## 4. Modelos
### Tenant
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
### Device
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
### Token / Credential
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
### Error
```json
{ "error": { "code": "TENANT_NOT_FOUND", "message": "Tenant id inválido" }}
```

## 5. Endpoints
### Tenants
| Método | Rota | Descrição | Código Sucesso |
|--------|------|-----------|---------------|
| POST | /v1/tenants | Criar tenant | 201 |
| GET | /v1/tenants | Listar tenants (pagina) | 200 |
| GET | /v1/tenants/{id} | Obter tenant | 200 |
| PATCH | /v1/tenants/{id} | Atualizar (name, plan, status) | 200 |
| DELETE | /v1/tenants/{id} | Encerrar (status=closed) | 204 |

### Devices
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/devices | Criar device (tenant_id, plc_id, type) |
| GET | /v1/devices?tenant_id= | Listar devices por tenant |
| GET | /v1/devices/{id} | Obter device |
| PATCH | /v1/devices/{id} | Atualizar (tags, active) |
| DELETE | /v1/devices/{id} | Remover (soft delete / active=false) |

### Credentials / Tokens
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/credentials | Criar credencial (tenant_id, device_id, kind) |
| GET | /v1/credentials?tenant_id= | Listar credenciais |
| DELETE | /v1/credentials/{id} | Revogar credencial |

### Usage / Quotas
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | /v1/tenants/{id}/usage | Dados agregados de uso e quotas |
| GET | /v1/tenants/{id}/metrics | Métricas recentes operacionais |

### Actions (Operações Especiais)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /v1/tenants/{id}/rotate-credentials | Rotacionar credenciais (mqtt/influx) |
| POST | /v1/devices/{id}/reissue-config | Reemitir arquivo config Edge |

## 6. Regras de Validação
- `slug` único global, regex: ^[a-z0-9-_]{3,32}$.
- `plc_id` único por tenant.
- `type` em enum suportado.
- `plan` em {free, pro, enterprise}.
- Limite de devices conforme plano (bloquear criação acima quota).

## 7. Paginação & Filtros
- Query params: `page`, `page_size` (default 50, max 200).
- Filtros: status (tenants), active (devices).
- Resposta inclui `total_items` e `next_page`.

## 8. Erros Padronizados
| Código | HTTP | Mensagem Exemplo |
|--------|------|------------------|
| VALIDATION_ERROR | 400 | Campo plan inválido |
| TENANT_NOT_FOUND | 404 | Tenant id inválido |
| DEVICE_NOT_FOUND | 404 | Device não encontrado |
| QUOTA_EXCEEDED | 409 | Limite de devices atingido |
| CREDENTIAL_NOT_FOUND | 404 | Credencial não existe |
| UNAUTHORIZED | 401 | Token inválido |
| FORBIDDEN | 403 | Sem permissão |

## 9. Segurança
- Rate limit per IP e por token.
- Secrets retornados somente na criação.
- Hash + salt para senhas MQTT (compatível com mosquitto). 
- Revogação imediata atualiza ACL.

## 10. Auditoria
- Tabela audit_log com: timestamp, actor, resource, action, before, after.
- Export mensal para bucket audit.

## 11. Fluxo de Onboarding Automático
1. POST /tenants (plan=pro).
2. POST /devices (plc_id list).
3. POST /credentials (mqtt + influx para cada device ou tenant-level).
4. Gerar arquivo YAML edge config consolidado.
5. Registrar dashboards iniciais via Grafana API.

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
- Webhooks para eventos provisioning.
- RBAC granular (roles por tenant).
- Suporte a chaves de API temporárias.

## 14. Health & Observabilidade
- Endpoint /v1/health (status básico).
- Métricas Prometheus: http_requests_total, latency buckets, provision_actions_total, quota_exceeded_total.

## 15. Próximos Passos
1. Definir contrato OpenAPI (swagger.yaml).
2. Implementar protótipo em Python FastAPI.
3. Integrar geração de credenciais MQTT (atualizar aclfile).
4. Automação dashboards Grafana (import JSON por tenant).

(Referências cruzadas: TENANCY_MODEL.md (modelagem), FEASIBILITY_PLAN.md (roadmap), OPERATIONS.md (procedimentos), ALERT_ENGINE_SPEC.md (uso métricas), DATA_RETENTION_STRATEGY.md (impacto quotas).)
