# Testes e Qualidade (pt-BR)

## Executar testes
- Windows PowerShell com venv do projeto:
  - Ative a venv e rode `python -m pytest -q`.
- A suíte é limitada a `plc-mirror/tests` por `pytest.ini`.
- Scripts de diagnóstico na raiz (ex.: `_conn_test.py`) não são testes automatizados.

## Escopo atual
- test_mirror.py: valida `PLCMirror.mirror_once()`.
- test_store.py: valida fila SQLite (enqueue/dequeue/delete e concorrência básica).
- test_config_loader.py: valida overrides por ambiente e normalização MQTT.

## Próximos testes sugeridos
- Mocks de `mqtt` e `requests` para validar publicação e backlog no `agent`.
- Testes de falha de leitura (snap7 ausente) publicando heartbeat com `read_failed`.
- Checagem do endpoint `/metrics` e `/api/last`.
