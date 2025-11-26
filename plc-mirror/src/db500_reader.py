import yaml, json, time
try:
    import snap7
    from snap7.util import get_bool, get_real, get_int
except Exception as e:
    snap7 = None
    _snap7_err = e

# Expected layout in DB500 (14 bytes)
FIELDS = [
    ("pecas_ruim",    "bool", 0, 0),  # byte 0 bit 0
    ("pecas_boas",    "bool", 0, 1),  # byte 0 bit 1
    ("maquina_ligada","bool", 0, 2),  # byte 0 bit 2
    ("AI_Corrente",   "real", 2,  None),
    ("AI_Vibracao",   "real", 6,  None),
    ("contador_bom",  "int",  10, None),
    ("contador_ruim", "int",  12, None),
]

def read_values(ip: str, rack: int, slot: int, db_number: int, db_size: int):
    if not snap7:
        raise RuntimeError(f"snap7 not available: {_snap7_err}")
    c = snap7.client.Client()
    # Connect and fail fast if PLC is not reachable
    c.connect(ip, rack, slot)
    raw = c.db_read(db_number, 0, db_size)
    vals = {}
    for name, typ, byte, bit in FIELDS:
        if typ == "bool":
            vals[name] = get_bool(raw, byte, bit)
        elif typ == "real":
            vals[name] = float(get_real(raw, byte))
        elif typ == "int":
            vals[name] = int(get_int(raw, byte))
    c.disconnect()
    return vals
