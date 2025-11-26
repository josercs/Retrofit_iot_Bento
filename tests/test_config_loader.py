import os
import textwrap
from src.config_loader import load_config


def test_env_overrides(tmp_path, monkeypatch):
    cfg_file = tmp_path / "c.yaml"
    cfg_file.write_text("source:\n  ip: '1.1.1.1'\n  db_number: 1\n  db_size: 14\noutput:\n  mode: 'stdout'\n")
    monkeypatch.setenv("PLC_IP", "2.2.2.2")
    monkeypatch.setenv("DB_NUMBER", "500")
    monkeypatch.setenv("OUTPUT_MODE", "mqtt")
    c = load_config(str(cfg_file))
    assert c.source.ip == "2.2.2.2"
    assert c.source.db_number == 500
    assert c.output.mode == "mqtt"


def test_mqtt_normalization(tmp_path):
    # Simulate misplaced MQTT keys directly under output
    cfg_file = tmp_path / "c.yaml"
    cfg_file.write_text(textwrap.dedent(
        """
        source:
          ip: '1.1.1.1'
          db_number: 1
          db_size: 14
        output:
          mode: mqtt
          broker: 'b'
          port: 1883
          topic: 't'
        """
    ))
    c = load_config(str(cfg_file))
    assert c.output.mqtt is not None
    assert c.output.mqtt.broker == 'b'
    assert c.output.mqtt.port == 1883
    assert c.output.mqtt.topic == 't'
