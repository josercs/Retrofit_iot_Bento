# Configuração do Agente (pt-BR)

Este documento descreve as chaves do `config.yaml` e as variáveis de ambiente suportadas.

## Arquivo config.yaml
- source:
  - ip (string): IP do PLC de origem.
  - rack (int): rack (padrão 0).
  - slot (int): slot (padrão 1).
  - db_number (int): número do DB.
  - db_size (int): tamanho em bytes do DB.
  - poll_interval (float): intervalo de leitura em segundos.
- output:
  - mode (string): stdout | mqtt | http
  - mqtt:
  - broker, port, topic, qos, retain
    - username, password
    - tls (bool), ca_file, cert_file, key_file, tls_insecure (bool)
  - http:
    - url, timeout, headers, tls_verify (bool)
- metrics_port (int): porta HTTP para /metrics e dashboard mínimo.
- store_path (string): caminho do arquivo SQLite (fila local).
 - tenant_id (string, opcional): identificador do tenant (cliente) para SaaS.
 - plc_id (string, opcional): identificador lógico do PLC no tenant.

## Variáveis de Ambiente
Sobrescrevem as chaves acima (útil em containers):
- PLC_IP → source.ip
- DB_NUMBER → source.db_number
- DB_SIZE → source.db_size
- OUTPUT_MODE → output.mode
- METRICS_PORT → metrics_port
- TENANT_ID → tenant_id
- PLC_ID → plc_id

### Placeholders no tópico MQTT
Use placeholders `${TENANT_ID}` e `${PLC_ID}` no tópico para roteamento multi‑tenant, por exemplo:
```
output:
  mode: mqtt
  mqtt:
    topic: "plc/${TENANT_ID}/${PLC_ID}"
```
O agente substitui com valores do YAML/env; se não conseguir resolver, volta para `plc/db1`.

### Derivação de tags no Telegraf
Mesmo que `tenant_id` e `plc_id` não venham no JSON, o Telegraf está configurado para derivar do tópico MQTT (via `topic_tag` + `processors.regex`), assumindo o padrão `plc/<tenant>/<plc>`. Isso torna o pipeline mais robusto e compatível com roteamento por tópico.
- MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_USERNAME, MQTT_PASSWORD
- MQTT_TLS, MQTT_CA_FILE, MQTT_CERT_FILE, MQTT_KEY_FILE, MQTT_TLS_INSECURE
- HTTP_URL

Observações:
- Valores booleanos devem ser passados como strings "true"/"false".
- Se chaves MQTT forem colocadas diretamente em `output` (erro de indentação), o agente tenta normalizar automaticamente para `output.mqtt`.

## Exemplo de payload publicado
```json
{
  "ts": 1731712345.12,
  "ip": "192.168.0.121",
  "db": 500,
  "tenant_id": "clienteA",
  "plc_id": "linha1_prensa",
  "values": {
    "pecas_ruim": false,
    "pecas_boas": true,
    "maquina_ligada": true,
    "AI_Corrente": 10.25,
    "AI_Vibracao": 0.12,
    "contador_bom": 152,
    "contador_ruim": 3
  }
}
```
