import json, time, yaml, sys
from datetime import datetime, timezone
from typing import Dict

from src.db500_reader import read_values

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None

import requests


def ts_iso():
    return datetime.now(timezone.utc).isoformat()


def publish_stdout(payload: Dict):
    print(json.dumps(payload, ensure_ascii=False))


def publish_mqtt(cfg: Dict, payload: Dict):
    if mqtt is None:
        raise RuntimeError("paho-mqtt not installed")
    b = cfg["output"]["mqtt"]["broker"]
    topic = cfg["output"]["mqtt"].get("topic", "plc/db500")
    qos = int(cfg["output"]["mqtt"].get("qos", 0))
    retain = bool(cfg["output"]["mqtt"].get("retain", False))
    client = mqtt.Client()
    if "username" in cfg["output"]["mqtt"]:
        client.username_pw_set(cfg["output"]["mqtt"].get("username"), cfg["output"]["mqtt"].get("password"))
    client.connect(b, int(cfg["output"]["mqtt"].get("port", 1883)), 60)
    client.loop_start()
    client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=qos, retain=retain)
    time.sleep(0.1)
    client.loop_stop()
    client.disconnect()


def publish_http(cfg: Dict, payload: Dict):
    url = cfg["output"]["http"]["url"]
    timeout = float(cfg["output"]["http"].get("timeout", 5))
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, timeout=timeout, headers=headers)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Read DB500 fields and publish to MQTT/HTTP/stdout")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--mode", choices=["stdout","mqtt","http"], help="Override output mode")
    p.add_argument("--once", action="store_true", help="Run once and exit")
    args = p.parse_args()

    cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))

    ip = cfg["source"]["ip"]
    rack = cfg.get("rack", 0)
    slot = cfg.get("slot", 1)
    dbn = int(cfg.get("db_number", 1))
    dbs = int(cfg.get("db_size", 16))
    interval = float(cfg.get("poll_interval", 1.0))

    mode = args.mode or cfg.get("output",{}).get("mode","stdout")

    def do_publish():
        vals = read_values(ip, rack, slot, dbn, dbs)
        payload = {"ts": ts_iso(), "ip": ip, "db": dbn, "values": vals}
        if mode == "stdout":
            publish_stdout(payload)
        elif mode == "mqtt":
            publish_mqtt(cfg, payload)
        elif mode == "http":
            publish_http(cfg, payload)

    if args.once:
        do_publish()
        return

    while True:
        try:
            do_publish()
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
        time.sleep(interval)

if __name__ == "__main__":
    main()
