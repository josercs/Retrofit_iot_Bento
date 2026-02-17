import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Callable, Optional
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY

# ============================================================
# CONTEXTO FIXO DO EDGE
# ============================================================

EDGE_ID = os.getenv("EDGE_ID", "edge01")
EDGE_IP = os.getenv("EDGE_IP", "unknown")
SITE    = os.getenv("SITE", "default")

EDGE_LABELS = {
    "edge_id": EDGE_ID,
    "ip": EDGE_IP,
    "site": SITE
}

# ============================================================
# EDGE — SAÚDE DO AGENTE
# measurement: edge
# ============================================================

EDGE_UP = Gauge(
    "edge_up",
    "Edge agent up flag (1=up)",
    ["edge_id", "ip", "site"]
)

EDGE_UP.labels(**EDGE_LABELS).set(1)

EDGE_BACKLOG = Gauge(
    "edge_backlog_size",
    "Store-and-forward backlog size",
    ["edge_id", "site"]
)

EDGE_UPTIME = Gauge(
    "edge_uptime_seconds",
    "Edge agent uptime in seconds",
    ["edge_id", "site"]
)

# ============================================================
# PLC — LEITURA E ESTADO
# measurement: plc
# ============================================================

PLC_READ_OK = Counter(
    "plc_read_ok_total",
    "Successful PLC DB reads",
    ["edge_id", "plc_id"]
)

PLC_READ_FAIL = Counter(
    "plc_read_fail_total",
    "Failed PLC DB reads",
    ["edge_id", "plc_id"]
)

PLC_READ_LATENCY_MS = Gauge(
    "plc_read_latency_ms",
    "PLC DB read latency in milliseconds",
    ["edge_id", "plc_id"]
)

PLC_MACHINE_ON = Gauge(
    "plc_machine_on",
    "Machine powered state (1=on)",
    ["edge_id", "plc_id"]
)

# ============================================================
# PIPELINE — PUBLICAÇÃO
# measurement: pipeline
# ============================================================

PIPELINE_PUBLISH_OK = Counter(
    "pipeline_publish_ok_total",
    "Successful publishes",
    ["edge_id", "mode"]
)

PIPELINE_PUBLISH_FAIL = Counter(
    "pipeline_publish_fail_total",
    "Failed publishes",
    ["edge_id", "mode"]
)

# ============================================================
# PAYLOAD — ÚLTIMO DADO
# measurement: payload
# ============================================================

PAYLOAD_LAST_TS = Gauge(
    "payload_last_ts_seconds",
    "Timestamp of last payload (unix seconds)",
    ["edge_id"]
)

# ============================================================
# HTTP METRICS SERVER
# ============================================================

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; version=0.0.4; charset=utf-8"
            )
            self.end_headers()
            self.wfile.write(generate_latest(REGISTRY))
            return

        if self.path.startswith("/api/last"):
            provider = get_last_payload_provider()
            if provider is None:
                self.send_response(204)
                self.end_headers()
                return

            try:
                data = provider()
            except Exception:
                data = None

            if not data:
                self.send_response(204)
                self.end_headers()
                return

            ts = data.get("ts")
            if ts:
                try:
                    PAYLOAD_LAST_TS.labels(edge_id=EDGE_ID).set(float(ts))
                except Exception:
                    pass

            import json
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()
            self.wfile.write(
                json.dumps(data, ensure_ascii=False).encode("utf-8")
            )
            return

        self.send_response(404)
        self.end_headers()


def start_metrics_server(port: int):
    def _run():
        httpd = HTTPServer(("0.0.0.0", port), MetricsHandler)
        httpd.serve_forever()

    Thread(target=_run, daemon=True).start()

# ============================================================
# PROVEDOR DO ÚLTIMO PAYLOAD
# ============================================================

_last_payload_provider: Optional[Callable[[], dict]] = None

def set_last_payload_provider(fn: Callable[[], dict]):
    global _last_payload_provider
    _last_payload_provider = fn

def get_last_payload_provider() -> Optional[Callable[[], dict]]:
    return _last_payload_provider
