import yaml
import os
try:
    import snap7
    from snap7.util import get_bool, get_real, get_int
except Exception as e:
    raise SystemExit(f"snap7 missing: {e}")

BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE, 'config.yaml')
cfg = yaml.safe_load(open(CFG_PATH,'r',encoding='utf-8'))
src = cfg['source']
ip = src['ip']
rack = src.get('rack',0)
slot = src.get('slot',1)
db = src.get('db_number',1)
size = src.get('db_size', 14)

import os
slot_env = os.getenv('S7_SLOT')
if slot_env:
    try:
        slot = int(slot_env)
    except Exception:
        pass

c = snap7.client.Client()
try:
    c.connect(ip, rack, slot)
except Exception as e:
    raise SystemExit(f"CONNECT ERROR ip={ip} rack={rack} slot={slot}: {e}")
try:
    raw = c.db_read(db, 0, size)
except Exception as e:
    raise SystemExit(f"DB READ ERROR db={db} size={size}: {e}")
finally:
    try:
        c.disconnect()
    except Exception:
        pass

def decode_simple14():
    # layout 14 bytes conforme db500_reader.py
    return {
        'pecas_ruim': bool(get_bool(raw, 0, 0)),
        'pecas_boas': bool(get_bool(raw, 0, 1)),
        'maquina_ligada': bool(get_bool(raw, 0, 2)),
        'AI_Corrente': float(get_real(raw, 2)),
        'AI_Vibracao': float(get_real(raw, 6)),
        'contador_bom': int(get_int(raw, 10)),
        'contador_ruim': int(get_int(raw, 12)),
    }

import json
print(json.dumps({'db': db, 'size': size, 'values': decode_simple14()}, ensure_ascii=False, indent=2))
