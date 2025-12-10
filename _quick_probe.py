import yaml
import time

try:
    import snap7
except Exception as e:
    raise SystemExit(f"snap7 not available: {e}")

def try_read(ip: str, rack: int, slot: int, db: int, size: int):
    c = snap7.client.Client()
    try:
        c.connect(ip, rack, slot)
        t0 = time.time()
        raw = c.db_read(db, 0, size)
        dt = (time.time() - t0) * 1000.0
        print(f"OK ip={ip} rack={rack} slot={slot} db={db} size={size} len={len(raw)} latency_ms={dt:.1f}")
    except Exception as e:
        print(f"FAIL ip={ip} rack={rack} slot={slot} db={db} size={size} err={e}")
    finally:
        try:
            c.disconnect()
        except Exception:
            pass

def main():
    cfg = yaml.safe_load(open('/app/config.yaml','r',encoding='utf-8'))
    ip = cfg['source']['ip']
    # Probe common permutations
    for rack in (0,):
        for slot in (0, 1):
            for size in (2, 14, 16, 20, 32):
                try_read(ip, rack, slot, 1, size)

if __name__ == '__main__':
    main()
