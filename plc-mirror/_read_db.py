import yaml  # Biblioteca para ler arquivos YAML (usada para carregar configurações)
import os    # Biblioteca para manipulação de caminhos e variáveis de ambiente

try:
    import snap7  # Biblioteca para comunicação com PLC Siemens S7
    from snap7.util import get_bool, get_real, get_int  # Funções utilitárias para extrair dados do buffer
except Exception as e:
    # Se snap7 não estiver instalado, encerra o programa com mensagem de erro
    raise SystemExit(f"snap7 missing: {e}")

# Define o caminho base do arquivo atual
BASE = os.path.dirname(os.path.abspath(__file__))
# Monta o caminho completo para o arquivo de configuração YAML
CFG_PATH = os.path.join(BASE, 'config.yaml')
# Carrega o arquivo de configuração YAML
cfg = yaml.safe_load(open(CFG_PATH,'r',encoding='utf-8'))
# Extrai as configurações de conexão do dicionário carregado
src = cfg['source']
ip = src['ip']  # Endereço IP do PLC
rack = src.get('rack',0)  # Número do rack (padrão 0)
slot = src.get('slot',1)  # Slot do PLC (padrão 1)
db = src.get('db_number',1)  # Número do bloco de dados (padrão 1)
size = src.get('db_size', 14)  # Tamanho do bloco de dados a ser lido (padrão 14 bytes)

# Permite sobrescrever o slot via variável de ambiente S7_SLOT
slot_env = os.getenv('S7_SLOT')
if slot_env:
    try:
        slot = int(slot_env)
    except Exception:
        pass  # Se não for possível converter, mantém o valor padrão

# Cria o cliente snap7 para comunicação com o PLC
c = snap7.client.Client()
try:
    # Tenta conectar ao PLC usando as configurações carregadas
    c.connect(ip, rack, slot)
except Exception as e:
    # Se falhar, encerra o programa com mensagem de erro
    raise SystemExit(f"CONNECT ERROR ip={ip} rack={rack} slot={slot}: {e}")
try:
    # Lê os dados brutos do bloco de dados especificado
    raw = c.db_read(db, 0, size)
except Exception as e:
    # Se falhar, encerra o programa com mensagem de erro
    raise SystemExit(f"DB READ ERROR db={db} size={size}: {e}")
finally:
    try:
        # Tenta desconectar do PLC (mesmo se houver erro na leitura)
        c.disconnect()
    except Exception:
        pass  # Ignora erros ao desconectar

def decode_simple14():
    # Decodifica os 14 bytes lidos do DB1 conforme layout esperado
    return {
        'pecas_ruim': bool(get_bool(raw, 0, 0)),         # Bit 0 do byte 0: indica peças ruins
        'pecas_boas': bool(get_bool(raw, 0, 1)),         # Bit 1 do byte 0: indica peças boas
        'maquina_ligada': bool(get_bool(raw, 0, 2)),     # Bit 2 do byte 0: máquina ligada/desligada
        'AI_Corrente': float(get_real(raw, 2)),          # Float (4 bytes) a partir do byte 2: corrente
        'AI_Vibracao': float(get_real(raw, 6)),          # Float (4 bytes) a partir do byte 6: vibração
        'contador_bom': int(get_int(raw, 10)),           # Inteiro (2 bytes) a partir do byte 10: contador bom
        'contador_ruim': int(get_int(raw, 12)),          # Inteiro (2 bytes) a partir do byte 12: contador ruim
    }

import json
# Imprime o resultado em formato JSON, incluindo o número do DB, tamanho e os valores decodificados
print(json.dumps({'db': db, 'size': size, 'values': decode_simple14()}, ensure_ascii=False, indent=2))
