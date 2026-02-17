import os
import json
import glob

def clean_json_file(filename):
    with open(filename, 'rb') as f:
        content = f.read()
    # Remove BOM se existir
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
    # Decode removendo caracteres não-ASCII
    text = content.decode('utf-8', errors='ignore')
    # Remove caracteres de controle
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    # Valida JSON
    try:
        data = json.loads(text)
        # Re-salva formatado
        new_filename = filename.replace('.json', '_clean.json')
        with open(new_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ {filename} → {new_filename}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ {filename}: {e}")
        return False

# Limpa todos os JSONs na pasta atual
json_dir = os.path.dirname(__file__)
for json_file in glob.glob(os.path.join(json_dir, '*.json')):
    if '_clean' not in json_file:
        clean_json_file(json_file)
