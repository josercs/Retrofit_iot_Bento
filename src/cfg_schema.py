from pydantic import BaseModel, Field
from typing import Optional

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

class HTTPConfig(BaseModel):
    url: str
    timeout: float = 5.0
    headers: dict = Field(default_factory=dict)
    tls_verify: bool = True

class OutputConfig(BaseModel):
    mode: str = Field(default="stdout")
    mqtt: Optional[MQTTConfig] = None
    http: Optional[HTTPConfig] = None

class AppConfig(BaseModel):
    source_ip: str = Field(alias="source.ip")
    rack: int = 0
    slot: int = 1
    db_number: int = 1
    db_size: int = 14
    poll_interval: float = 1.0
    output: OutputConfig = Field(default_factory=OutputConfig)

    class Config:
        populate_by_name = True
