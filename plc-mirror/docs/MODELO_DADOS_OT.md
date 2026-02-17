# Modelo de Dados OT Definitivo (Retrofit IoT Bento)

## 1. Measurement: s7_db1
- **Descrição:** Dados de produção e variáveis OT vindas do PLC.
- **Tags obrigatórias:**
  - ip (string) — IP do PLC
  - db (int/string) — Número do DB/área lógica do PLC
- **Campos (_field):**
  - contador_bom (int) — Contador de peças boas
  - contador_ruim (int) — Contador de peças ruins
  - status_maquina (int/bool) — 1=ligada, 0=parada
  - maquina_ligada (int/bool) — 1=ligada, 0=parada
  - AI_Corrente (float) — Corrente analógica
  - AI_Vibracao (float) — Vibração analógica
  - temperatura (float)
  - vibracao (float)
  - (outros campos de processo, conforme necessidade real)

## 2. Measurement: prometheus
- **Descrição:** Métricas de health, heartbeat e monitoramento do Edge Agent.
- **Tags obrigatórias:**
  - ip (string) — IP do agente/PLC
  - db (int/string) — DB monitorado (quando aplicável)
  - plc_id (string) — Identificador lógico do PLC (quando aplicável)
- **Campos (_field):**
  - edge_up (int/bool) — 1=agente ativo, 0=inativo
  - plc_read_ok_total (int) — Leituras bem-sucedidas acumuladas
  - edge_backlog_size (int) — Tamanho do backlog do agente
  - plc_read_latency_ms (float) — Latência de leitura do PLC (ms)
  - (outros campos de health, conforme necessidade real)

---

## Regras e Boas Práticas
- Sempre usar as tags ip e db em todos os pontos de coleta.
- Se disponível, usar plc_id como identificador lógico (facilita multi-máquina).
- Não misturar domínios: produção (s7_db1) ≠ health (prometheus).
- Campos adicionais devem ser documentados e padronizados.
- Time range sempre dinâmico (v.timeRangeStart/Stop) nos dashboards.
- Variáveis de dashboard: ip, db, plc_id.

---

## Exemplos de Payload (JSON)

### Produção
{"ip":"192.168.0.121","db":1,"values":{"contador_bom":10,"contador_ruim":2,"status_maquina":1}}

### Sensor
{"ip":"192.168.0.121","db":1,"machine_index":1,"sensor_index":2,"values":{"temperatura":62.5,"vibracao":0.12}}

### Health
_measurement: prometheus, _field: edge_up, ip: "192.168.0.121", db: 1, plc_id: "PLC01", _value: 1

---

Este documento reflete fielmente o modelo de dados já utilizado e validado no ambiente Retrofit IoT Bento.
