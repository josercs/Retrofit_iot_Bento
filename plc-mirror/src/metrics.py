from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Callable, Optional
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY

READ_OK = Counter('plc_read_ok_total', 'Successful PLC DB reads')
READ_FAIL = Counter('plc_read_fail_total', 'Failed PLC DB reads')
PUBLISH_OK = Counter('plc_publish_ok_total', 'Successful publishes', ['mode'])
PUBLISH_FAIL = Counter('plc_publish_fail_total', 'Failed publishes', ['mode'])
LAST_VALUE = Gauge('plc_last_value', 'Last numeric values', ['name'])
PLC_LAST_TS = Gauge('plc_last_ts_seconds', 'Timestamp of last payload (unix seconds)')
BACKLOG = Gauge('edge_backlog_size', 'Store-and-forward backlog size')
READ_LATENCY_MS = Gauge('plc_read_latency_ms', 'PLC DB read latency in milliseconds')
EDGE_UP = Gauge('edge_up', 'Edge agent up flag (1=up)')

EDGE_UP.set(1)

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(generate_latest(REGISTRY))
        elif self.path == '/' or self.path.startswith('/dashboard'):
            self.send_response(404); self.end_headers()
        elif self.path.startswith('/api/last'):
            provider = get_last_payload_provider()
            if provider is None:
                self.send_response(204); self.end_headers(); return
            try:
                data = provider()
            except Exception:
                data = None
            if data is None:
                self.send_response(204); self.end_headers(); return
            # Atualiza a métrica de timestamp do último payload
            ts = None
            if isinstance(data, dict):
                ts = data.get('ts')
            if ts:
                try:
                    PLC_LAST_TS.set(float(ts))
                except Exception:
                    pass
            import json
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404); self.end_headers()


def start_metrics_server(port: int):
    def _run():
        httpd = HTTPServer(('0.0.0.0', port), MetricsHandler)
        httpd.serve_forever()
    Thread(target=_run, daemon=True).start()

# --- Simple provider wiring for last payload ---
_last_payload_provider: Optional[Callable[[], dict]] = None

def set_last_payload_provider(fn: Callable[[], dict]):
        global _last_payload_provider
        _last_payload_provider = fn

def get_last_payload_provider() -> Optional[Callable[[], dict]]:
        return _last_payload_provider


# --- Minimal HTML dashboard ---
