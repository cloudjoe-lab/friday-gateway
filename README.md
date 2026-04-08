# Friday Gateway 🦾

**Status:** Phase 3.1 — Vanguard's Throne Built & Operational

> "Immortalize the Matrix."

The Friday Gateway is the sovereign infrastructure layer powering CJ's personal AI Matrix. It coordinates multiple AI agents (Vanguard, Atlas, Forge, Sentinel), a message broker (MQTT), and an event store (SurrealDB Bronze Layer) to run autonomous operations 24/7.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     HERMES GATEWAY                          │
│           (WhatsApp DM interface — primary)                 │
└──────────┬──────────────────────────────────────────────────┘
           │ dispatch
┌──────────▼──────────────────────────────────────────────────┐
│              VANGUARD PAPERCUP  [Port 3100]                 │
│     Agent Orchestration Engine — PM2 daemonized             │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   ATLAS      │   FORGE      │  SENTINEL    │   (stubs)     │
│  Archivist   │ Infrastructure│   Auditor    │               │
└──────┬───────┴──────┬───────┴──────┬───────┘               │
       │              │              │                         │
┌──────▼──────────────▼──────────────▼─────────────────────┐
│              MQTT BROKER  [Mosquitto 2.1.2 | Port 1883]    │
│         Wildcard subscribed — friday/# topic tree           │
└──────────────────────┬──────────────────────────────────────┘
                       │ persist
       ┌───────────────▼────────────────┐
       │   MQTT → SurrealDB Bridge       │
       │   (mqtt_to_surreal.py)          │
       │   systemd service               │
       └───────────────┬────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │   SURREALDB BRONZE LAYER        │
       │   [Port 8080 | RocksDB]         │
       │   Events + Metrics tables       │
       └─────────────────────────────────┘
```

---

## Systems Status

| Component | Status | Port/Location |
|-----------|--------|--------------|
| Mosquitto MQTT Broker | ✅ Online | 0.0.0.0:1883 |
| SurrealDB Bronze Layer | ✅ Online | 0.0.0.0:8080 |
| Vanguard Paperclip | ✅ Online | localhost:3100 |
| MQTT→SurrealDB Bridge | ✅ Online | systemd user svc |
| Hermes Gateway | ✅ Online | localhost:3000 |

---

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.10+
- SurrealDB binary (`surreal` in PATH or `~/friday-gateway/surrealdb/`)

### Start Everything

```bash
# 1. MQTT Broker
~/friday-gateway/mqtt/start_broker.sh

# 2. SurrealDB Bronze Layer
~/friday-gateway/surrealdb/start-bronze.sh

# 3. MQTT Bridge (systemd)
systemctl --user start mqtt-bridge.service

# 4. Vanguard Paperclip (PM2)
cd ~/friday-gateway/paperclip && pm2 start ecosystem.config.cjs
```

---

## Project Structure

```
friday-gateway/
├── paperclip/          # Vanguard Paperclip — Agent orchestration engine
│   ├── src/
│   │   ├── index.js           # Express API server
│   │   ├── routes/            # /health, /jobs, /agents, /commands
│   │   ├── services/         # Job queue, scheduler, heartbeat monitor
│   │   └── agents/           # Atlas, Forge, Sentinel stubs
│   ├── ecosystem.config.cjs  # PM2 config
│   └── pm2.config.js
├── mqtt/               # MQTT broker config
│   ├── config/         # mosquitto.conf, hbmqtt.yaml
│   ├── start_broker.sh
│   └── install_service.sh
├── surrealdb/          # SurrealDB Bronze Layer
│   ├── start-bronze.sh # Launch RocksDB-backed SurrealDB
│   └── setup.sql        # Schema definition
├── scripts/             # Operational scripts
│   ├── mqtt_to_surreal.py   # MQTT→SurrealDB bridge (core)
│   ├── setup-paperclip.sh
│   └── mqtt-*.py
├── vault/              # PARA system — project docs & knowledge
│   ├── 1_Projects/
│   ├── 2_Areas/
│   ├── 3_Resources/
│   └── 4_Archives/
└── docs/
    └── ARCHITECTURE.md
```

---

## Paperclip API

Vanguard Paperclip exposes a REST API on port 3100:

```
GET  /health          Full health + agent status + queue stats
POST /jobs            Enqueue a job
GET  /jobs            List all jobs
GET  /jobs/:id        Get job details
PATCH /jobs/:id       Update job (start/complete/fail)
DELETE /jobs/:id      Cancel pending job
POST /agents          Register a new agent
GET  /agents          List all registered agents
PATCH /agents/:name   Heartbeat / status update
POST /commands        Dispatch command to an agent
GET  /commands/types  List available command types
```

### Agent Roster

| Agent | Type | Role |
|-------|------|------|
| ATLAS | archivist | Memory & Indexing — vault management |
| FORGE | infrastructure | Gateway uptime, system maintenance |
| SENTINEL | auditor | QA — constitution enforcement |

---

## MQTT Topics

```
friday/bridge/           ← Bridge heartbeats & status
friday/agents/           ← Agent-to-agent messaging
friday/hermes/           ← Hermes Gateway events
friday/cron/             ← Scheduled job events
friday/commands/         ← Command dispatch
```

Full topic reference: `mqtt/TOPICS.md`

---

## Vault (PARA System)

The vault is synced to Google Drive via `rclone vault-crypt:`. Locally it lives at `~/friday-gateway/vault/`.

```
1_Projects/   Active deliverables (Paperclip Phase 3.1, BULL the Trader, etc.)
2_Areas/       Ongoing contexts (HCU Medical, Radha Wellness, Finance)
3_Resources/   Knowledge base (MiniMax playbook, Zontes manuals, recipes)
4_Archives/    Cold storage — completed years
```

---

## Phase Roadmap

- [x] **Phase 3.1** — Vanguard Paperclip: job queue, agent registry, command dispatch
- [ ] **Phase 3.2** — SurrealDB Silver Layer: computed aggregates & projections
- [ ] **Phase 3.3** — Atlas full implementation: PARA auto-enforcement, vault indexing
- [ ] **Phase 3.4** — Forge full implementation: self-healing gateway, auto-restart
- [ ] **Phase 3.5** — Sentinel full implementation: constitution enforcement, QA auditing
- [ ] **Phase 3.6** — BULL: autonomous day-trading agent integration

---

*Built with 🪷 by Friday AI — 2026-04-08*
