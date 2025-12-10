import yaml
import sys
import os

try:
    import snap7
except Exception as e:
    print('ERROR: python-snap7 not installed or DLL missing:', e)
    sys.exit(1)

BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE, 'config.yaml')
cfg = yaml.safe_load(open(CFG_PATH,'r',encoding='utf-8'))
src = cfg.get('source', {})
ip = src.get('ip') or src.get('host')
rack = src.get('rack', 0)
slot = src.get('slot', 1)

if not ip:
    print('ERROR: source.ip não encontrado no config.yaml')
    sys.exit(2)

c = snap7.client.Client()
try:
    c.connect(ip, rack, slot)
    status = 'OK' if c.get_connected() else 'FAIL'
except Exception as e:
    status = f'FAIL: {e}'
finally:
    try:
        c.disconnect()
    except Exception:
        pass

print('RESULT:', {'ip': ip, 'rack': rack, 'slot': slot, 'status': status})
