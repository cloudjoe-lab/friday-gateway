# MQTT Central Data Hub — Phase 3.1.2
> _Technical Specification — Universal Event Bus_
> _Author: Friday (Primary Developer)_
> _Date: 2026-04-08_
> _Status: SPEC DRAFT — Pending Implementation_

---

## 1. Overview

**What:** MQTT broker as the central data hub for the entire Friday/CJ ecosystem.
**Why:** Single real-time event bus for everything — AI agents, IoT devices, Home Assistant, and future integrations.
**Migration note:** Keep all host/port credentials in `.env`. No hardcoded values. WSL2 ↔ Mini PC ↔ Raspberry Pi — zero code changes when migrating.

---

## 2. Architecture — One Broker, Many Roles

### 2.1 The Central Data Hub Role

```
                    ┌─────────────────────────────────────────────────────┐
                    │         MQTT CENTRAL DATA HUB                      │
                    │                                                     │
                    │  ┌───────────────┐  ┌───────────────┐  ┌─────────┐  │
                    │  │ Friday       │  │ IoT Devices  │  │ Future  │  │
                    │  │ (subs/pub)   │  │ (sensors,    │  │ integrations│
                    │  │             │  │  switches)   │  │         │  │
                    │  └──────┬──────┘  └──────┬───────┘  └────┬────┘  │
                    │         │               │               │        │
                    │         └───────────────┴───────────────┘        │
                    │                        ↕                        │
                    │              ┌───────────────┐                 │
                    │              │ Home Assistant │                 │
                    │              │ (Raspberry Pi) │                │
                    │              │ + Broker backup│                │
                    │              └───────────────┘                 │
                    └─────────────────────────────────────────────────────┘
```

**The MQTT broker is the universal connector.** All components publish to and subscribe from the same broker, regardless of whether they are AI agents, IoT sensors, or home automation devices.

### 2.2 Deployment Environments

```
Deployment A — WSL2 on Windows Host (current)
┌─────────────────────────────────────────────────┐
│  Windows Host                                  │
│    └── mosquitto broker (EXISTING)             │
│         host: 127.0.0.1:1883                  │
│         (or custom port)                       │
│                                                 │
│  WSL2 Linux                                    │
│    └── Friday / Vanguard (future components)   │
│         connect to Windows broker via          │
│         WSL2 host IP                           │
└─────────────────────────────────────────────────┘

Deployment B — Mini PC (target primary deployment)
┌─────────────────────────────────────────────────┐
│  Mini PC (Linux bare-metal)                     │
│    └── mosquitto broker (NEW — PRIMARY)         │
│         host: 127.0.0.1:1883                   │
└─────────────────────────────────────────────────┘

Deployment C — Raspberry Pi (Home Assistant)
┌─────────────────────────────────────────────────┐
│  Raspberry Pi                                  │
│    └── Home Assistant OS                        │
│    └── Mosquitto broker (BACKUP/EDGE)           │
│         host: <rpi_ip>:1883                    │
│         ↕ syncs with Mini PC broker             │
└─────────────────────────────────────────────────┘
```

**Key rule:** Only ONE broker is primary at any time. All clients connect to `MQTT_HOST` from `.env`. When primary goes down, clients reconnect to backup automatically (MQTT reconnect logic).

---

## 3. MQTT Broker Installation

### 3.1 Windows (existing broker — no changes needed)

- CJ already has a broker running on Windows
- WSL2 processes connect to it via WSL2 host IP
- No installation needed for Windows side

### 3.2 Mini PC (target deployment — new broker)

```bash
# Install Mosquitto
sudo apt install mosquitto mosquitto-clients

# Enable as user service (no root needed)
systemctl --user enable mosquitto
systemctl --user start mosquitto

# Enable linger (starts service without user logged in)
loginctl enable-linger $USER

# Verify
systemctl --user status mosquitto
```

### 3.3 Raspberry Pi (Home Assistant — backup broker)

Home Assistant comes with a Mosquitto broker add-on. Enable it via:
- Home Assistant UI → Settings → Add-ons → Mosquitto Broker
- Or use the official Mosquitto app

**Redundancy:** The RPi broker runs independently. It does NOT need to bridge to the Mini PC broker for Home Assistant to work. HA devices publish/subscribe to RPi's local broker. For the AI agents to see IoT events, connect them to the RPi broker IP.

---

## 4. MQTT Configuration File

**Location:** `/home/krsna/friday-gateway/mqtt/config/mosquitto.conf`

### 4.1 Mini PC (primary broker)

```bash
# Listener
listener 1883 127.0.0.1

# Allow WebSocket for browser clients (Deck V3)
listener 9001 127.0.0.1
protocol websockets

# Protocol
protocol mqtt

# Persistence
persistence true
persistence_location /home/krsna/friday-gateway/mqtt/data/

# Logging
log_dest stdout
log_type error
log_type warning
log_type notice

# Security (Phase 3.3 — auth)
allow_anonymous true

# Max connections
max_connections -1

# Auto-save interval
autosave_interval 300
```

### 4.2 RPi / Home Assistant (backup broker)

The Home Assistant Mosquitto add-on is configured via HA UI. No manual config file needed. Access via:
- Home Assistant → Settings → Add-ons → Mosquitto Broker

---

## 5. Environment Variables (.env)

**File:** `/home/krsna/friday-gateway/.env` (never commit this file)

```bash
# ── MQTT Central Data Hub ──────────────────────────────────
# The primary broker address. All clients read from here.
# No hardcoded values — only .env.

# Mini PC (primary broker):
MQTT_HOST=127.0.0.1
MQTT_PORT=1883

# WSL2 (connect to Windows broker — current):
# MQTT_HOST=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
# MQTT_PORT=1883

# Raspberry Pi (backup broker — for HA redundancy):
# MQTT_HOST_RPI=<rpi_ip>
# MQTT_PORT_RPI=1883

# Optional auth (Phase 3.3)
# MQTT_USERNAME=
# MQTT_PASSWORD=

# Client identity
MQTT_CLIENT_ID=friday-gateway
MQTT_TLS=false

# Reconnection
MQTT_RECONNECT_INTERVAL=5000
```

**WSL2 Host Resolution (run once):**
```bash
WSL_HOST_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo "Windows host IP: $WSL_HOST_IP"
```

Store in `.env`:
```bash
MQTT_HOST=<resolved WSL host IP>
```

---

## 6. Topic Hierarchy — Universal Namespace

All topics follow: `realm/zone/resource/event`

```
# ── AI Agents (Friday ↔ Vanguard ↔ Atlas/Forge/Sentinel) ───
friday/agent/mention              # Friday mentioned by any agent
friday/agent/response            # Friday responds to agents
vanguard/cron/job_fired          # Vanguard fires a cron job
vanguard/cron/job_completed     # Vanguard completes a job
vanguard/cron/job_failed        # Vanguard job failed
vanguard/agent/registered       # Agent registered in Paperclip
vanguard/agent/heartbeat        # Agent heartbeat
vanguard/qa/failure_detected    # Sentinel found a QA failure
vanguard/qa/pass                # Sentinel passed QA
vanguard/vault/sync_started     # Atlas started Bronze→Silver sync
vanguard/vault/sync_completed   # Atlas completed Bronze→Silver sync
vanguard/infra/status_changed   # Forge detected infra change

# ── IoT / Home Assistant ────────────────────────────────────
ha/sensor/#                      # HA sensor readings (temp, humidity, etc.)
ha/binary_sensor/#              # HA binary sensors (motion, door, etc.)
ha/device/#                     # HA device state changes
ha/automation/#                 # HA automation triggers
ha/state/#                      # HA entity state changes

# ── Physical World ─────────────────────────────────────────
device/+/status                 # Generic device status (+ is wildcard)
device/+/telemetry             # Sensor readings
device/+/command               # Commands to devices

# ── Deck V3 (Control Panel) ─────────────────────────────────
deck/command                   # Friday sends command to Deck
deck/status                    # Deck sends status to Friday
deck/#                          # All Deck-related events
```

---

## 7. Event Schema

### 7.1 Standard Envelope (JSON)

```json
{
  "agent": "friday|vanguard|atlas|forge|sentinel|ha|device",
  "event_type": "cron.job.fired|sensor.reading|state.changed|...",
  "payload": { ... },
  "timestamp": "2026-04-08T06:00:00.000Z",
  "version": "1.0",
  "source": "ws://hostname:port or mqtt client id"
}
```

### 7.2 IoT / Home Assistant Events

```json
{
  "agent": "ha",
  "event_type": "sensor.reading",
  "payload": {
    "entity_id": "sensor.temperature_living_room",
    "state": "22.5",
    "unit_of_measurement": "°C",
    "friendly_name": "Temperature Living Room"
  },
  "timestamp": "2026-04-08T06:00:00.000Z",
  "version": "1.0",
  "source": "homeassistant"
}
```

---

## 8. Home Assistant Integration

### 8.1 RPi as MQTT Broker Redundancy

The Raspberry Pi runs Home Assistant OS with the Mosquitto broker add-on enabled. This means:
- Home Assistant devices publish to the RPi's local broker
- Friday/Vanguard subscribe to the same broker (or Mini PC broker if RPi is unreachable)
- If Mini PC goes down, RPi broker continues serving HA devices
- AI agents can subscribe to `ha/#` to monitor the home

### 8.2 HA → Friday Connection

**Option A (recommended):** Friday subscribes to `ha/#` on the Mini PC broker. HA is configured to bridge `ha/#` topics to the Mini PC broker via MQTT bridging.

**Option B (simpler):** HA and Friday connect to the same broker (Mini PC). RPi runs HA without its own broker — uses the Mini PC broker directly.

**Option C (full redundancy):** Both Mini PC and RPi brokers run simultaneously. MQTT bridging keeps them in sync. If Mini PC broker goes down, agents reconnect to RPi broker.

### 8.3 Home Assistant MQTT Discovery

HA auto-discovers MQTT devices. No manual entity setup needed — just configure HA to connect to the broker and entities appear automatically.

---

## 9. Paperclip Framework Integration (Phase 3.1.3)

### 9.1 What is Paperclip

**Paperclip** (paperclipai.net, GitHub: paperclipai/paperclip) is an existing open-source orchestration platform for AI agent teams. It is NOT a system we are building — it is an existing framework we are integrating.

Paperclip provides:
- Agent registry and management dashboard
- Goal alignment and task tracking
- Multi-agent coordination (Atlas, Forge, Sentinel live here)
- Cost budgets and audit trails
- Built-in PostgreSQL for persistence

### 9.2 Where Vanguard Lives

**Vanguard is the team lead inside Paperclip.** Paperclip is the office building. Vanguard is the COO who runs the office.

```
Friday (CEO — strategic command)
    ↓ MQTT + direct dispatch
Vanguard (COO — lives in Paperclip)
    ↓ coordinates via Paperclip API
  ├── Atlas agent (Bronze→Silver pipeline)
  ├── Forge agent (infra/service management)
  └── Sentinel agent (QA + constitution enforcement)
```

### 9.3 Friday ↔ Vanguard Interface

Friday and Vanguard communicate via:
1. **MQTT** — event broadcasts (job fired, QA result, vault sync)
2. **Paperclip API** — task dispatch, agent status queries
3. **WhatsApp** — CJ's natural interface to Friday

Vanguard does NOT need its own WhatsApp bridge. It operates inside Paperclip's dashboard and communicates with Friday via MQTT events.

### 9.4 Phase 3.1.3 Scope (separate spec)

- Deploy Paperclip (self-hosted or Zeabur one-click)
- Configure Vanguard as Paperclip admin agent
- Register Atlas, Forge, Sentinel as Paperclip worker agents
- Configure MQTT pub/sub between Friday and Paperclip
- Wire HA event feed into Paperclip monitoring

---

## 10. Systemd User Service (Mini PC)

**Location:** `/home/krsna/.config/systemd/user/mosquitto.service`

```ini
[Unit]
Description=Mosquitto MQTT Broker (user service — central data hub)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/sbin/mosquitto -c /home/krsna/friday-gateway/mqtt/config/mosquitto.conf
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536

[Install]
WantedBy=default.target
```

**Commands:**
```bash
systemctl --user daemon-reload
systemctl --user start mosquitto
systemctl --user enable mosquitto
systemctl --user status mosquitto
journalctl --user -u mosquitto -f
```

---

## 11. MQTT Client Libraries

### 11.1 Node.js (Paperclip — already supports MQTT natively)

Paperclip has built-in agent heartbeat and MQTT support. No extra library needed for Paperclip agents.

For custom Node.js components:
```bash
npm install mqtt
```

### 11.2 Python (Atlas, Forge, Sentinel, or HA bridge)

```bash
pip install paho-mqtt
```

---

## 12. Bronze Layer — MQTT Persistence with RethinkDB

**STATUS:** Pending spec — separate document (Phase 3.2).

MQTT is ephemeral — once a message is consumed, it's gone. The Bronze layer subscribes to all `vanguard/#` and `ha/#` topics and persists every event to RethinkDB for:
- Immutable audit trail
- Historical queries by Friday
- Deck V3 reads from RethinkDB (not MQTT directly)

**Design choice:** RethinkDB changefeeds push events to Deck V3 in real-time via WebSocket, eliminating the need for Deck V3 to run an MQTT client.

---

## 13. Migration Checklist — WSL2 → Mini PC → RPi HA

### Phase 1: WSL2 + Windows broker (NOW)
- [x] Windows broker running
- [ ] Update `.env` with WSL host IP for `MQTT_HOST`
- [ ] Verify WSL2 processes connect to Windows broker

### Phase 2: Mini PC (primary broker)
- [ ] Install mosquitto + mosquitto-clients
- [ ] Copy `mqtt/config/mosquitto.conf`
- [ ] Create systemd user service
- [ ] Update `.env` → `MQTT_HOST=127.0.0.1`
- [ ] Enablelinger: `loginctl enable-linger $USER`
- [ ] Test all components reconnect to Mini PC broker

### Phase 3: Raspberry Pi (Home Assistant + backup broker)
- [ ] Enable Mosquitto broker add-on in HA
- [ ] Configure HA to bridge `ha/#` topics to Mini PC broker (optional)
- [ ] Test failover: stop Mini PC broker → agents reconnect to RPi

**Zero code changes across all phases.** Only `.env` values change.

---

## 14. Implementation Order

```
NOW     → Use existing Windows broker (WSL2 connects via host IP)
SOON    → Spec Bronze/RethinkDB (MQTT persistence)
3.1.2.A → Mini PC: install mosquitto, systemd service, .env update
3.1.2.B → Paperclip: connect to MQTT broker, pub/sub for Vanguard
3.1.2.C → Friday: MQTT subscribe to agent events
3.1.3  → Paperclip framework deployment + Vanguard onboarding
3.2    → Bronze/RethinkDB layer (MQTT → RethinkDB persistence)
3.3    → Home Assistant integration (RPi broker, HA bridging)
```

---

*Document Version: 1.1 — 2026-04-08*
*Author: Friday*
*Major Changes: Clarified Paperclip is existing framework (not built here).*
*              Added HA/RPi as MQTT redundancy. Broadened topic namespace.*
*Classification: Sovereign Internal — Friday/CJ Ecosystem*
*Status: DRAFT — Pending CJ Approval*
