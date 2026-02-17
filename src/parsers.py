"""Registro de parsers para leitura de DBs.
Permite escolher parser por nome a partir da configuração.
"""
from typing import Callable, Dict

from src.db500_reader import read_values as read_db500

def read_raw_bytes(ip: str, rack: int, slot: int, db_number: int, db_size: int):
    """Fallback: lê bytes do DB e retorna dict com hex/len.
    Útil quando layout não está implementado.
    """
    try:
        import snap7
    except Exception as e:
        raise RuntimeError(f'snap7 not available: {e}')
    c = snap7.client.Client()
    c.connect(ip, rack, slot)
    raw = c.db_read(db_number, 0, db_size)
    c.disconnect()
    return {
        'raw_hex': raw.hex(),
        'length': len(raw),
    }

# Mapa de funções de leitura por nome de parser
PARSERS: Dict[str, Callable[[str, int, int, int, int], dict]] = {
    'db500': read_db500,
    'raw': read_raw_bytes,
    # 'db200_balancas': implementar conforme layout das balanças
}

def get_reader(name: str) -> Callable[[str, int, int, int, int], dict]:
    return PARSERS.get(name, read_raw_bytes)