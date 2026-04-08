# MQTT Topic Namespace — Friday / Vanguard / Paperclip

## Broker
- Host: `127.0.0.1:1883` (WSL2 Mosquitto)
- No auth required (local only)

## Topic Tree

```
friday/
  command/
    vanguard          → Comandos de Friday para Vanguard (via Bridge → Paperclip HTTP)
  vanguard/
    status/           ← Status de Vanguard (Bridge republishing)
      heartbeat       → Heartbeat do Vanguard
      idle            → Vanguard em modo idle
      working         → Vanguard a processar tarefa
      error           → Erro reportado pelo Vanguard

vanguard/
  status/#            → Status nativo do Vanguard
    heartbeat
    idle
    working
    error
```

## Bridge Routing

| MQTT Topic IN              | Source | Action |
|----------------------------|--------|--------|
| `friday/command/vanguard`  | Friday | Forward → Paperclip HTTP adapter |
| `vanguard/status/#`        | Vanguard | Republish → `friday/vanguard/status/#` |

## Paperclip HTTP Adapter Payload

Quando um comando chega em `friday/command/vanguard`, o bridge faz POST para Paperclip:

```json
{
  "bridge": "paperclip-mqtt-bridge",
  "topic": "friday/command/vanguard",
  "payload": {
    "action": "ping",
    "taskId": "...",
    "context": {}
  },
  "timestamp": 1744104480.123
}
```

Paperclip precisa de ser configurado com o HTTP adapter a apontar para o bridge.

## Status Report (Vanguard → Friday)

Exemplo de payload em `vanguard/status/heartbeat`:

```json
{
  "agentId": "vanguard-001",
  "status": "heartbeat",
  "tasks": ["task-abc"],
  "timestamp": "2026-04-08T11:05:00Z"
}
```

## Test Commands

```bash
# Publicar comando (simular Friday)
mosquitto_pub -t friday/command/vanguard -m '{"action":"ping"}'

# Subscrever status
mosquitto_sub -t "friday/vanguard/status/#" -v
```
