import json
import sys
import types
from types import SimpleNamespace

# Forçar um módulo 'requests' fake no sys.modules antes do import do agente
class _Resp:
    status_code = 200
def _noop_post(*a, **k):
    return _Resp()
sys.modules.setdefault('requests', types.SimpleNamespace(post=_noop_post))

import src.agent as agent


def make_cfg_http(url="http://example.local/ingest"):
    http = SimpleNamespace(url=url, timeout=1.0, headers={"X-Test":"1"}, tls_verify=True)
    output = SimpleNamespace(http=http, mqtt=None, mode="http")
    return SimpleNamespace(output=output)


def make_cfg_mqtt():
    mqtt = SimpleNamespace(
        broker="broker.local", port=1883, topic="plc/${TENANT_ID}/${PLC_ID}", qos=0, retain=False,
        username=None, password=None, tls=False, ca_file=None, cert_file=None, key_file=None, tls_insecure=False
    )
    output = SimpleNamespace(http=None, mqtt=mqtt, mode="mqtt")
    return SimpleNamespace(output=output)


def test_publish_http(monkeypatch):
    called = {}

    def fake_post(url, json=None, timeout=None, headers=None, verify=None):
        called.update(dict(url=url, payload=json, timeout=timeout, headers=headers, verify=verify))
        class R:  # minimal response
            status_code = 200
        return R()

    monkeypatch.setattr(agent, "requests", SimpleNamespace(post=fake_post))
    cfg = make_cfg_http()
    payload = {"ok": True}
    agent.publish_http(cfg, payload)
    assert called["url"].startswith("http://example.local"); assert called["payload"] == payload


def test_publish_mqtt(monkeypatch):
    events = {"published": False, "topic": None, "payload": None, "loop_started": False, "stopped": False}

    class PubInfo:
        def wait_for_publish(self, timeout=None):
            return True

    class FakeClient:
        def __init__(self): pass
        def username_pw_set(self, *a, **k): pass
        def tls_set(self, *a, **k): pass
        def tls_insecure_set(self, *a, **k): pass
        def connect(self, *a, **k): pass
        def loop_start(self): events["loop_started"] = True
        def publish(self, topic, payload, qos=0, retain=False):
            events.update({"published": True, "topic": topic, "payload": payload})
            return PubInfo()
        def loop_stop(self): events["stopped"] = True
        def disconnect(self): pass

    fake_mqtt = SimpleNamespace(Client=lambda: FakeClient())
    monkeypatch.setattr(agent, "mqtt", fake_mqtt)
    cfg = make_cfg_mqtt()
    # define env for placeholder replacement
    monkeypatch.setenv('TENANT_ID', 'clienteA')
    monkeypatch.setenv('PLC_ID', 'linha1_prensa')
    agent.publish_mqtt(cfg, {"x": 1})
    assert events["published"] and events["loop_started"] and events["stopped"]
    assert events["topic"] == "plc/clienteA/linha1_prensa"
    # payload is JSON string
    data = json.loads(events["payload"])
    assert data["x"] == 1
