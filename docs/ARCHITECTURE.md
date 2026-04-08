# FRIDAY Architecture — System Organogram

```
                         ╔══════════════════════════════╗
                         ║         CL AUDIO (CJ)         ║
                         ║   👤  WhatsApp / Voice / CLI   ║
                         ╚═══════════╦══════════════════╝
                                     │ speaks / listens
                                     ▼
                    ┌────────────────────────────────┐
                    │      FRIDAY (ALIX mode)         │
                    │   🧠 Minimax M2.7 · Hermes v2.7  │
                    │  ┌────────────────────────────┐ │
                    │  │   RADHA WELLNESS 🪷💜       │ │
                    │  │   PT-BR · Portuguese Voice  │ │
                    │  └────────────────────────────┘ │
                    └──────────────┬─────────────────┘
                                   │
               ┌───────────────────┼───────────────────┐
               │                   │                   │
               ▼                   ▼                   ▼
     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
     │  VANGUARD       │  │  ATLAS          │  │  FORGE          │
     │  🛰️ Operator    │  │  📦 Archivist   │  │  🔧 Builder     │
     │  Healthchecks   │  │  PARA vault     │  │  Gateway/Deck   │
     │  Cron execution │  │  Memory index   │  │  Infra maint.   │
     │  MQTT bridge    │  │  5TB rclone     │  │  Zontes 368G    │
     └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
              │                     │                     │
              │                     │                     │
              ▼                     │                     │
     ┌─────────────────┐            │                     │
     │  MQTT BROKER     │            │                     │
     │  🛰️ Mosquitto    │            │                     │
     │  localhost:1883  │            │                     │
     └────────┬────────┘            │                     │
              │                     │                     │
              ▼                     │                     │
     ┌─────────────────┐            │                     │
     │  PAPERPILCE     │            │                     │
     │  🏢 AI Company   │            │                     │
     │  Control Plane  │            │                     │
     │  localhost:3100  │            │                     │
     │  HTTP Adapter   │◄────────────┘                     │
     └────────┬────────┘                                   │
              │                                           │
              │         SENTINEL 🛡️                        │
              │         Constitution QA                   │
              │         Rules enforcement                 │
              └──────────────────┬───────────────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              ▼                                     ▼
    ┌─────────────────┐                   ┌─────────────────┐
    │  C: DRIVE       │                   │  CLOUD STORAGE  │
    │  � Local        │                   │  📁 Google Drive │
    │  WSL2 /home/    │                   │  🔐 vault-crypt  │
    │  slim (minimal) │                   │  AES encrypted   │
    └─────────────────┘                   └─────────────────┘
              │                                     │
              └────────────────┬────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  PARA SYSTEM   🗂️ │
                    │  ┌───────────┐  │
                    │  │1_Projects │  │
                    │  │2_Areas    │  │
                    │  │3_Resources│  │
                    │  │4_Archives │  │
                    │  └───────────┘  │
                    └─────────────────┘
```

## Connections Detail

```
WhatsApp ──────► FRIDAY Gateway ──────► Hermes CLI / Minimax
                                   │
                                   ▼
                         ┌─────────────────┐
                         │  Hermes Agent    │
                         │  (AIAgent loop) │
                         └────────┬────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
    ┌────────────┐        ┌────────────┐        ┌────────────┐
    │  Vanguard  │        │   Atlas    │        │   Forge    │
    │  (active) │        │ (active)   │        │ (active)   │
    └─────┬──────┘        └─────┬──────┘        └─────┬──────┘
          │                     │                     │
          │ MQTT                │ rclone              │ SSH / services
          ▼                     ▼                     ▼
    ┌───────────┐          ┌───────────┐          ┌───────────┐
    │ Mosquitto │          │ vault-    │          │ Systemd   │
    │ :1883     │          │ crypt:    │          │ services  │
    └─────┬─────┘          └─────┬─────┘          └───────────┘
          │                     │
          │ HTTP POST           │
          ▼                     ▼
    ┌───────────┐          ┌───────────┐
    │ Paperclip │          │  Google   │
    │ :3100     │          │  Drive    │
    └───────────┘          └───────────┘
```

## Key Ports & Services

| Service | Port | Type | Status |
|---------|------|------|--------|
| Hermes Gateway | localhost:3101 | WebSocket | running |
| Paperclip CP | localhost:3100 | HTTP REST | running |
| Mosquitto MQTT | localhost:1883 | MQTT broker | running |
| MQTT Bridge | — | systemd service | running |

## Phase Roadmap

```
Phase 1 ✅  Gateway alive (WhatsApp ↔ Hermes)
Phase 2 ✅  Vanguard fleet (4 agents, MQTT, rclone vault)
Phase 3 🔄  Paperclip AI (Autonomous company · ONGOING)
Phase 4 ⬜  Omni-皇帝 (Full multimodal · future)
```

---
*Generated by FRIDAY · 2026-04-08*
