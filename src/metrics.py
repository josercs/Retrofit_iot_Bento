from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Callable, Optional
from prometheus_client import Counter, Gauge, generate_latest, REGISTRY

READ_OK = Counter('plc_read_ok_total', 'Successful PLC DB reads')
READ_FAIL = Counter('plc_read_fail_total', 'Failed PLC DB reads')
PUBLISH_OK = Counter('plc_publish_ok_total', 'Successful publishes', ['mode'])
PUBLISH_FAIL = Counter('plc_publish_fail_total', 'Failed publishes', ['mode'])
LAST_VALUE = Gauge('plc_last_value', 'Last numeric values', ['name'])
BACKLOG = Gauge('edge_backlog_size', 'Store-and-forward backlog size')
READ_LATENCY_MS = Gauge('plc_read_latency_ms', 'PLC DB read latency in milliseconds')
EDGE_UP = Gauge('edge_up', 'Edge agent up flag (1=up)')

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(generate_latest(REGISTRY))
        elif self.path == '/' or self.path.startswith('/dashboard'):
            # Simple HTML dashboard
            html = DASHBOARD_HTML
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
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
DASHBOARD_HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>PLC DB500 Dashboard</title>
    <style>
        body { font-family: Segoe UI, Arial, sans-serif; margin: 20px; color: #222; }
        h1 { font-size: 20px; margin-bottom: 8px; }
        .meta { color: #555; margin-bottom: 16px; }
        table { border-collapse: collapse; width: 520px; max-width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background: #f4f4f4; text-align: left; }
        .ok { color: #0a7; font-weight: 600; }
        .bad { color: #b22; font-weight: 600; }
        .mono { font-family: Consolas, monospace; }
    </style>
    <script>
        async function loadLast(){
            try{
                const r = await fetch('/api/last');
                if(!r.ok) return;
                const data = await r.json();
                document.getElementById('ip').textContent = data.ip;
                document.getElementById('db').textContent = data.db;
                document.getElementById('ts').textContent = new Date(data.ts*1000).toLocaleString();
                const v = data.values || {};
                const rows = [
                    ['pecas_ruim', v.pecas_ruim],
                    ['pecas_boas', v.pecas_boas],
                    ['maquina_ligada', v.maquina_ligada],
                    ['AI_Corrente', v.AI_Corrente],
                    ['AI_Vibracao', v.AI_Vibracao],
                    ['contador_bom', v.contador_bom],
                    ['contador_ruim', v.contador_ruim],
                ];
                const tbody = document.getElementById('tbody');
                tbody.innerHTML='';
                for(const [name,val] of rows){
                    const tr = document.createElement('tr');
                    const td1 = document.createElement('td'); td1.textContent=name; tr.appendChild(td1);
                    const td2 = document.createElement('td');
                    if(typeof val === 'boolean'){
                        td2.innerHTML = val ? '<span class="ok">ON</span>' : '<span class="bad">OFF</span>';
                    } else {
                        td2.textContent = val;
                    }
                    tr.appendChild(td2);
                    tbody.appendChild(tr);
                }
            }catch(e){ /* ignore */ }
        }
        setInterval(loadLast, 1000);
        window.addEventListener('load', loadLast);
    </script>
</head>
<body>
    <h1>PLC DB500 Dashboard</h1>
    <div class="meta">IP: <span id="ip" class="mono">-</span> | DB: <span id="db" class="mono">-</span> | Último: <span id="ts" class="mono">-</span></div>
    <table>
        <thead><tr><th>Sinal</th><th>Valor</th></tr></thead>
        <tbody id="tbody"></tbody>
    </table>
    <p class="meta">Métricas Prometheus: <a href="/metrics">/metrics</a></p>
</body>
</html>
"""
