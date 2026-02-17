import yaml
import sys

try:
    import snap7
except Exception as e:
    print('ERROR: python-snap7 not installed or DLL missing:', e)
    sys.exit(1)

cfg = yaml.safe_load(open('config.yaml','r',encoding='utf-8'))
ips = [('source', cfg['source']['ip']), ('destination', cfg['destination']['ip'])]
rack = cfg.get('rack',0)
slot = cfg.get('slot',1)

results = {}
for name, ip in ips:
    c = snap7.client.Client()
    try:
        c.connect(ip, rack, slot)
        results[name] = 'OK' if c.get_connected() else 'FAIL'
    except Exception as e:
        results[name] = f'FAIL: {e}'
    finally:
        try:
            c.disconnect()
        except Exception:
            pass

print('RESULTS:', results)
