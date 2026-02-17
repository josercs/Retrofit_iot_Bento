# Onboarding Grafana Industrial Edge

Este guia orienta a configuração e uso dos dashboards industriais padronizados para monitoramento OT/Edge/PLC com InfluxDB e Grafana.

## 1. Pré-requisitos
- Grafana >= v8
- InfluxDB >= v2
- Datasource InfluxDB cadastrado no Grafana com UID: `R951FEA4DE68E13C5`
- Dashboards JSON validados e copiados para a pasta de provisionamento: `plc-mirror/infra/grafana/provisioning/dashboards/json/`

## 2. Provisionamento dos Dashboards
1. Copie todos os arquivos `.json` para a pasta de provisionamento do Grafana.
2. Reinicie o serviço do Grafana para carregar os dashboards automaticamente.
3. Verifique se todos os dashboards aparecem na interface e estão usando o datasource correto.

## 3. Estrutura dos Dashboards
- **Dashboard Unificado**: Visão geral OT/Edge, produção, status de máquinas, backlog, latência, qualidade.
- **Edge Health**: Saúde dos agentes, leituras OK/falha, MQTT, corrente/vibração, máquina ligada.
- **OEE Starter**: Disponibilidade, performance, qualidade, OEE calculado, variáveis por IP/DB.
- **Debug S7**: Painéis brutos para validação de ingestão e troubleshooting.

## 4. Variáveis e Filtros
- Todos os dashboards usam variáveis dinâmicas (site, line, machine_id, ip, db, plc_id, segment) para filtragem.
- As queries de variáveis usam o bucket `processo` e refletem os dados reais do ambiente.

## 5. Datasource
- Todos os painéis usam o objeto datasource: `{"type": "influxdb", "uid": "R951FEA4DE68E13C5"}`
- Se necessário, ajuste o UID no Grafana para corresponder ao ambiente.

## 6. Encoding e Validação
- Todos os arquivos JSON estão em UTF-8 sem BOM.
- Recomenda-se validar com `jq` ou `jsonlint` antes do provisionamento.

## 7. Troubleshooting
- Se algum painel não exibir dados, verifique:
  - UID do datasource
  - Permissões do bucket InfluxDB
  - Queries Flux e variáveis
  - Logs do agente e do Grafana

## 8. Customização
- Os dashboards são templates: podem ser duplicados e adaptados para novos segmentos, linhas ou sites.
- Recomenda-se manter o padrão de variáveis e queries para garantir compatibilidade futura.

## 9. Referências
- Documentação do projeto: `plc-mirror/docs/`
- Modelos de dados e exemplos: `plc-mirror/docs/DB500_LAYOUT.md`, `plc-mirror/docs/CONFIGURACAO.md`

---

Para dúvidas ou suporte, consulte o time de engenharia ou abra uma issue no repositório.
