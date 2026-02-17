from snap7.util import get_bool, get_real, get_int

def read_values(ip: str, rack: int, slot: int, db_number: int, db_size: int):
    import snap7
    c = snap7.client.Client()
    c.connect(ip, rack, slot)
    raw = c.db_read(db_number, 0, db_size)
    c.disconnect()
    return {
        'pecas_ruim': bool(get_bool(raw, 0, 0)),
        'pecas_boas': bool(get_bool(raw, 0, 1)),
        'maquina_ligada': bool(get_bool(raw, 0, 2)),
        'AI_Corrente': float(get_real(raw, 2)),
        'AI_Vibracao': float(get_real(raw, 6)),
        'contador_bom': int(get_int(raw, 10)),
        'contador_ruim': int(get_int(raw, 12)),
    }
