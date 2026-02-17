# MODELO DE DADOS UNIFICADO - VERSÃO 2.0

bucket: processo

---

## 1. HEALTH/STATUS (Edge + PLC)
measurement: edge_status
  tags:
    - site
    - line
    - machine_id
    - edge_id
    - plc_type
  fields:
    - edge_up
    - plc_connected
    - plc_latency_ms
    - backlog_size
    - cpu_usage
    - mem_usage

## 2. PRODUCTION COUNTERS
measurement: production
  tags:
    - site
    - line
    - machine_id
    - product_code
  fields:
    - good_count
    - reject_count
    - total_count
    - cycle_time_ms

## 3. MACHINE STATE
measurement: machine_state
  tags:
    - site
    - line
    - machine_id
  fields:
    - running
    - faulted
    - mode
    - speed_percent

## 4. SENSOR DATA
measurement: sensors
  tags:
    - site
    - line
    - machine_id
    - sensor_type
    - sensor_id
  fields:
    - value
    - unit
    - status

## 5. EVENTS/ALARMS
measurement: events
  tags:
    - site
    - line
    - machine_id
    - severity
    - category
  fields:
    - event_code
    - message
    - acknowledged

---

# Exemplos de Payloads

## edge_status
{
  "measurement": "edge_status",
  "tags": {"site": "RS01", "line": "L1", "machine_id": "M01", "edge_id": "E01", "plc_type": "s7"},
  "fields": {"edge_up": 1, "plc_connected": 1, "plc_latency_ms": 12.5, "backlog_size": 0, "cpu_usage": 22.1, "mem_usage": 45.3}
}

## production
{
  "measurement": "production",
  "tags": {"site": "RS01", "line": "L1", "machine_id": "M01", "product_code": "P123"},
  "fields": {"good_count": 1200, "reject_count": 15, "total_count": 1215, "cycle_time_ms": 1200}
}

## machine_state
{
  "measurement": "machine_state",
  "tags": {"site": "RS01", "line": "L1", "machine_id": "M01"},
  "fields": {"running": 1, "faulted": 0, "mode": 1, "speed_percent": 85}
}

## sensors
{
  "measurement": "sensors",
  "tags": {"site": "RS01", "line": "L1", "machine_id": "M01", "sensor_type": "temperature", "sensor_id": "T01"},
  "fields": {"value": 24.5, "unit": "C", "status": 1}
}

## events
{
  "measurement": "events",
  "tags": {"site": "RS01", "line": "L1", "machine_id": "M01", "severity": "warning", "category": "quality"},
  "fields": {"event_code": "Q001", "message": "Peça fora de especificação", "acknowledged": 0}
}

---

# Queries Flux (exemplo)

## Qualidade (%)
from(bucket: "processo")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "production" and (r._field == "good_count" or r._field == "reject_count"))
  |> filter(fn: (r) => r.site == "${site}" and r.line == "${line}" and r.machine_id == "${machine_id}")
  |> difference()
  |> reduce(
    fn: (r, acc) => ({
      good: acc.good + if r._field == "good_count" then r._value else 0,
      bad:  acc.bad  + if r._field == "reject_count" then r._value else 0
    }),
    identity: {good: 0.0, bad: 0.0}
  )
  |> map(fn: (r) => ({ _value: r.good / (r.good + r.bad) * 100.0 }))

## Disponibilidade (%)
from(bucket: "processo")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "machine_state" and r._field == "running")
  |> filter(fn: (r) => r.site == "${site}" and r.line == "${line}" and r.machine_id == "${machine_id}")
  |> aggregateWindow(every: 1m, fn: mean)
  |> map(fn: (r) => ({ _value: r._value * 100.0 }))

## Performance (pcs/min)
from(bucket: "processo")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "production" and r._field == "good_count")
  |> filter(fn: (r) => r.site == "${site}" and r.line == "${line}" and r.machine_id == "${machine_id}")
  |> derivative(unit: 1m, nonNegative: true)
  |> aggregateWindow(every: 1m, fn: mean)

---

# Template de Dashboard

Painéis recomendados:
- Disponibilidade (%)
- Performance (pcs/min)
- Qualidade (%)
- Edge UP
- Leituras OK/min
- Falhas/min
- Backlog
- Latência PLC (ms)
- Alarmes recentes
- Sensores críticos

Todos filtráveis por site, line, machine_id, segment, product_code, etc.
