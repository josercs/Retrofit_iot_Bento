import json
import time
from src.metrics import start_metrics_server, set_last_payload_provider
import urllib.request as http


def test_metrics_endpoint_available(tmp_path):
    # start on random high port to avoid conflicts
    port = 9208
    start_metrics_server(port)
    # allow server thread to start
    time.sleep(0.1)
    with http.urlopen(f'http://127.0.0.1:{port}/metrics', timeout=2) as r:
        body = r.read().decode('utf-8')
        assert 'plc_read_ok_total' in body


def test_api_last_returns_payload():
    port = 9210
    start_metrics_server(port)
    # provide a fake last payload
    set_last_payload_provider(lambda: {
        "ts": 123.0,
        "ip": "1.2.3.4",
        "db": 1,
        "tenant_id": "clienteA",
        "plc_id": "linha1_prensa",
        "values": {"contador_bom": 10}
    })
    time.sleep(0.1)
    with http.urlopen(f'http://127.0.0.1:{port}/api/last', timeout=2) as r:
        data = json.loads(r.read().decode('utf-8'))
        assert data["ip"] == "1.2.3.4" and data["db"] == 1
        assert data["tenant_id"] == "clienteA" and data["plc_id"] == "linha1_prensa"
