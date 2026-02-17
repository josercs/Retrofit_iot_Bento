import os, yaml
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ValidationError

class SourceConfig(BaseModel):
    ip: str
    rack: int = 0
    slot: int = 1
    db_number: int = 1
    db_size: int = 14
    poll_interval: float = 1.0

class MQTTConfig(BaseModel):
    broker: str
    port: int = 1883
    topic: str = "plc/db500"
    qos: int = 0
    retain: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    tls: bool = False
    ca_file: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    tls_insecure: bool = False

class HTTPConfig(BaseModel):
    url: str
    timeout: float = 5.0
    headers: Dict[str, str] = Field(default_factory=dict)
    tls_verify: bool = True

class OutputConfig(BaseModel):
    mode: Literal['stdout','mqtt','http'] = 'stdout'
    mqtt: Optional[MQTTConfig] = None
    http: Optional[HTTPConfig] = None

class AppConfig(BaseModel):
    source: SourceConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    metrics_port: Optional[int] = 9108
    store_path: str = 'queue.sqlite'
    tenant_id: Optional[str] = None
    plc_id: Optional[str] = None

ENV_MAP = {
    ('source','ip'): 'PLC_IP',
    ('source','db_number'): 'DB_NUMBER',
    ('source','db_size'): 'DB_SIZE',
    ('output','mode'): 'OUTPUT_MODE',
    ('metrics_port',): 'METRICS_PORT',
    ('tenant_id',): 'TENANT_ID',
    ('plc_id',): 'PLC_ID',
}

MQTT_ENV = {
    ('output','mqtt','broker'): 'MQTT_BROKER',
    ('output','mqtt','port'): 'MQTT_PORT',
    ('output','mqtt','topic'): 'MQTT_TOPIC',
    ('output','mqtt','username'): 'MQTT_USERNAME',
    ('output','mqtt','password'): 'MQTT_PASSWORD',
    ('output','mqtt','tls'): 'MQTT_TLS',
    ('output','mqtt','ca_file'): 'MQTT_CA_FILE',
    ('output','mqtt','cert_file'): 'MQTT_CERT_FILE',
    ('output','mqtt','key_file'): 'MQTT_KEY_FILE',
    ('output','mqtt','tls_insecure'): 'MQTT_TLS_INSECURE',
}

HTTP_ENV = {
    ('output','http','url'): 'HTTP_URL',
}

def _set_in(d: Dict[str, Any], path: tuple, value: str):
    ref = d
    for key in path[:-1]:
        cur = ref.get(key)
        if not isinstance(cur, dict):
            cur = {}
            ref[key] = cur
        ref = cur
    ref[path[-1]] = value

def _merge_env(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure base 'output' is a dict if present, but don't create empty 'mqtt'/'http'
    if raw.get('output') is None:
        raw['output'] = {}
    elif not isinstance(raw.get('output'), dict):
        raw['output'] = {'mode': raw.get('output')}
    for path, key in ENV_MAP.items():
        v = os.environ.get(key)
        if v is not None:
            _set_in(raw, path, v)
    for path, key in MQTT_ENV.items():
        v = os.environ.get(key)
        if v is not None:
            _set_in(raw, path, v)
    for path, key in HTTP_ENV.items():
        v = os.environ.get(key)
        if v is not None:
            _set_in(raw, path, v)
    return raw

def _normalize_mqtt_section(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    If users mistakenly place MQTT keys directly under 'output' (indentation error),
    move known keys into 'output.mqtt' to avoid runtime failure.
    """
    out = raw.get('output') or {}
    if not isinstance(out, dict):
        return raw
    mqtt_cfg = out.get('mqtt')
    known = ['broker','port','topic','qos','retain','username','password','tls','ca_file','cert_file','key_file','tls_insecure']
    misplaced = {k: out.get(k) for k in known if k in out}
    if (mqtt_cfg is None or not isinstance(mqtt_cfg, dict)) and any(v is not None for v in misplaced.values()):
        out['mqtt'] = {k: v for k, v in misplaced.items() if v is not None}
        # Clean up misplaced keys from 'output'
        for k in misplaced.keys():
            out.pop(k, None)
        raw['output'] = out
    return raw

def load_config(path: str) -> AppConfig:
    data: Dict[str, Any] = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    data = _merge_env(data)
    data = _normalize_mqtt_section(data)
    try:
        return AppConfig(**data)
    except ValidationError as e:
        raise RuntimeError(f'Invalid configuration: {e}')
