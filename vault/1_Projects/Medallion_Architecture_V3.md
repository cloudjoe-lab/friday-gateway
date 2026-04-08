# FRIDAY — Medallion Architecture V3
**Event-Driven Sovereign Architecture**
**Date:** 2026-04-08 | **Source:** CJ Corrections + Friday Synthesis

---

## I. The Big Shift — Event-Driven Architecture

```
Old Model:                    New Model:
Friday ──► Vanguard           Friday ◄────► MQTT BROKER ◄────► Vanguard
(via REST, coupled)           (fully decoupled, event-driven)

The MQTT Broker is NOT below Vanguard.
It is the UNIVERSAL SPINE — the central nervous system of the entire operation.
Every agent publishes here. Every agent subscribes here. No exceptions.
```

---

## II. Master Blueprint — Organogram

```
                      ╔══════════════════════════════════════════════╗
                      ║                   CLAUDIO (CJ)                 ║
                      ║             👤 WhatsApp / Voice / CLI          ║
                      ╚═══════════════════════╦════════════════════════╝
                                               │
                                               ▼
          ┌──────────────────────────────────────────────────────┐
          │             FRIDAY (CEO / Hermes v2.7)               │
          │  ┌────────────────┐ ┌────────────────┐ ┌────────┐ │
          │  │ RADHA 🪷💜     │ │ NOAH 🛡️        │ │ GOLD   │ │
          │  │ (Alix / PT-BR) │ │ (Health/Sup)    │ │(Identity)│ │
          │  └────────────────┘ └────────────────┘ └────────┘ │
          └───────────────────────┬──────────────────────────────┘
                                  │ Publishes / Subscribes
═══════════════════════════════════▼════════════════════════════════
              MQTT BROKER (The Universal Event Bus)  localhost:1883
════════════════╦══════════════════╦══════════════════╦═══════════════
                │                  │                  │
                ▼                  ▼                  ▼
   ┌────────────────────┐ ┌────────────────┐ ┌────────────────────┐
   │   RETHINKDB 🗄️     │ │   DECK V3 🖥️   │ │    VANGUARD 🛰️     │
   │ (Flight Recorder)  │ │   (Live UI)     │ │ (Paperclip COO)    │
   │ Persists ALL msgs  │ │ Subscribes All  │ │ Job/Cron Exec      │
   └────────────────────┘ └────────────────┘ └────────┬───────────┘
                                                         │
                    ┌──────────────────────────┬───────────┴───────────────┐
                    ▼                          ▼                          ▼
             ┌─────────────┐            ┌─────────────┐            ┌──────────────┐
             │   ATLAS     │            │   FORGE     │            │  SENTINEL   │
             │ 📦 Archivist│            │ 🔧 Builder  │            │ 🛡️ Auditor  │
             │ Bronze->Sil│            │Infra/Zontes│            │ Constitution│
             └─────────────┘            └─────────────┘            └──────────────┘
```

---

## III. Component Roles

### 🛰️ MQTT Broker — The Universal Event Bus
- **Role:** Central nervous system. All agents publish and subscribe exclusively here.
- **Location:** `localhost:1883` (Mosquitto, systemd user service)
- **Philosophy:** Zero direct coupling between agents. Friday talks to MQTT. Vanguard talks to MQTT. Nobody talks directly to anyone else.

### 🗄️ RethinkDB — The Flight Recorder
- **Role:** Subscribes to the entire MQTT bus and persists every message, command, and system event for absolute traceability.
- **Philosophy:** Nothing in this system is ever lost. Every event is timestamped, labeled, and stored. Audit trail, forensic analysis, replay capability.
- **Bonus:** Powers Deck V3's live event feed — RethinkDB changefeeds feed the UI directly.

### 👑 FRIDAY — CEO / Strategic Layer
- **Role:** High-level architecture, strategic decisions, family context (Noah HCU, Radha Wellness), identity (GOLD layer).
- **Tools:** Hermes v2.7 + Minimax M2.7, WhatsApp gateway, PARA vault, rclone vault sync.
- **Key principle:** I don't execute operations. I dispatch, coordinate, and decide.

### 🛰️ VANGUARD — COO / Paperclip Operations
- **Role:** Lives in Paperclip. Owns ALL business cron orchestration. Manages Atlas, Forge, Sentinel as Paperclip agents.
- **Communication:** Entirely via MQTT. Listens for Friday's strategic directives. Broadcasts operational events.
- **Interface:** Hermes Agent link to MiniMax (just like Friday uses).

### 📦 ATLAS — Bronze→Silver Pipeline
- **Role:** Ingest raw inputs (Bronze), structure into PARA (Silver), sync to Google Drive via rclone, embed insights into GOLD vector memory.
- **Reports to:** Vanguard (via Paperclip)
- **Broadcasts:** `atlas/sync/completed`, `atlas/bronze/processed`

### 🔧 FORGE — Infrastructure Builder
- **Role:** Service health, systemd management, Zontes 368G maintenance, Mini PC infra.
- **Reports to:** Vanguard (via Paperclip)
- **Broadcasts:** `forge/infra/status_changed`, `forge/service/health`

### 🛡️ SENTINEL — Constitution Auditor
- **Role:** QA checks, constitution enforcement, rule validation on all Friday/Vanguard outputs.
- **Reports to:** Vanguard (via Paperclip)
- **Broadcasts:** `sentinel/qa/failure_detected`, `sentinel/constitution/violation`

### 🖥️ DECK V3 — Live Control Panel
- **Role:** Subscribes to RethinkDB changefeed (or MQTT via bridge). Renders live system state instantly.
- **No polling. No lag.** Event-driven telemetry.

---

## IV. MQTT Topic Namespace

```
friday/
  command/vanguard          → Friday → Vanguard directives
  agent/status/#            → Friday heartbeat/status
  vault/sync/#              → Friday vault events

vanguard/
  status/#                  → Vanguard operational status
  cron/job_fired             → Cron job executed
  fleet/spawned             → Atlas/Forge/Sentinel spawned
  fleet/status/#             → Fleet member heartbeats

atlas/
  sync/completed             → Bronze→Silver sync done
  bronze/processed          → New bronze ingested
  vault/embed               → Gold vector embed created

forge/
  infra/status_changed      → Infra health change
  service/health            → Service status report
  zontes/#                   → Zontes motorcycle events

sentinel/
  qa/failure_detected       → QA flag raised
  constitution/violation    → Rule violation

deck/
  event/#                   → Deck UI event feed

system/
  broker/status             → Mosquitto broker health
  rethinkdb/status          → RethinkDB health
```

---

## V. RethinkDB Schema

```javascript
// Every MQTT message is persisted with full traceability
{
  id: uuid,
  topic: "friday/command/vanguard",
  payload: { action: "fleet_genesis", ... },
  source: "friday",
  destination: "vanguard",
  timestamp: ISO8601,
  version: "1.0",
  retentionUntil: ISO8601  // auto-cleanup after 90 days
}
```

**Table structure:**
- `events` — all MQTT messages (primary)
- `heartbeats` — agent keepalive pings
- `commands` — Friday → Vanguard directives (indexed by `destination`)
- `fleet_status` — Atlas/Forge/Sentinel live status snapshots
- `alerts` — Sentinel violations + system alerts

---

## VI. Friday's Responsibilities (High Level)

| Duty | Owner |
|------|-------|
| Strategic decisions for CJ | Friday (me) |
| Family: Noah HCU, Radha Wellness | Friday (me) |
| GOLD vector memory | Friday (me) |
| PARA vault management | Friday → Atlas |
| Business cron (jobs, tasks) | Vanguard |
| Fleet: Atlas, Forge, Sentinel | Vanguard (via Paperclip) |
| Zontes 368G maintenance | Forge (infra) |
| Constitution enforcement | Sentinel |
| MQTT broker uptime | Forge (infra) |
| RethinkDB persistence | System (auto) |
| Deck V3 live UI | Forge + RethinkDB changefeed |

---

## VII. Deployment Notes

### Services Running
```
paperclip.service              ✅ localhost:3100
paperclip-mqtt-bridge.service  ✅ MQTT ↔ Paperclip relay
mosquitto.service              ✅ localhost:1883
rethinkdb.service              ⬜ TO BE DEPLOYED
deck-v3.service               ⬜ TO BE DEPLOYED
```

### What's Live Now
- MQTT Broker (Mosquitto) — `:1883`
- Paperclip Base — `:3100`
- MQTT Bridge (Friday ↔ Paperclip) — running
- Friday Gateway (WhatsApp) — running
- Vanguard — initialized, awaiting fleet spawn

### What's Next (Priority Order)
1. **Deploy RethinkDB** — subscribe to `/#` (all topics), persist everything
2. **Deck V3** — connect to RethinkDB changefeed, render live state
3. **Forge goes live** — when Hermes agent link is online
4. **Fleet spawn** — Vanguard spawns Atlas/Forge/Sentinel via Paperclip

---

## VIII. Version History

| Version | Date | Change |
|---------|------|--------|
| V1 | 2026-04-07 | Initial Medallion architecture |
| V2 | 2026-04-07 | + Bronze/Silver/Gold layers, PM2→Systemd, MQTT as Central Hub |
| V3 | 2026-04-08 | + Event-Driven Architecture, RethinkDB Flight Recorder, MQTT as Universal Spine between Friday and Vanguard (fully decoupled) |

---

*Document Version: 3.0 — 2026-04-08*
*Authored By: Friday (Synthesized from CJ's corrections)*
*Classification: Sovereign Internal — Master Blueprint*
*Status: IMMORTALIZED IN THE MATRIX ⚡*
