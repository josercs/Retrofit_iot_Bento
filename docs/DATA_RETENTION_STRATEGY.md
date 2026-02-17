# Estratégia de Retenção & Downsampling

## 1. Objetivo
Balancear custo de armazenamento e performance de consulta mantendo granularidade adequada para análise operacional e histórica.

## 2. Camadas de Dados
| Camada | Bucket | Granularidade | Retenção | Uso |
|--------|--------|---------------|----------|-----|
| Bruto | processo_raw | pontos originais (segundos) | variável/plano | insumos alert/diagnóstico curto prazo |
| Processado | processo | mesmas métricas com limpeza/conversões | variável/plano | dashboards padrão tempo recente |
| Agregado | processo_1m | média/estatísticas 1m | longa (>= 180d) | históricos, tendência, ML inicial |
| Frio | arquivo externo / object storage | parquet diário | anos | auditoria, ML avançado |

## 3. Retenção por Plano (Sugestão)
| Plano | processo_raw | processo | processo_1m | Arquivo Frio |
|-------|--------------|---------|-------------|--------------|
| Free | 3d | 7d | 30d | sob demanda |
| Pro | 7d | 30d | 180d | 365d |
| Enterprise | 30d | 90d | 365d | 5y |

## 4. Downsampling
- Tarefas Flux a cada 5m: lê últimos 5m de processo_raw e escreve em processo_1m (mean, min, max opcional).
- Campos boolean não agregados (usar sum para contagem de ocorrências ou keep último estado).

Exemplo script:
```flux
option task = {name: "downsample_1m", every: 5m}
from(bucket: "processo_raw")
  |> range(start: -5m)
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> to(bucket: "processo_1m")
```

## 5. Arquivamento Frio
- Job diário exporta séries do intervalo que excedeu retenção configurada para parquet (ex: Apache Arrow / Pandas) em object storage.
- Compactação gzip ou zstd.
- Nome arquivo: `<tenant_slug>/<YYYY>/<MM>/<DD>/<bucket>_<tenant_slug>_<YYYYMMDD>.parquet`.

## 6. Limpeza & Expurgo
- Expurgo automático executado pelo Influx conforme política de bucket.
- Monitorar backlog expurgo (metrics internal) se volume alto.

## 7. Cardinalidade & Otimizações
- Reduzir tags: somente tenant_id, plc_id, db, variáveis essenciais.
- Evitar tag com valores altamente variáveis (ex: sensor_serial se muitas instâncias).
- Alertar quando cardinalidade_series > limite por plano.

## 8. Cálculo Estimado de Storage
Fórmula aproximada:
```
bytes_por_ponto ≈ 50 (Influx compactado)
storage_raw_dia = pontos_dia * bytes_por_ponto
```
Exemplo Pro: 5k pontos/min => 7.2M/dia => ~360MB/dia => 7d ~2.5GB.

## 9. Monitoramento da Retenção
Métricas por tenant:
- storage_bytes (estimado)
- points_expired_dia (pontos removidos)
- downsample_lag_seconds (atraso tarefa)

Alertas:
- downsample_lag_seconds > 300.
- storage_bytes > 90% da projeção plano.

## 10. Migração de Políticas
Processo para mudar retenção:
1. Criar novo bucket com retenção desejada.
2. Habilitar dual-write (temporário) no Telegraf para bucket antigo e novo.
3. Cortar ingest bucket antigo após período transição.
4. Export e arquivar dados históricos excedentes.

## 11. Conformidade & Auditoria
- Parquet no armazenamento frio mantém histórico para análises forenses.
- Checklist mensal: integridade arquivos, checksum, acessos.

## 12. Próximos Passos
1. Implementar tarefa downsampling (Flux) no MVP.
2. Criar job estimativa storage por tenant.
3. Definir pipeline export parquet (script Python). 
4. Expor métricas de lag e storage em /usage.

(Referências cruzadas: FEASIBILITY_PLAN.md (objetivos), TENANCY_MODEL.md (impacto quotas), OPERATIONS.md (tarefas), PROVISIONING_API_SPEC.md (exposição uso), ALERT_ENGINE_SPEC.md (janelas temporal).)
