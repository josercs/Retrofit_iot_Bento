import yaml, time
import snap7

cfg = yaml.safe_load(open('config.yaml','r',encoding='utf-8'))
IP = cfg['source']['ip']; rack=cfg.get('rack',0); slot=cfg.get('slot',1)
cl = snap7.client.Client(); cl.connect(IP, rack, slot)
found = []
for db in range(1, 601):
    try:
        data = cl.db_read(db, 0, 2)
        found.append(db)
        print(f'FOUND DB {db} size>=2')
    except Exception:
        pass
cl.disconnect()
print('SUMMARY:', found)
