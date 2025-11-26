import yaml
try:
    import snap7
    from snap7.util import get_bool, get_real, get_int
except Exception as e:
    raise SystemExit(f"snap7 missing: {e}")

cfg = yaml.safe_load(open('config.yaml','r',encoding='utf-8'))
ip = cfg['source']['ip']
rack = cfg.get('rack',0)
slot = cfg.get('slot',1)
db = cfg.get('db_number',1)
size = cfg.get('db_size',16)

c = snap7.client.Client()
c.connect(ip, rack, slot)
raw = c.db_read(db, 0, size)

vals = {
    'pecas_ruim':      get_bool(raw, 0, 0),  # 0.0
    'pecas_boas':      get_bool(raw, 0, 1),  # 0.1
    'maquina_ligada':  get_bool(raw, 0, 2),  # 0.2
    'AI_Corrente':     get_real(raw, 2),     # 2.0
    'AI_Vibracao':     get_real(raw, 6),     # 6.0
    'contador_bom':    get_int(raw, 10),     # 10.0
    'contador_ruim':   get_int(raw, 12),     # 12.0
}
print('DB VALUES:', vals)
