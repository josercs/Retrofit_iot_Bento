# Passo a Passo de Diagnóstico: MQTT → Telegraf → InfluxDB

Este guia documenta o procedimento para identificar e corrigir problemas de integração entre Mosquitto (MQTT), Telegraf e InfluxDB.

---

## 1. Verifique se todos os containers estão rodando

```powershell
docker ps
```
Todos os serviços essenciais (`mosquitto`, `telegraf`, `influxdb`, `collector`) devem estar com status "Up".

---

## 2. Cheque os logs do Telegraf

```powershell
docker logs telegraf --tail 50
```
Procure por erros como:
- `connect: connection refused`
- `network Error`
- Falha de autenticação

---

## 3. Confirme se o Mosquitto está ouvindo na porta correta

No `docker-compose.yml`, o serviço `mosquitto` deve expor a porta 1883:
```yaml
ports:
  - "1883:1883"
  - "8883:8883"
```
No `mosquitto.conf`, deve haver:
```
listener 1883 0.0.0.0
allow_anonymous true
```

---

## 4. Teste se o broker MQTT está recebendo mensagens

Use o comando:
```powershell
docker exec -it mqtt-broker mosquitto_sub -h localhost -p 1883 -t "#" -v
```
Se não aparecerem mensagens, o problema está no publisher.

---

## 5. Verifique a configuração do publisher (collector)

No arquivo `config.yaml`, o broker deve ser o nome do serviço Docker, não `localhost`:
```yaml
output:
  mode: mqtt
  mqtt:
    broker: mosquitto
    port: 1883
```
Reinicie o collector após ajustes:
```powershell
docker restart edge-collector
```

---

## 6. Reinicie os serviços após alterações

Sempre reinicie os containers afetados após mudanças em configuração:
```powershell
docker-compose up -d mosquitto
docker restart teleg