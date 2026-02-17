import yaml
import snap7
cfg = yaml.safe_load(open('config.yaml','r',encoding='utf-8'))
IP = cfg['source']['ip']; rack=cfg.get('rack',0); slot=cfg.get('slot',1)
client = snap7.client.Client(); client.connect(IP, rack, slot)
for db in (1, 500, 501, 100, 2, 3, 10):
    try:
        data = client.db_read(db, 0, 16)
        print(f'DB {db}: OK len={len(data)}')
    except Exception as e:
        print(f'DB {db}: FAIL {e}')
client.disconnect()
