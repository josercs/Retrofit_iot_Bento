"""
Mirror de DB S7: lê DB do PLC fonte e escreve no PLC destino.
Usage:
  python -m src.mirror --config config.yaml
"""
import time
import yaml
import logging

try:
    import snap7
except Exception:
    snap7 = None  # Em testes podemos mockar snap7

LOG = logging.getLogger("plc_mirror")


class PLCMirror:
    def __init__(self, src_ip: str, dst_ip: str, rack: int = 0, slot: int = 1, db_number: int = 1, db_size: int = 16):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.rack = rack
        self.slot = slot
        self.db_number = db_number
        self.db_size = db_size
        self.src_client = None
        self.dst_client = None

    def _make_client(self):
        if not snap7:
            raise RuntimeError("snap7 lib not available")
        return snap7.client.Client()

    def connect(self):
        self.src_client = self._make_client()
        self.dst_client = self._make_client()
        LOG.info("Connecting to source %s and destination %s", self.src_ip, self.dst_ip)
        self.src_client.connect(self.src_ip, self.rack, self.slot)
        self.dst_client.connect(self.dst_ip, self.rack, self.slot)
        if not self.src_client.get_connected() or not self.dst_client.get_connected():
            raise RuntimeError("Could not connect to source or destination PLC")

    def disconnect(self):
        for c in (self.src_client, self.dst_client):
            if c:
                try:
                    c.disconnect()
                except Exception:
                    pass

    def read_db_raw(self) -> bytes:
        return self.src_client.db_read(self.db_number, 0, self.db_size)

    def write_db_raw(self, data: bytes):
        return self.dst_client.db_write(self.db_number, 0, data)

    def mirror_once(self) -> bytes:
        raw = self.read_db_raw()
        self.write_db_raw(raw)
        return raw


def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mirror an S7 DB from source PLC to destination PLC.")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    cfg = load_config(args.config)
    m = PLCMirror(
        src_ip=cfg["source"]["ip"],
        dst_ip=cfg["destination"]["ip"],
        db_number=cfg.get("db_number", 1),
        db_size=cfg.get("db_size", 16),
        rack=cfg.get("rack", 0),
        slot=cfg.get("slot", 1),
    )
    try:
        LOG.info("Connecting to PLCs")
        m.connect()
        LOG.info("Starting mirror loop (Ctrl-C to stop)")
        while True:
            raw = m.mirror_once()
            LOG.info("Mirrored %d bytes", len(raw))
            time.sleep(cfg.get("poll_interval", 1.0))
    except KeyboardInterrupt:
        LOG.info("Interrupted")
    finally:
        m.disconnect()
