# Arquitetura SaaS (Resumo de Viabilidade)

## Objetivo
Transformar o agente/stack atual em um serviço SaaS de IoT industrial multi-tenant.

## Componentes propostos
- Edge agent: leve, com store-and-forward, métricas e autenticação por token/mTLS.
- Ingestão: HTTP+MQTT gateway escalável (k8s), com fila gerenciada (Kafka/PubSub/Event Hubs).
- Processamento: consumidores stateless que validam e roteiam dados.
- Armazenamento: TSDB multi-tenant (Influx Cloud/Timescale/ClickHouse).
- Observabilidade/UI: Grafana multi-tenant e métricas centralizadas.
- Control-plane: API de provisionamento (tenant, devices, tokens), UI e billing.

## Multi-tenant
- Isolamento lógico por tenant (bucket/tag por tenant) com quotas e retenção por plano.
- Autorização por token e ACLs por tópico/HTTP endpoint.

## Segurança
- mTLS/TLS, rotação de segredos, secrets no Vault/KMS.
- Logs e auditoria por tenant.

## Roadmap MVP
- Onboarding/keys, ingest gateway simples, TSDB com buckets por tenant, dashboards template.
- Edge com suporte a token e `tenant_id` no payload.

## Riscos
- Custos de TSDB em larga escala, compliance industrial, redes restritivas.

---

## 1. Proposta de Valor & Diferenciação
Problema: soluções IoT industriais tradicionais são caras, lentas para implantar e com UX antiquada.
Valor: implantação em horas (gateway plug-and-play), dashboards prontos para KPIs (OEE, energia), custo previsível, evolução rápida (features em semanas, não anos), IA incremental.
Por que não usar somente cloud genérica (AWS/Azure IoT)? → Curva de complexidade alta, integração pesada e pouca customização de métricas industriais out‑of‑the‑box.

## 2. Funcionalidades por Estágio
| Estágio | Funcionalidades |
|---------|-----------------|
| MVP | Telemetria tempo real, dashboards template, alertas básicos, multi-tenant, API provisionamento |
| Growth | Manutenção preditiva inicial, relatórios agendados, integrações ERP/MES, gestão de energia |
| Scale | IA avançada (anomalias multivariadas), digital twin, automações condicionais, RBAC granular |
| Enterprise | SLA 99.9%, auditoria completa, single sign-on, criptografia end-to-end, OTA firmware |

## 3. Arquitetura Detalhada
```mermaid
flowchart LR
	subgraph Edge
		PLC[PLCs / Sensores]
		GW[Gateway / Edge Agent]
	end
	PLC --> GW
	GW -->|MQTT TLS| BRK[Broker MQTT/Kafka Bridge]
	BRK --> ING[Ingest Service]
	ING --> VAL[Validação / Normalização]
	VAL --> TS[(Time-Series DB)]
	VAL --> QUEUE[(Fila Eventos)]
	QUEUE --> PROC[Processadores / Enriquecimento]
	PROC --> TS
	TS --> API[API GraphQL/REST]
	API --> UI[Web App / Dashboards]
	TS --> AI[Motor IA/Anomalias]
	AI --> UI
	API --> INT[Integrações ERP/MES]
	class BRK,ING,VAL,PROC,TS,API,AI,INT infra;
	classDef infra fill=#eef,stroke=#468,stroke-width=1px;
```

### Principais Fluxos
1. Coleta → publish MQTT.
2. Ingest Service valida assinatura, quota, formato.
3. Normalização adiciona metadata (tenant, plc_id, location).
4. Persistência TSDB + fila eventos para processamentos assíncronos (alertas, IA, agregações).
5. API serve consultas, listagem de ativos e gera tokens.
6. IA lê janelas agregadas (prometheus + séries) para detecção precoce.

## 4. Multi-Tenancy & Isolamento
Estratégias possíveis:
| Camada | Técnica |
|--------|--------|
| MQTT | Tópico raiz por tenant: `plc/<tenant>/...` + ACL |
| TSDB | Bucket por tenant (Influx) ou schema por tenant (Timescale) |
| Cache | Prefixo de chave Redis `tenant:<id>:` |
| Armazenamento frio | Pasta/objeto segregado (S3: `tenant-id/YYYY/MM/`) |
| API | Claims JWT: tenant_id, roles, quotas |

Quota enforcement: contagem de pontos/hora, dispositivos ativos, alertas configurados.

## 5. Segurança & Conformidade
| Área | Medida |
|------|--------|
| Transporte | TLS 1.2+, mTLS para edge crítico |
| Autenticação | JWT/OAuth2 + refresh + device token rotacionável |
| Segredos | Vault/KMS + rotação trimestral senhas técnicas |
| Auditoria | Log append-only (WORM) para ações de usuários |
| LGPD | Minimizar dados pessoais, pseudonimizar operador |
| Hardening | CIS benchmarks em containers/base OS |
| Firmware | Assinatura e verificação OTA (Ed25519) |

Detecção de anomalias de segurança: regras sobre picos de mensagens, mudanças bruscas em configuração de alertas.

## 6. Motor de IA (Evolução)
Fase 1: Regras dinâmicas (limiares adaptativos, EWMA).
Fase 2: Detecção de anomalias multivariada (Isolation Forest / PCA reconstruction error).
Fase 3: Modelos supervisionados (predictive maintenance) com labels coletados de histórico de falhas.
Fase 4: Prescriptive analytics (qual ação executar para evitar parada).

Pipeline IA:
1. Collector (TSDB) → job de agregação (janelas 1m/5m/1h).
2. Feature store → treino batch.
3. Modelo versionado → serving em endpoint gRPC/REST.
4. Alert engine consome score e gera evento.

## 7. Observabilidade Interna
Métricas chave:
| Métrica | Descrição |
|---------|-----------|
| ingest_messages_total | Total de mensagens recebidas (por tenant) |
| ingest_lag_ms | Latência do publish até persistência |
| parse_error_total | Falhas de parsing JSON/protocolo |
| backlog_size | Itens no buffer store-forward edge |
| ai_inference_latency_ms | Tempo de resposta dos modelos |
| quota_usage_percent | Uso de quota vs limite plano |

Logs estruturados (JSON) com `tenant_id`, `trace_id`, `device_id` para correlação.

## 8. Escalabilidade & Partições
Escala vertical inicial usando Mosquitto; migração para Kafka quando: > 20k msgs/s ou necessidade de replay/retention granular.
Particionamento por tenant garante isolamento de throughput (Kafka topics `tenant.<id>.telemetry`).

## 9. Performance & Custos
Estimativa inicial por dispositivo (mensagens 1/s, ~150 bytes → ~13 MB/dia):
| Item | Custo estimado mensal (exemplo) |
|------|---------------------------------|
| Armazenamento quente (30d) | Compressão ~3x → ~130 MB → R$ baixo |
| Egress dashboards | Cache → ~5% dos dados |
| CPU ingest | ~0.05 vCPU por 1k dispositivos |
Downsampling: janelas 1m para métricas de consumo reduzindo 60x volume histórico.

## 10. Monetização Detalhada
Dimensões: dispositivos, mensagens/mês, retenção, IA ativa, integrações.
Upsell gatilhos: necessidade de maior retenção (>30d), manutenção preditiva, integrações ERP, SLA suporte.

## 11. Roadmap Trimestral
| Quarter | Entregas |
|---------|----------|
| Q1 | MVP (telemetria, alertas básicos, multi-tenant, provisioning) |
| Q2 | Integrações ERP, relatórios agendados, downsampling automatizado |
| Q3 | IA preditiva inicial + gestão de energia + RBAC avançado |
| Q4 | OTA firmware, digital twin lite, prescriptive analytics |

## 12. Go-To-Market
ICP inicial: fábricas discretas 10–50 máquinas; dor: falta visibilidade OEE + desperdício energia.
Canal: integradores locais + parceiros automação.
Oferta PoC: 30 dias, kit gateway + dashboard produtividade + relatório final (ROI estimado).

## 13. Riscos & Mitigações (Expandido)
| Risco | Mitigação |
|-------|-----------|
| Explosão custos storage | Downsampling + cold storage S3 + limites por plano |
| Latência rede industrial | Buffer local + compressão + retries exponenciais |
| Segurança gateway | Hardening + verificação assinatura OTA |
| Vendor lock-in TSDB | Abstração storage (interface) + export routine |
| Adoção lenta | Kits rápidos + casos de sucesso públicos |

## 14. Métricas de Negócio
| Métrica | Objetivo inicial |
|---------|------------------|
| Activation Rate (30d) | > 70% gateways enviados ativos |
| Churn mensal | < 3% |
| Ticket médio | Crescer 15% após upsell IA |
| MTTD falhas críticas | < 5 min |
| Redução downtime reportado | > 10% em 6 meses |

## 15. Checklist Produção (Hardening)
1. TLS mTLS broker habilitado.
2. Tokens com escopo mínimo (write/ read separated).
3. Alertas de quota 80%.
4. Backup TSDB diário + teste restore mensal.
5. Política de rota edge → cloud com watchdog offline.
6. CI/CD com scan dependências (SCA) + lint infra (Terraform validate).

## 16. Padrões de Código Edge
* Reconnect resiliente MQTT.
* Enfileirar antes de publicar (batch) para reduzir overhead TLS.
* Timeout leitura PLC configurável.
* Log estruturado (JSON) opcional.

## 17. Evolução de Protocolos
Adicionar drivers: OPC-UA, Modbus TCP, Ethernet/IP, MQTT Sparkplug B (payload padronizado), LoRaWAN gateway integração.

## 18. Estratégia de Exportação Dados
* APIs / GraphQL.
* Bulk export parquet para data lake (S3 + Glue Catalog).
* Webhook eventos (alertas) para sistemas externos.

## 19. Considerações de Compliance
* Guardar somente dados técnicos (evitar PII).
* Registros de acesso (audit) retidos >= 1 ano.
* Criptografia at-rest (disco + backups). 

## 20. Próximos Passos Imediatos (do projeto atual)
1. Introduzir reconexão persistente (reduz latência publish). 
2. Converter tenant/plc a tags exclusivamente (remover duplicação field). 
3. Implementar canal de downsampling 1m → 5m → 1h. 
4. Criar script de verificação de quota local. 
5. Adicionar testes de regressão para store-forward.

---
> Documento expandido para orientar evolução de MVP a plataforma SaaS completa.
