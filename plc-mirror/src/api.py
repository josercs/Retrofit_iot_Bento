from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pathlib
import os
import requests
import re
from src.models import (
    StatusModel, PLCModel, MQTTModel, DataLastModel, ConfigModel
)
from typing import Optional, Dict, Any
from src.config_loader import load_config

app = FastAPI()

AGENT_BASE = "http://localhost:9108"  # ou a porta real do metrics.py

def get_ui_html():
    return '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Edge Agent • Industrial UI</title>

<style>
:root {
    --bg: #0b0f14;
    --panel: #111823;
    --panel-border: #1f2a3a;
    --text: #e6e8eb;
    --muted: #8b98a9;
    --accent: #00e5ff;
    --ok: #00d27a;
    --warn: #ffb020;
    --bad: #ff4d4d;
    --mono: "Consolas", "Courier New", monospace;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 20px;
    background: linear-gradient(180deg, #0b0f14, #0a0d12);
    color: var(--text);
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
}

h1 {
    font-size: 20px;
    margin: 0 0 6px 0;
    letter-spacing: 0.5px;
}

.meta {
    color: var(--muted);
    margin-bottom: 20px;
    font-size: 13px;
}

.dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 16px;
}

.section {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.4), 0 10px 30px rgba(0,0,0,0.4);
}

.title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
    color: var(--accent);
    letter-spacing: 0.4px;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

th {
    text-align: left;
    color: var(--muted);
    font-weight: 500;
    padding: 6px 0;
    width: 45%;
}

td {
    padding: 6px 0;
    font-family: var(--mono);
}

.state-ok { color: var(--ok); font-weight: 600; }
.state-bad { color: var(--bad); font-weight: 600; }

.logs {
    max-height: 220px;
    overflow-y: auto;
}

.logs table {
    font-size: 12px;
}

.logs th {
    position: sticky;
    top: 0;
    background: var(--panel);
}

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
}

.badge-ok { background: rgba(0,210,122,0.15); color: var(--ok); }
.badge-bad { background: rgba(255,77,77,0.15); color: var(--bad); }

.footer {
    margin-top: 24px;
    text-align: right;
    font-size: 11px;
    color: var(--muted);
}
</style>

<script>
    async function loadStatus(){
        const r = await fetch('/api/status');
        if(!r.ok) return;
        const data = await r.json();
        document.getElementById('status_agent').textContent = data.agent_status;
        document.getElementById('status_uptime').textContent = data.uptime;
        document.getElementById('status_cpu').textContent = data.cpu_usage.toFixed(1) + 's';
        document.getElementById('status_mem').textContent = data.mem_usage.toFixed(1) + ' MB';
        if (data.last_read_ts && data.last_read_ts > 0) {
            document.getElementById('status_lastread').textContent = new Date(data.last_read_ts*1000).toLocaleString();
        } else {
            document.getElementById('status_lastread').textContent = '-';
        }
    }
    async function loadPLC(){
        const r = await fetch('/api/plc');
        if(!r.ok) return;
        const data = await r.json();
        document.getElementById('plc_ip').textContent = data.ip;
        document.getElementById('plc_rack').textContent = data.rack;
        document.getElementById('plc_slot').textContent = data.slot;
        document.getElementById('plc_state').textContent = data.connection_state;
        document.getElementById('plc_avg').textContent = data.avg_read_time_ms;
        document.getElementById('plc_err').textContent = data.read_error_count;
    }
    async function loadMQTT(){
        const r = await fetch('/api/mqtt');
        if(!r.ok) return;
        const data = await r.json();
        document.getElementById('mqtt_broker').textContent = data.broker;
        document.getElementById('mqtt_port').textContent = data.port;
        document.getElementById('mqtt_topic').textContent = data.topic;
        document.getElementById('mqtt_state').textContent = data.connection_state;
        document.getElementById('mqtt_pub').textContent = data.published_count;
        if (data.last_publish_ts && data.last_publish_ts > 0) {
            document.getElementById('mqtt_last').textContent = new Date(data.last_publish_ts*1000).toLocaleString();
        } else {
            document.getElementById('mqtt_last').textContent = '-';
        }
    }
    async function loadDataLast(){
        const r = await fetch('/api/data/last');
        if(!r.ok) return;
        const data = await r.json();
        if (data.ts && data.ts > 0) {
            document.getElementById('data_ts').textContent = new Date(data.ts*1000).toLocaleString();
        } else {
            document.getElementById('data_ts').textContent = '-';
        }
        const v = data.values || {};
        const rows = Object.entries(v);
        const tbody = document.getElementById('data_tbody');
        tbody.innerHTML='';
        for(const [name,val] of rows){
            const tr = document.createElement('tr');
            const td1 = document.createElement('td'); td1.textContent=name; tr.appendChild(td1);
            const td2 = document.createElement('td'); td2.textContent=val; tr.appendChild(td2);
            tr.appendChild(td2);
            tbody.appendChild(tr);
        }
    }
    async function loadLogs(){
        const r = await fetch('/api/logs');
        if(!r.ok) return;
        const data = await r.json();
        const tbody = document.getElementById('logs_tbody');
        tbody.innerHTML='';
        for(const log of data.logs){
            const tr = document.createElement('tr');
            const td1 = document.createElement('td'); td1.textContent=new Date(log.ts*1000).toLocaleString(); tr.appendChild(td1);
            const td2 = document.createElement('td'); td2.textContent=log.level; tr.appendChild(td2);
            const td3 = document.createElement('td'); td3.textContent=log.msg; tr.appendChild(td3);
            tr.appendChild(td3);
            tbody.appendChild(tr);
        }
    }
    async function loadConfig(){
        const r = await fetch('/api/config');
        if(!r.ok) return;
        const data = await r.json();
        document.getElementById('cfg_ip').textContent = data.plc.ip;
        document.getElementById('cfg_rack').textContent = data.plc.rack;
        document.getElementById('cfg_slot').textContent = data.plc.slot;
        document.getElementById('cfg_broker').textContent = data.mqtt.broker;
        document.getElementById('cfg_port').textContent = data.mqtt.port;
        document.getElementById('cfg_topic').textContent = data.mqtt.topic;
        document.getElementById('cfg_interval').textContent = data.read_interval;
        document.getElementById('cfg_asset').textContent = data.asset_id;
        document.getElementById('cfg_client').textContent = data.client || '';
    }
    function refreshAll(){
        loadStatus(); loadPLC(); loadMQTT(); loadDataLast(); loadLogs(); loadConfig();
    }
    setInterval(refreshAll, 2000);
    window.addEventListener('load', refreshAll);
</script>
</head>

<body>

<h1>EDGE AGENT</h1>
<div class="meta">Interface industrial • Monitoramento local em tempo real</div>

<div class="dashboard">

    <div class="section">
        <div class="title">STATUS DO AGENTE</div>
        <table>
            <tr><th>Status</th><td id="status_agent"></td></tr>
            <tr><th>Uptime</th><td id="status_uptime"></td></tr>
            <tr><th>CPU</th><td id="status_cpu"></td></tr>
            <tr><th>Memória</th><td id="status_mem"></td></tr>
            <tr><th>Última leitura</th><td id="status_lastread"></td></tr>
        </table>
    </div>

    <div class="section">
        <div class="title">PLC</div>
        <table>
            <tr><th>IP</th><td id="plc_ip"></td></tr>
            <tr><th>Rack</th><td id="plc_rack"></td></tr>
            <tr><th>Slot</th><td id="plc_slot"></td></tr>
            <tr><th>Estado</th><td id="plc_state"></td></tr>
            <tr><th>Tempo médio (ms)</th><td id="plc_avg"></td></tr>
            <tr><th>Erros</th><td id="plc_err"></td></tr>
        </table>
    </div>

    <div class="section">
        <div class="title">MQTT</div>
        <table>
            <tr><th>Broker</th><td id="mqtt_broker"></td></tr>
            <tr><th>Porta</th><td id="mqtt_port"></td></tr>
            <tr><th>Tópico</th><td id="mqtt_topic"></td></tr>
            <tr><th>Estado</th><td id="mqtt_state"></td></tr>
            <tr><th>Publicações</th><td id="mqtt_pub"></td></tr>
            <tr><th>Última publicação</th><td id="mqtt_last"></td></tr>
        </table>
    </div>

    <div class="section">
        <div class="title">ÚLTIMO PAYLOAD</div>
        <table>
            <tr><th>Timestamp</th><td id="data_ts"></td></tr>
        </table>
        <table>
            <thead><tr><th>Variável</th><th>Valor</th></tr></thead>
            <tbody id="data_tbody"></tbody>
        </table>
    </div>

    <div class="section logs">
        <div class="title">LOGS</div>
        <table>
            <thead>
                <tr><th>Timestamp</th><th>Nível</th><th>Mensagem</th></tr>
            </thead>
            <tbody id="logs_tbody"></tbody>
        </table>
    </div>

    <div class="section">
        <div class="title">CONFIGURAÇÃO</div>
        <table>
            <tr><th>IP PLC</th><td id="cfg_ip"></td></tr>
            <tr><th>Rack</th><td id="cfg_rack"></td></tr>
            <tr><th>Slot</th><td id="cfg_slot"></td></tr>
            <tr><th>Broker MQTT</th><td id="cfg_broker"></td></tr>
            <tr><th>Porta</th><td id="cfg_port"></td></tr>
            <tr><th>Tópico</th><td id="cfg_topic"></td></tr>
            <tr><th>Intervalo (ms)</th><td id="cfg_interval"></td></tr>
            <tr><th>Asset</th><td id="cfg_asset"></td></tr>
            <tr><th>Cliente</th><td id="cfg_client"></td></tr>
        </table>
    </div>

</div>

<div class="footer">Edge Agent • Industrial IoT Runtime</div>

</body>
</html>
'''


@app.get('/ui', response_class=HTMLResponse)
def serve_ui():
    return get_ui_html()


def fetch_agent_last() -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{AGENT_BASE}/api/last", timeout=1.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def fetch_agent_metrics() -> Dict[str, Any]:
    """Fetch /metrics text and parse a few important metrics into a dict."""
    out: Dict[str, Any] = {}
    try:
        r = requests.get(f"{AGENT_BASE}/metrics", timeout=1.0)
        if r.status_code != 200:
            return out
        text = r.text.splitlines()
        # simple parser: metric_name{label="x"} value OR metric_name value
        m_re = re.compile(r'^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)\s*(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>[-0-9.eE+]*)')
        for line in text:
            line = line.strip();
            if not line or line.startswith('#'):
                continue
            mo = m_re.match(line)
            if not mo:
                continue
            name = mo.group('name')
            labels = mo.group('labels')
            value = float(mo.group('value'))
            if labels:
                # parse labels like name="x",mode="y"
                labs = {}
                for part in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"', labels):
                    labs[part.group(1)] = part.group(2)
                # store in nested dict
                out.setdefault(name, {})
                # use a simple key for single-label metrics
                if 'name' in labs:
                    out[name][labs['name']] = value
                else:
                    # create composite key
                    key = '|'.join(f"{k}={v}" for k, v in labs.items())
                    out[name][key] = value
            else:
                out[name] = value
    except Exception:
        pass
    return out


@app.get('/api/status', response_model=StatusModel)
def get_status():
    # try agent /api/last and /metrics
    last = fetch_agent_last()
    metrics = fetch_agent_metrics()
    edge_up = bool(metrics.get('edge_up', 0.0))
    cpu = float(metrics.get('process_cpu_seconds_total', 0.0))
    mem = float(metrics.get('process_resident_memory_bytes', 0.0)) / (1024*1024)
    # uptime approximated by process start time
    uptime = 0
    try:
        start = float(metrics.get('process_start_time_seconds', 0.0))
        if start:
            import time
            uptime = int(time.time() - start)
    except Exception:
        pass
    # Preferir timestamp da métrica Prometheus, se disponível
    last_read_ts = 0
    if 'plc_last_ts_seconds' in metrics:
        try:
            last_read_ts = int(float(metrics['plc_last_ts_seconds']))
        except Exception:
            last_read_ts = 0
    if not last_read_ts:
        last_read_ts = int(last.get('ts')) if last and 'ts' in last else 0
    return StatusModel(
        agent_status='RODANDO' if edge_up else 'PARADO',
        uptime=uptime,
        cpu_usage=cpu,
        mem_usage=mem,
        last_read_ts=last_read_ts,
        edge_up=edge_up,
    )


@app.get('/api/plc', response_model=PLCModel)
def get_plc():
    last = fetch_agent_last() or {}
    metrics = fetch_agent_metrics()
    ip = last.get('ip') or ''
    db = last.get('db')
    avg_read = float(metrics.get('plc_read_latency_ms', 0.0))
    read_fail = int(metrics.get('plc_read_fail_total', 0))
    return PLCModel(
        ip=ip,
        rack=0,
        slot=0,
        connection_state='CONECTADO' if ip else 'DESCONECTADO',
        avg_read_time_ms=avg_read,
        read_error_count=read_fail,
        last_error_msg=None,
    )


@app.get('/api/mqtt', response_model=MQTTModel)
def get_mqtt():
    metrics = fetch_agent_metrics()
    last = fetch_agent_last() or {}

    def sum_mode(metric, mode='mqtt'):
        if isinstance(metric, dict):
            return int(metric.get(mode, 0))
        try:
            return int(metric)
        except Exception:
            return 0

    pub_ok = sum_mode(metrics.get('plc_publish_ok_total', {}), 'mqtt')
    pub_fail = sum_mode(metrics.get('plc_publish_fail_total', {}), 'mqtt')

    import time
    last_ts = int(last.get('ts', 0))
    now = int(time.time())
    recently_published = last_ts > 0 and (now - last_ts) < 30

    # Considera conectado se houve publicação recente, mesmo com falhas
    connected = recently_published

    try:
        cfg = load_config('config.yaml')
        mqtt_cfg = cfg.output.mqtt if getattr(cfg, 'output', None) else None
        broker = mqtt_cfg.broker if mqtt_cfg else ''
        port = int(mqtt_cfg.port) if mqtt_cfg else 0
        topic = mqtt_cfg.topic if mqtt_cfg else ''
    except Exception:
        broker = ''
        port = 0
        topic = ''

    return MQTTModel(
        broker=broker,
        port=port,
        topic=topic,
        connection_state='CONECTADO' if connected else 'DESCONECTADO',
        published_count=pub_ok,
        last_publish_ts=last_ts,
        last_error_msg=None if pub_fail == 0 else 'Falha recente de publicação MQTT'
    )


@app.get('/api/data/last', response_model=DataLastModel)
def get_data_last():
    metrics = fetch_agent_metrics()
    # Sinais do PLC via métricas Prometheus
    plc_values = metrics.get('plc_last_value', {})
    # Monta o dicionário de valores para a UI
    values = {
        'pecas_ruim': int(plc_values.get('pecas_ruim', 0)),
        'pecas_boas': int(plc_values.get('pecas_boas', 0)),
        'maquina_ligada': int(plc_values.get('maquina_ligada', 0)),
        'AI_Corrente': float(plc_values.get('AI_Corrente', 0)),
        'AI_Vibracao': float(plc_values.get('AI_Vibracao', 0)),
        'contador_bom': int(plc_values.get('contador_bom', 0)),
        'contador_ruim': int(plc_values.get('contador_ruim', 0)),
    }
    # Timestamp aproximado: pega o start_time do processo
    import time
    ts = int(metrics.get('process_start_time_seconds', time.time()))
    # IP e DB podem ser fixos ou vindos de config
    ip = '192.168.0.121'  # ajuste conforme necessário
    db = 1
    return DataLastModel(ts=ts, ip=ip, db=db, values=values)

@app.get('/api/config', response_model=ConfigModel)
def get_config():
    # try to load config.yaml using project loader
    try:
        cfg = load_config('config.yaml')
        plc = cfg.source
        mqtt = cfg.output.mqtt if getattr(cfg, 'output', None) else None
        return ConfigModel(
            plc={'ip': plc.ip, 'rack': plc.rack, 'slot': plc.slot},
            mqtt={'broker': mqtt.broker if mqtt else '', 'port': int(mqtt.port) if mqtt else 0, 'topic': mqtt.topic if mqtt else ''},
            read_interval=int(plc.poll_interval) if hasattr(plc, 'poll_interval') else 1000,
            asset_id=getattr(cfg, 'plc_id', '') or getattr(cfg, 'tenant_id', '') or getattr(cfg, 'asset_id', ''),
            client=getattr(cfg, 'client', None)
        )
    except Exception:
        # fallback to empty/default
        return ConfigModel(
            plc={'ip': '', 'rack': 0, 'slot': 0},
            mqtt={'broker': '', 'port': 0, 'topic': ''},
            read_interval=1000,
            asset_id='',
            client=None
        )

@app.post('/api/config', response_model=ConfigModel)
def set_config(config: ConfigModel):
    # Persist changes to config.yaml (best-effort) - write minimal structure
    try:
        # load existing, update fields, save back
        cfg = {}
        import yaml
        if os.path.exists('config.yaml'):
            try:
                with open('config.yaml', 'r', encoding='utf-8') as fh:
                    cfg = yaml.safe_load(fh) or {}
            except Exception:
                cfg = {}
        # shallow write into expected structure
        cfg.setdefault('source', {})
        cfg.setdefault('output', {})
        cfg['source'].update({'ip': config.plc.ip, 'rack': config.plc.rack, 'slot': config.plc.slot, 'poll_interval': config.read_interval})
        cfg['output'].setdefault('mqtt', {})
        cfg['output']['mqtt'].update({'broker': config.mqtt.broker, 'port': config.mqtt.port, 'topic': config.mqtt.topic})
        with open('config.yaml', 'w', encoding='utf-8') as fh:
            yaml.safe_dump(cfg, fh, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except Exception:
        pass
    return config
