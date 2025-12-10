# Checklist: Edge Box pronta para ir ao cliente

Use este checklist marcável antes da entrega/instalação.

## Hardware e SO
- [ ] Box liga estável; ventilação e fixação adequadas
- [ ] Espaço em disco > 20% livre; RAM suficiente
- [ ] Relógio/NTP sincronizado

## Rede e PLC
- [ ] IPs configurados (Edge, PLC, Broker) e ping OK
- [ ] Porta S7 (102) acessível; DB número/tamanho corretos
- [ ] Firewall liberado apenas para portas necessárias

## MQTT / Telegraf / Influx / Grafana
- [ ] Broker TLS 8883 acessível (handshake OK com CA)
- [ ] Credenciais e ACL corretas (edge_agent publica `plc/#`, telegraf lê `plc/#`)
- [ ] Buckets Influx criados: `processo`, `processo_raw` (tokens válidos)
- [ ] Telegraf consumindo `plc/#` e escrevendo em Influx
- [ ] Grafana com datasource Flux provisionado e dashboards visíveis

## Configuração do Agente
- [ ] `config.yaml` revisado (ip/rack/slot/db_number/db_size/poll_interval)
- [ ] Placeholders resolvidos: `TENANT_ID`, `PLC_ID`; tópico final `plc/<tenant>/<plc>`
- [ ] TLS ativo (`tls: true`, `ca_file` correto)
- [ ] Métricas ativas em `/metrics` (porta `metrics_port`)

## Segurança
- [ ] Senhas/tokens fora do repositório (arquivo `.env`)
- [ ] Certificados válidos; `tls_insecure: false`
- [ ] Usuários desnecessários no broker removidos/bloqueados

## Operação e Observabilidade
- [ ] Dashboard de saúde com dados (measurement `s7_db1`, counters, latência)
- [ ] Métricas: `plc_read_ok/fail`, `plc_publish_ok/fail`, `edge_backlog_size`
- [ ] `queue.sqlite` íntegro; backlog sob controle
- [ ] Alertas mínimos configurados: ausência de pontos, backlog, latência alta

## Testes Finais
- [ ] Publicação sintética OK (script `publish_synthetic_payload.ps1`)
- [ ] Consulta Flux retorna pontos recentes (`processo_raw`)
- [ ] Scripts de diagnóstico executam: Grafana/Influx/MQTT

## Docker / Serviços
- [ ] `docker compose up -d --build` sem erros
- [ ] Healthchecks OK; volumes persistentes em `data/`

## Documentação e Suporte
- [ ] `LEIAME.md` e `OPERACOES.md` atualizados
- [ ] Contatos de suporte e plano de rollback definidos
- [ ] Inventário de versão/commit/branch e data de entrega

## Entrega
- [ ] `.gitignore` impede envio de secrets/certs/data
- [ ] Licença `LICENSE` (MIT) presente
- [ ] Checklist anexado ao ticket/ordem de serviço
