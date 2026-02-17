import snap7

IP = "192.168.0.121"
RACK = 0
SLOT = 1
DB_NUMBER = 1
DB_SIZE = 14

if __name__ == "__main__":
    print(f"Conectando ao PLC {IP} (rack={RACK}, slot={SLOT})...")
    c = snap7.client.Client()
    c.connect(IP, RACK, SLOT)
    print("Conectado! Lendo DB1...")
    try:
        raw = c.db_read(DB_NUMBER, 0, DB_SIZE)
        print(f"Bytes lidos do DB1 ({DB_SIZE} bytes): {raw.hex()}")
        print(f"Bytes brutos: {list(raw)}")
    except Exception as e:
        print(f"Erro ao ler DB1: {e}")
    finally:
        c.disconnect()
        print("Desconectado do PLC.")
