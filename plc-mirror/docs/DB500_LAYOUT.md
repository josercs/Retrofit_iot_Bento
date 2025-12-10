# DB500 – Layout multi-máquinas (UDT_Maquina / UDT_Sensor)

Este documento descreve como organizar e ler um DB "monolítico" (DB500) contendo várias máquinas, cada uma com um conjunto fixo de sensores, usando o agente Edge deste repositório.

## Conceito
- No TIA Portal:
  - UDT_Sensor: campos Valor (REAL), Flags (BYTE), eventualmente padding de alinhamento.
  - UDT_Maquina: array Sensores[1..S], flags/status, contadores, reserva.
  - DB500: Maquinas[1..N] do tipo UDT_Maquina.
- No agente Python:
  - Leitura de um único DB grande por ciclo (ex.: 400–2000 bytes), calculando offsets por (máquina, sensor).

## Layout padrão (baseado no exemplo do TIA)
Estrutura por máquina (bloco com tamanho fixo):
- byte 0: flags (bits)
  - bit0: contador_bom_flag
  - bit1: contador_ruim_flag
  - bit2: status_maquina
- byte 1: reserva (BYTE)
- Sensores: começam em byte 2
  - Sensor j usa: REAL em offset (base_sensores + j*6)
  - Flags (BYTE) em offset (base_sensores + j*6 + 4)
- Contadores (Int):
  - contador_bom em offset base + 62
  - contador_ruim em offset base + 64

Constantes padrão no código:
- MACHINES = 5
- SENSORS_PER_MACHINE = 5
- MACHINE_BLOCK_SIZE = 66 bytes
- SENSOR_BLOCK_SIZE = 6 bytes
- OFF_SENSORS_START = 2

Você pode sobrescrever esses valores via `parser_opts` no `config.yaml` ou variáveis de ambiente.

## Configuração via `config.yaml` (recomendado)
No `config.yaml` (ou `config.yaml.example`):

- Em `dbs:` adicione o bloco do DB500 com `parser: db500` e `parser_opts`:

```yaml
source:
  ip: "192.168.0.121"
  rack: 0
  slot: 1
  poll_interval: 1.0

output:
  mode: "mqtt"
  mqtt:
    broker: "mosquitto"
    port: 8883
    topic: "plc/${TENANT_ID}/${PLC_ID}"
    tls: true
    ca_file: "/app/ca.crt"

metrics_port: 9108
store_path: "queue.sqlite"

dbs:
  - name: "processo"
    db_number: 500
    db_size: 400   # tamanho suficiente para N máquinas
    measurement: "s7_db500"
    parser: "db500"
    parser_opts:
      machines: 5
      sensors_per_machine: 5
      machine_block_size: 66
      sensor_block_size: 6
    tags:
      area: "linha1"
    fields:
      db: 500
```

O agente aplica `parser_opts` exportando variáveis de ambiente esperadas pelo `db500_reader` antes de cada leitura.

## Configuração via variáveis de ambiente (alternativa)
- DB500_MACHINES
- DB500_SENSORS_PER_MACHINE
- DB500_MACHINE_BLOCK_SIZE
- DB500_SENSOR_BLOCK_SIZE

Exemplo (Windows PowerShell, container ou serviço):
```powershell
$env:DB500_MACHINES = "8"
$env:DB500_SENSORS_PER_MACHINE = "5"
$env:DB500_MACHINE_BLOCK_SIZE = "66"
$env:DB500_SENSOR_BLOCK_SIZE = "6"
```

## Como adicionar mais máquinas no futuro
1. No TIA Portal:
   - Aumente `Maquinas[1..N]` no DB500 mantendo o mesmo UDT_Maquina.
   - Certifique-se de manter o bloco por máquina com o mesmo tamanho e ordem de campos (congelar layout).
   - Se houver mudança de layout, versionar: ex.: "DB500 v2" e atualizar os offsets.
2. No agente:
   - Ajuste `machines` em `parser_opts` do `config.yaml` (ou use `DB500_MACHINES`).
   - Ajuste `db_size` para cobrir `N * MACHINE_BLOCK_SIZE`.
   - Não é necessário editar o código.
3. Monitoramento:
   - No payload, o agente publicará `machines[]` com sensores/contadores.
   - Grafana/Telegraf devem ser ajustados para consumir os novos índices.

## Cálculo de offsets (fórmula)
- Base da máquina i (começando em 0): `base_i = i * MACHINE_BLOCK_SIZE`
- Base do sensor j: `s_base = base_i + OFF_SENSORS_START + j * SENSOR_BLOCK_SIZE`
- Valor do sensor: REAL em `s_base`
- Flags do sensor: BYTE em `s_base + 4`
- Contador bom: INT em `base_i + OFF_CONTADOR_BOM_INT`
- Contador ruim: INT em `base_i + OFF_CONTADOR_RUIM_INT`

## Script de diagnóstico
Use `_read_db.py` para verificar o DB rapidamente. Ele já usa os mesmos offsets e imprime um JSON com `machines`.

## Boas práticas
- Desligar “optimized block access” se estiver usando leitura por byte/offset (S7Comm/snap7).
- Nomear UDTs e campos de forma clara para manutenção.
- Documentar versão do layout quando alterar offsets.
- Garantir `db_size` suficiente para o número de máquinas.

---
Última atualização: alinhado com `src/db500_reader.py` e `src/agent.py`. 
