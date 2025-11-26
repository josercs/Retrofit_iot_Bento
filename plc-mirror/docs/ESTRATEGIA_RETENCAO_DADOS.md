# Estratégia de Retenção & Downsampling

## 1. Objetivo
Balancear custo de armazenamento e performance de consulta mantendo granularidade adequada para análise operacional e histórica.

## 2. Camadas de Dados
| Camada | Bucket | Granularidade | Retenção | Uso |
|--------|--------|---------------|----------|-----|
| Bruto | processo_raw | pontos originais (segundos) | variável/plano | insumos de alerta/diagnóstico curto prazo |
| Processado | processo | mesmas métricas com limpeza/conversões | variável/plano | dashboards padrão recente |
| Agregado | processo_1m | média/estatísticas 1m | longa (>= 180d) | históricos, tendência, ML inicial |
| Frio | armazenamento externo (object storage) | parquet diário | anos | auditoria, ML avançado |

## 3. Retenção por Plano (Sugestão)
| Plano | processo_raw | processo | processo_1m | Arquivo Frio |
|-------|--------------|---------|-------------|--------------|
| Free | 3d | 7d | 30d | sob demanda |
| Pro | 7d | 30d | 180d | 365d |
| Enterprise | 30d | 90d | 365d | 5y |

## 4. Downsampling
- Tarefa Flux a cada 5m: lê últimos 5m de `processo_raw` e escreve em `processo_1m` (mean, min, max opcional).
- Campos boolean: usar sum para contagem ou último estado para snapshot.

Exemplo script:
```flux
option task = {name: "downsample_1m", every: 5m}
from(bucket: "processo_raw")
  |> range(start: -5m)
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> to(bucket: "processo_1m")
```

## 5. Arquivamento Frio
- Job diário exporta séries que excederam retenção configurada para parquet (Arrow/Pandas) em object storage.
- Compactação gzip ou zstd.
- Nome arquivo: `<locatario_slug>/<YYYY>/<MM>/<DD>/<bucket>_<locatario_slug>_<YYYYMMDD>.parquet`.

## 6. Limpeza & Expurgo
- Expurgo automático executado pelo Influx conforme política do bucket.
- Monitorar backlog de expurgo (métricas internas) se volume alto.

## 7. Cardinalidade & Otimizações
- Reduzir tags: somente locatario_id, plc_id, db e variáveis essenciais.
- Evitar tag com valores altamente variáveis (ex: sensor_serial).
- Alertar quando `cardinality_series` > limite por plano.

## 8. Cálculo Estimado de Storage
Fórmula aproximada:
```
bytes_por_ponto ≈ 50 (Influx compactado)
storage_raw_dia = pontos_dia * bytes_por_ponto
```
Exemplo Pro: 5k pontos/min => 7.2M/dia ≈ 360MB/dia => 7d ≈ 2.5GB.

## 9. Monitoramento da Retenção
Métricas por locatário:
- storage_bytes (estimado)
- points_expired_dia (pontos removidos)
- downsample_lag_seconds (atraso da tarefa)

Alertas:
- downsample_lag_seconds > 300.
- storage_bytes > 90% da projeção do plano.

## 10. Migração de Políticas
1. Criar novo bucket com retenção desejada.
2. Habilitar dual‑write (temporário) no Telegraf para bucket antigo e novo.
3. Cortar ingestão do bucket antigo após período de transição.
4. Exportar e arquivar dados históricos excedentes.

## 11. Conformidade & Auditoria
- Parquet em armazenamento frio preserva histórico para análises forenses.
- Checklist mensal: integridade de arquivos, checksum, acessos.

## 12. Próximos Passos
1. Implementar tarefa de downsampling (Flux) no MVP.
2. Criar job de estimativa de storage por locatário.
3. Definir pipeline de export para parquet (script Python).
4. Expor métricas de lag e storage em /usage.

(Referências: PLANO_VIABILIDADE.md (objetivos), MODELO_MULTI_LOCATARIOS.md (impacto quotas), OPERACOES.md (tarefas), ESPECIFICACAO_API_PROVISIONAMENTO.md (exposição de uso), ESPECIFICACAO_MOTOR_ALERTAS.md (janelas temporais).)