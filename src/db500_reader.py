import yaml, json, time, os
try:
    import snap7
    from snap7.util import get_bool, get_real, get_int
except Exception as e:
    snap7 = None
    _snap7_err = e

"""
Leitura de DB500 em layout simples (uma máquina) – 14 bytes:

byte 0 bits: 0=pecas_ruim, 1=pecas_boas, 2=maquina_ligada
REAL em 2 (AI_Corrente)
REAL em 6 (AI_Vibracao)
INT em 10 (contador_bom)
INT em 12 (contador_ruim)
"""

def read_values(ip: str, rack: int, slot: int, db_number: int, db_size: int):
    if not snap7:
        raise RuntimeError(f"snap7 not available: {_snap7_err}")
    c = snap7.client.Client()
    c.connect(ip, rack, slot)
    raw = c.db_read(db_number, 0, db_size)
    c.disconnect()

    # Parse layout simples de 14 bytes
    vals = {}
    try:
        vals['pecas_ruim'] = bool(get_bool(raw, 0, 0))
    except Exception:
        vals['pecas_ruim'] = None
    try:
        vals['pecas_boas'] = bool(get_bool(raw, 0, 1))
    except Exception:
        vals['pecas_boas'] = None
    try:
        vals['maquina_ligada'] = bool(get_bool(raw, 0, 2))
    except Exception:
        vals['maquina_ligada'] = None
    try:
        vals['AI_Corrente'] = float(get_real(raw, 2))
    except Exception:
        vals['AI_Corrente'] = None
    try:
        vals['AI_Vibracao'] = float(get_real(raw, 6))
    except Exception:
        vals['AI_Vibracao'] = None
    try:
        vals['contador_bom'] = int(get_int(raw, 10))
    except Exception:
        vals['contador_bom'] = None
    try:
        vals['contador_ruim'] = int(get_int(raw, 12))
    except Exception:
        vals['contador_ruim'] = None

    return vals
