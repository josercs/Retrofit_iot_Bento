from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class StatusModel(BaseModel):
    agent_status: str
    uptime: int
    cpu_usage: float
    mem_usage: float
    last_read_ts: int
    edge_up: bool

class PLCModel(BaseModel):
    ip: str
    rack: int
    slot: int
    connection_state: str
    avg_read_time_ms: float
    read_error_count: int
    last_error_msg: Optional[str] = None

class MQTTModel(BaseModel):
    broker: str
    port: int
    topic: str
    connection_state: str
    published_count: int
    last_publish_ts: int
    last_error_msg: Optional[str] = None

class DataLastModel(BaseModel):
    ts: int
    ip: str
    db: int
    values: Dict[str, Any]



class ConfigPLCModel(BaseModel):
    ip: str
    rack: int
    slot: int

class ConfigMQTTModel(BaseModel):
    broker: str
    port: int
    topic: str

class ConfigModel(BaseModel):
    plc: ConfigPLCModel
    mqtt: ConfigMQTTModel
    read_interval: int
    asset_id: str
    client: Optional[str] = None
