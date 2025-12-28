import yaml
import requests
import socket
import time

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test_mqtt(cfg):
    try:
        sock = socket.create_connection((cfg['broker'], cfg['port']), timeout=cfg.get('timeout', 3))
        sock.close()
        return "OK: Conexão MQTT estabelecida"
    except Exception as e:
        return f"ERRO: {e}"

def test_influx(cfg):
    try:
        headers = {
            "Authorization": f"Token {cfg['token']}"
        }
        url = f"{cfg['url']}/api/v2/buckets"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return "OK: Conexão InfluxDB estabelecida"
        else:
            return f"ERRO: {r.status_code} {r.text}"
    except Exception as e:
        return f"ERRO: {e}"

def test_grafana(cfg):
    try:
        url = f"{cfg['url']}/api/datasources/name/{cfg['datasource']}"
        r = requests.get(url, auth=(cfg['username'], cfg['password']), timeout=5)
        if r.status_code == 200:
            return "OK: Conexão Grafana estabelecida"
        else:
            return f"ERRO: {r.status_code} {r.text}"
    except Exception as e:
        return f"ERRO: {e}"

def main():
    print("=== AUDITORIA RETROFIT IoT BENTO ===\n")
    config = load_config("config.yaml")

    print("MQTT:", test_mqtt(config['mqtt']))
    print("InfluxDB:", test_influx(config['influx']))
    print("Grafana:", test_grafana(config['grafana']))

if __name__ == "__main__":
    main()