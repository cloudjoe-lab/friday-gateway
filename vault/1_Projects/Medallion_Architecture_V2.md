# FRIDAY — Revised Architecture Briefing
**Medallion + Paperclip Phase 3 — Updated Worldview**
**Date:** 2026-04-07 | **Source:** CJ Corrections

---

## I. Three Corrections Applied

### ✅ Correction 1: PM2 → Systemd
PM2 is retired. The core engine (Hermes Gateway) and all Vanguard services now run as **native Linux Systemd user services**. This is leaner, more sovereign, and properly integrated with the Linux host. No more PM2 daemon overhead.

### ✅ Correction 2: Bronze Layer Added
Three-tier memory architecture now complete:

| Layer | System | Purpose |
|-------|--------|---------|
| 🥇 **Gold** | Vector Store (`~/.hermes/`) | Identity, personal context — I wake up knowing who I am |
| 🥈 **Silver** | PARA Vault (`~/friday-gateway/vault/`) | Structured knowledge, projects, resources |
| 🥉 **Bronze** | Raw Inbox (`~/.hermes/bronze/`) | Unstructured drops, raw logs, unindexed media, traces |

**Atlas's real job:** Operate the Bronze→Silver pipeline. Every raw input that hits our system flows through Atlas for structuring. It ingests Bronze, enforces PARA discipline on Silver, syncs critical files to Google Drive via rclone, and embeds high-value insights into my Gold vector memory so I *inherently* know them without searching.

### ✅ Correction 3: MQTT Central Data Hub
Paperclip Phase 3.1.2 is not just REST APIs. The true nervous system is an **MQTT broker** — a real-time central data hub that ALL components publish to and subscribe from: Friday, Vanguard, Atlas, Forge, Sentinel, IoT devices, and Home Assistant.

```
Event Examples:
  • Vanguard fires a cron job       → MQTT broadcast (vanguard/cron/job_fired)
  • Sentinel flags a QA failure      → MQTT broadcast (vanguard/qa/failure_detected)
  • Atlas finishes a Bronze sync     → MQTT broadcast (vanguard/vault/sync_completed)
  • Forge pub: infra/status_changed → MQTT broadcast
  • IoT sensor reading              → MQTT broadcast (ha/sensor/#)
  • HA automation trigger           → MQTT broadcast (ha/automation/#)
  • CJ sends me a message           → Bronze trace → I respond via WhatsApp
  • Radha sends me a message        → Bronze trace → ALIX responds → broadcast to Deck
```

**Deck V3** subscribes to MQTT and reflects system state instantly — no polling, no lag. Just live telemetry. **Home Assistant** on the RPi also connects to this broker, making it a universal hub for both AI agents and smart home devices.

**Paperclip is NOT something we build.** It is an existing open-source framework (paperclipai.net, paperclipai/paperclip on GitHub) — the "company" where Vanguard and its team of agents live and work. Friday coordinates with Vanguard via MQTT, and Vanguard coordinates Paperclip and its agents (Atlas, Forge, Sentinel).

---

## II. Revised Fleet Dynamics — MQTT Changes Everything

### The Old Model (REST-based, polling)
```
CJ → Friday → [HTTP requests to sub-agents]
Sub-agents respond via callback URLs or polling
Friday is a relay, not a conductor
```

### The New Model (MQTT pub/sub, event-driven)
```
CJ (Strategic Command)
    ↓ WhatsApp (natural interface)
Friday (CEO — strategic decisions only)
    ↓ MQTT / direct dispatch
Vanguard (COO — lives in Paperclip, coordinates the Office)
    ↓ Paperclip framework API
┌──────────────────────────────────────────────────────────────┐
│                    PAPERCLIP FRAMEWORK                       │
│            (existing framework — paperclipai.net)            │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐    │
│   │  Atlas → Bronze→Silver pipeline + rclone + Gold     │    │
│   │  Forge → Service health, systemd management, infra  │    │
│   │  Sentinel → QA checks, constitution enforcement    │    │
│   └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
    ↓ MQTT (all events)
┌──────────────────────────────────────────────────────────────┐
│              MQTT CENTRAL DATA HUB (Mosquitto)               │
│                                                              │
│  📡 Vanguard pub: vanguard/cron/job_fired                    │
│  📡 Sentinel pub: vanguard/qa/failure_detected              │
│  📡 Atlas pub: vanguard/vault/sync_completed                 │
│  📡 Forge pub: vanguard/infra/status_changed                │
│  📡 HA sub: ha/sensor/#, ha/automation/#                    │
│  📡 IoT sub: device/+/status, device/+/telemetry           │
│                                                              │
│  📡 Deck V3 sub: all of the above (MQTT or RethinkDB feed)  │
│  📡 Friday sub: friday/agent/#, vanguard/#                 │
│  📡 Home Assistant (RPi) ← MQTT broker redundancy           │
└──────────────────────────────────────────────────────────────┘
```

### What This Means for Friday

**My job is now clearly strategic, not operational.** I don't manage the cron jobs — Vanguard does, and it broadcasts the results over MQTT. I don't poll sub-agents for status — I subscribe to the event feed. I don't manage the vault — Atlas does, and it signals Bronze→Silver completions over MQTT. I don't manage IoT or home automation — Home Assistant handles that, and events flow through the same MQTT hub.

**I stay clean, CJ stays free.** When CJ talks to me, I'm making the strategic call. When Vanguard fires, it broadcasts. When IoT sensors report, HA broadcasts. When Deck V3 renders, it reflects live state. No bottlenecks, no polling loops, no single points of failure.

### Coordination Hierarchy (As Designed)
```
CJ (Strategic Command)
    ↓ WhatsApp
Friday (CEO — I make the big calls)
    ↓ MQTT events + dispatch
Vanguard (COO — Paperclip's team lead)
    ↓ Paperclip framework
Paperclip (the existing framework — paperclipai.net)
    ├── Atlas → Bronze→Silver pipeline + rclone sync + Gold embeddings
    ├── Forge → Service health, systemd management, infra
    └── Sentinel → QA checks, constitution enforcement
    ↓ MQTT pub/sub
MQTT Central Data Hub (everything connects here)
    ↓
Home Assistant (Raspberry Pi — smart home + MQTT redundancy)
    ↓
Deck V3 (Friday Control Panel) ← MQTT or RethinkDB changefeed, live telemetry
```

This is a **true multi-agent architecture**. Friday sits at the top as CEO, Vanguard becomes the COO below me, and the three operational sub-agents report into Vanguard. CJ only speaks to me — I handle the rest through the chain.

---

## III. What This Means for Phase 3.1.2

The Phase 3.1.2 spec (MQTT Central Data Hub) needs to add:

1. **MQTT Broker service** (Mosquitto running as systemd user service on Mini PC)
2. **MQTT topic namespace** — standardized `realm/zone/resource/event` hierarchy
3. **Home Assistant** on RPi connected to the same broker (MQTT redundancy)
4. **MQTT client libraries** in Paperclip (mqtt.js for Node.js, paho-mqtt for any Python agents)
5. **Event schemas** — every broadcast message follows standardized envelope: `{ agent, event_type, payload, timestamp, version, source }`
6. **Bronze layer** — RethinkDB subscriber that persists all MQTT events
7. **Deck V3 MQTT/RethinkDB subscriber** — UI layer that reflects live state

The REST API (`/health`, `/jobs`, `/agents`, `/commands`) still exists for discrete operations and health checks, but the **live coordination** flows over MQTT.

## IV. What This Means for Phase 3.1.3 (Paperclip Integration)

**Paperclip** (paperclipai.net) is an existing open-source framework — NOT something we build. We integrate with it.

Phase 3.1.3 scope:
1. Deploy Paperclip (self-hosted on Mini PC, or Zeabur one-click)
2. Register Vanguard as the admin agent in Paperclip
3. Register Atlas, Forge, Sentinel as Paperclip worker agents
4. Configure MQTT pub/sub between Friday and Paperclip
5. Wire HA event feed into Paperclip monitoring dashboard

Paperclip provides its own PostgreSQL database for audit trails, task tracking, and agent state. Vanguard manages the Paperclip instance, not us.

---

## IV. My Assessment

This is a clean architecture. The three-tier memory (Bronze/Silver/Gold) gives me the right information hierarchy. The MQTT Central Data Hub means the system is reactive, not polling-based — and it's universal, connecting AI agents AND IoT devices. And the CJ→Friday→Vanguard→Paperclip chain keeps everyone at the right level of abstraction.

**One flag:** Atlas is the most complex agent in this stack, but it lives INSIDE Paperclip once we integrate. Atlas still needs to:
- Watch the Bronze folder for new drops
- Run PARA structuring logic (decide which folder a file belongs in)
- Execute rclone sync to Google Drive (with encryption)
- Generate vector embeddings for Gold layer insertion
- Publish Bronze→Silver completion events to MQTT

That's a full service. I'd treat Atlas as a Phase 3.2 priority at minimum, with a proper spec before implementation — but it now lives in Paperclip's agent framework, so it's better isolated.

**Another flag:** Home Assistant MQTT redundancy needs careful setup. The RPi broker and Mini PC broker should NOT be running as a cluster unless we set up MQTT bridging properly. Simpler approach: HA connects to Mini PC broker directly. RPi broker runs only for HA's own redundancy. Friday/Vanguard connect to Mini PC broker only.

---

*Document Version: 2.1 — 2026-04-08*
*Last Updated By: Friday (Synthesized from CJ Corrections)*
*Classification: Sovereign Internal — Vanguard Fleet Architecture*
*Status: IMMORTALIZED IN THE MATRIX*