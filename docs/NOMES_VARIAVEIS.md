# Nomes de Variáveis (pt-BR)

## Sinais do DB (exemplo DB500)
- pecas_ruim (bool): indica peça ruim.
- pecas_boas (bool): indica peça boa.
- maquina_ligada (bool): estado ON/OFF da máquina.
- AI_Corrente (real): corrente medida.
- AI_Vibracao (real): vibração medida.
- contador_bom (int): contador de peças boas.
- contador_ruim (int): contador de peças ruins.

## Métricas Prometheus
- plc_read_ok_total
- plc_read_fail_total
- plc_publish_ok_total{mode}
- plc_publish_fail_total{mode}
- plc_last_value{name}
- edge_backlog_size
- plc_read_latency_ms
- edge_up

## Metadados do payload
- ts (epoch segundos): timestamp da leitura/publicação.
- ip (string): IP do PLC.
- db (int): número do DB.
- values (objeto): mapa `nome → valor` conforme lista acima.
