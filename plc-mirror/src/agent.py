import json, sys, time, os
import yaml
from typing import Dict
from src.config_loader import load_config
from src.db500_reader import read_values
from src.metrics import READ_OK, READ_FAIL, PUBLISH_OK, PUBLISH_FAIL, LAST_VALUE, BACKLOG, READ_LATENCY_MS, EDGE_UP, start_metrics_server, set_last_payload_provider
from src.store import StoreForward
from threading import Thread, Event
import logging

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None
import requests


def publish_stdout(payload: Dict):
    print(json.dumps(payload, ensure_ascii=False))


def publish_mqtt(cfg, payload: Dict):
    if mqtt is None:
        raise RuntimeError('paho-mqtt not installed')
    m = cfg.output.mqtt
    if m is None:
        raise ValueError('MQTT config missing (output.mqtt). Check config.yaml and indentation/mount.')
    # Log a concise summary once per process for troubleshooting
    # (avoid printing secrets)
    try:
        if not getattr(publish_mqtt, "_printed_cfg", False):
            logging.info('MQTT CFG: broker=%s port=%s topic=%s tls=%s ca_file=%s user=%s', m.broker, m.port, m.topic, m.tls, bool(m.ca_file), bool(m.username))
            publish_mqtt._printed_cfg = True
    except Exception:
        pass
    client = mqtt.Client()
    if m.username:
        client.username_pw_set(m.username, m.password)
    if m.tls:
        # Use only CA if cert/key not provided (common for username/password auth)
        try:
            client.tls_set(ca_certs=m.ca_file, certfile=m.cert_file if m.cert_file else None, keyfile=m.key_file if m.key_file else None)
            client.tls_insecure_set(bool(m.tls_insecure))
        except Exception as e:
            logging.debug('TLS setup error (continuing): %r', e)
    client.connect(m.broker, int(m.port), 60)
    client.loop_start()
    # Resolve placeholders in topic (e.g., plc/${TENANT_ID}/${PLC_ID})
    topic = m.topic or "plc/db1"
    try:
        tenant = getattr(cfg, 'tenant_id', None) or os.environ.get('TENANT_ID')
        plc = getattr(cfg, 'plc_id', None) or os.environ.get('PLC_ID')
        if '${TENANT_ID}' in topic and tenant:
            topic = topic.replace('${TENANT_ID}', str(tenant))
        if '${PLC_ID}' in topic and plc:
            topic = topic.replace('${PLC_ID}', str(plc))
    except Exception:
        pass
    # Fallback se placeholders permanecerem não resolvidos
    if '${' in topic:
        topic = 'plc/db1'
    try:
        logging.info('MQTT publish topic resolved to: %s', topic)
    except Exception:
        pass
    info = client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=int(m.qos), retain=bool(m.retain))
    try:
        info.wait_for_publish(timeout=2.0)
    except Exception:
        # Best-effort: give network loop a brief moment
        time.sleep(0.1)
    finally:
        client.loop_stop(); client.disconnect()


def publish_http(cfg, payload: Dict):
    h = cfg.output.http; assert h is not None
    requests.post(h.url, json=payload, timeout=float(h.timeout), headers=h.headers, verify=bool(h.tls_verify))


def main():
    import argparse
    p = argparse.ArgumentParser(description='PLC DB500 edge agent')
    p.add_argument('--config', default='config.yaml')
    p.add_argument('--mode', choices=['stdout','mqtt','http'])
    p.add_argument('--once', action='store_true')
    args = p.parse_args()

    # Start HTTP/metrics server early to avoid connection refused while config loads
    last_payload = {'ts': 0, 'ip': '', 'db': 0, 'values': {}}
    # Try reading metrics_port directly from YAML (best-effort). Fallback to 9108.
    _metrics_port = 9108
    try:
        with open(args.config, 'r', encoding='utf-8') as _f:
            _raw = yaml.safe_load(_f) or {}
            _mp = _raw.get('metrics_port')
            if _mp is not None:
                _metrics_port = int(_mp)
    except Exception:
        pass
    start_metrics_server(_metrics_port)
    set_last_payload_provider(lambda: last_payload)
    EDGE_UP.set(1)

    # Load configuration with retry so we keep serving HTTP even if YAML/env are momentarily invalid
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    while True:
        try:
            cfg = load_config(args.config)
            try:
                logging.info('CFG SUMMARY: source.ip=%s db=%s mode=%s mqtt_present=%s', cfg.source.ip, cfg.source.db_number, cfg.output.mode, cfg.output.mqtt is not None)
                if cfg.output.mqtt:
                    m = cfg.output.mqtt
                    logging.info('MQTT to %s:%s topic=%s tls=%s ca=%s user=%s', m.broker, m.port, m.topic, m.tls, m.ca_file, m.username or '-')
            except Exception as e:
                logging.debug('CFG PRINT ERROR: %r', e)
            break
        except Exception as e:
            logging.error('CONFIG ERROR: %s', e)
            time.sleep(2.0)
    mode = args.mode or cfg.output.mode
    # Update placeholder payload meta now that cfg is available
    last_payload.update({'ip': cfg.source.ip, 'db': cfg.source.db_number, 'tenant_id': cfg.tenant_id, 'plc_id': cfg.plc_id})

    store = StoreForward(cfg.store_path)

    stop_flag = Event()

    def forced_heartbeat_loop():
        # Periodic heartbeat independent of PLC read (every 30s)
        while not stop_flag.is_set():
            hb = {
                'ts': time.time(),
                'ip': cfg.source.ip,
                'db': cfg.source.db_number,
                'tenant_id': cfg.tenant_id,
                'plc_id': cfg.plc_id,
                'values': {
                    'heartbeat': 1,
                },
                'forced': True,
            }
            last_payload.update(hb)
            try:
                if mode == 'stdout':
                    publish_stdout(hb)
                elif mode == 'mqtt':
                    publish_mqtt(cfg, hb)
                elif mode == 'http':
                    publish_http(cfg, hb)
                PUBLISH_OK.labels(mode).inc()
                logging.debug('forced heartbeat published')
            except Exception as pe:
                PUBLISH_FAIL.labels(mode).inc(); store.enqueue(hb)
                logging.debug('forced heartbeat publish error: %r', pe)
            for _ in range(30):
                if stop_flag.is_set(): break
                time.sleep(1)

    Thread(target=forced_heartbeat_loop, daemon=True).start()

    def one_cycle():
        try:
            t0 = time.time()
            # Try PLC read but don't kill the server if it fails; we'll record and retry.
            vals = read_values(cfg.source.ip, cfg.source.rack, cfg.source.slot, cfg.source.db_number, cfg.source.db_size)
            READ_LATENCY_MS.set((time.time()-t0)*1000.0)
            READ_OK.inc()
            for k, v in vals.items():
                if isinstance(v, (int, float)):
                    LAST_VALUE.labels(k).set(float(v))
        except Exception as e:
            READ_FAIL.inc()
            # Publish a heartbeat payload so downstream can see outage state
            hb = {
                'ts': time.time(),
                'ip': cfg.source.ip,
                'db': cfg.source.db_number,
                'tenant_id': cfg.tenant_id,
                'plc_id': cfg.plc_id,
                'values': {
                    'heartbeat': 1,
                    'read_failed': True,
                },
                'error': str(e)[:180],
            }
            last_payload.update(hb)
            try:
                logging.debug('publishing read-failure heartbeat')
                if mode == 'stdout':
                    publish_stdout(hb)
                elif mode == 'mqtt':
                    publish_mqtt(cfg, hb)
                elif mode == 'http':
                    publish_http(cfg, hb)
                PUBLISH_OK.labels(mode).inc()
            except Exception as pe:
                PUBLISH_FAIL.labels(mode).inc(); store.enqueue(hb)
                logging.error('PUBLISH ERROR (%s) heartbeat: %r', mode, pe)
            # Log PLC error and sleep briefly before next loop
            logging.error('PLC READ ERROR: %r', e)
            time.sleep(1.0)
            return
        payload = {
            'ts': time.time(),
            'ip': cfg.source.ip,
            'db': cfg.source.db_number,
            'tenant_id': cfg.tenant_id,
            'plc_id': cfg.plc_id,
            'values': vals,
        }
        last_payload.update(payload)
        try:
            if mode == 'stdout':
                publish_stdout(payload)
            elif mode == 'mqtt':
                publish_mqtt(cfg, payload)
            elif mode == 'http':
                publish_http(cfg, payload)
            PUBLISH_OK.labels(mode).inc()
        except Exception as e:
            PUBLISH_FAIL.labels(mode).inc(); store.enqueue(payload)
            logging.error('PUBLISH ERROR (%s): %r', mode, e)
            # Do not raise to avoid crash loop; backlog will flush later
            return

        # Flush backlog
        batch = store.dequeue(200)
        # Update backlog size metric
        try:
            BACKLOG.set(store.count())
        except Exception:
            pass
        if batch:
            ok_ids = []
            for rid, pl in batch:
                try:
                    if mode == 'stdout': publish_stdout(pl)
                    elif mode == 'mqtt': publish_mqtt(cfg, pl)
                    elif mode == 'http': publish_http(cfg, pl)
                    ok_ids.append(rid)
                except Exception:
                    break
            store.delete_ids(ok_ids)

    try:
        if args.once:
            one_cycle(); return
        while True:
            try:
                one_cycle()
            except Exception as e:
                logging.error('ERROR: %s', e)
            time.sleep(cfg.source.poll_interval)
    except KeyboardInterrupt:
        stop_flag.set()
        pass

if __name__ == '__main__':
    main()
