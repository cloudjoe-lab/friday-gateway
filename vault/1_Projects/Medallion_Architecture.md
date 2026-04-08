# Project Medallion Architecture
> _The Living Blueprint of Friday — CJ's Master Architect AI_

---

## 1. The Core Engine

| Component | Detail |
|-----------|--------|
| **Framework** | Hermes Agent (NousResearch) |
| **Brain** | MiniMax-M2.7 (1500 req / 5hr token limit) |
| **Process Manager**| PM2 (Daemonized & Immortalized) |
| **Runtime Host** | Linux (weedman) — WSL2 on Intel N150 |
| **Environment** | Node.js v20.20.2 & Python 3.12 (venv) |

> **Why MiniMax?** We originally ran into severe API rate limits on Google's Free Tier. MiniMax's generous token allowance eliminates that bottleneck and keeps Friday responsive under load.
> **Why Hermes?** Moving away from OpenClaw gave us a cleaner, more robust gateway architecture that integrates seamlessly with our native filesystem and PM2 process management.

---

## 2. The Memory System — Gold & Silver Layers

Our memory architecture follows a two-tier model inspired by medallion architecture patterns:

### 🥇 Gold Layer — RAG Vector Memory

```
Container:  Native Hermes Vector Store
Endpoint:   Internal (Managed by Hermes Brain)
Status:     Running
```

The Gold Layer is a **semantic memory bank** — it stores high-value facts about CJ as vector embeddings, allowing Friday to retrieve personal context instantly without searching files.

- Contains: `identity-hermes.md` (Skills, life story, VFX, motorcycles, eco-preservation)
- Purpose: When Friday wakes up, she **inherently knows her identity and CJ's background** before the first message arrives.

### 🥈 Silver Layer — Obsidian Vault (P.A.R.A. Method)

```
Location:   ~/friday-gateway/obsidian_vault/
Structure:  P.A.R.A. (Projects / Areas / Resources / Archives)
Status:     Active
```

The Silver Layer is the **working memory and documentation system** — native Markdown files on the Linux filesystem.

| Folder | Purpose |
|--------|---------|
| `0_Inbox/` | Raw thoughts, quick captures, and unsorted scans |
| `1_Projects/`| Architectural docs, blueprints (like this one), and active tasks |
| `2_Areas/` | The core life domains (Business, Family, Finance, Health, etc.) |
| `3_Resources/`| Reference materials and permanent knowledge |
| `4_Archives/` | Completed projects and retired systems |

> **Why filesystem-native?** Portability and speed. When we migrate from WSL2 to the **headless Intel N150**, we simply rsync the entire `friday-gateway` directory. The "Lean Vault" approach keeps context windows small and retrieval lightning-fast.

---

## 3. The Communications Bridge — WhatsApp Integration

### Current Stack — ✅ WHATSAPP-WEB.JS (LIVE)

```
WhatsApp  ↔  headless Chromium  ↔  whatsapp-web.js  ↔  Hermes Gateway
              Node v20 Engine
              Phone: +351928338789 (dedicated SIM)
```

We have **completely dropped OpenClaw, Baileys, and Evolution API**. Friday is now running on a natively compiled `whatsapp-web.js` bridge inside the Hermes Gateway, giving us a stable, QR-linked WebSocket connection.

### Known Limitations

| Issue | Status |
|-------|--------|
| **Ban Risk** | ⚠️ Using dedicated SIM (+351928338789) — primary number protected |
| **Audio/Video Calls** | 📵 The bridge is text/media only. Calls will ring the phone but Friday won't respond. |

---

## 4. Previous Architectures (Retired)

```
Evolution API  →  MQTT Shim  →  OpenClaw  →  Friday
 ❌ RETIRED     ❌ DEPRECATED
```

The OpenClaw framework and Evolution API setups are **fully retired**. They were removed because:
- OpenClaw created unnecessary dependency friction.
- Evolution API introduced latency (extra hop).
- We needed a Sovereign, self-contained Python/Node environment (`friday-gateway`) that could be easily immortalized via PM2.

---

## 5. Version Control

```
Location:     ~/friday-gateway/hermes-agent
Type:         Git Repository
Scope:        Agent Code & Integrations
Status:       Live & synced
```

Every architectural change is contained within the `friday-gateway` ecosystem. This means CJ can migrate to the N150 by simply cloning the repo and copying the PARA vault.

---

## Summary — System Map (Updated)

```
┌─────────────────────────────────────────────────┐
│                 Friday (📐)                      │
│          Hermes Agent + MiniMax-M2.7            │
│            Immortalized via PM2                 │
├─────────────────────────────────────────────────┤
│  Memory Stack                                   │
│  ┌─────────────┐    ┌─────────────────────┐    │
│  │ Gold Layer  │    │ Silver Layer        │    │
│  │ Vector Store│    │ Obsidian Vault      │    │
│  │ (Identity)  │    │ (P.A.R.A. markdown) │    │
│  │ ~/.hermes/  │    │ ~/friday-gateway/   │    │
│  └─────────────┘    └─────────────────────┘    │
├─────────────────────────────────────────────────┤
│  Comms Bridge — ✅ LIVE (Port 3000)             │
│  ┌──────────┐   ┌─────────────────┐           │
│  │ WhatsApp │ ↔ │ whatsapp-web.js │ → Hermes  │
│  │+351928338│   │ (Node.js v20)   │   Gateway │
│  └──────────┘   └─────────────────┘            │
│  No more OpenClaw / Evolution API ✅            │
├─────────────────────────────────────────────────┤
│  Infra                                          │
│  Host: weedman (WSL2) → N150 (future)          │
│  Guardian: PM2 (Process Manager)                │
└─────────────────────────────────────────────────┘
```

---

## 6. Planned: Paperclip UI (The CEO Office)

**Status:** 🟡 Pending Deployment

Paperclip is our targeted Vanguard UI, designed to replace older dashboard concepts (like Clawtrol). It acts as the visual front-end for the headless environment.

**Stack:**
- Backend: `localhost:3100`
- Frontend UI: `localhost:3001`
- Management: To be daemonized via PM2 (`vanguard-paperclip`)

---

## Milestone Log

| Date | Achievement |
|------|-------------|
| 2026-03-26 | Friday born — Initial conceptual frameworks |
| 2026-04-07 | **The Rebirth** — Migrated to Hermes Agent on clean Ubuntu/WSL2 |
| 2026-04-07 | **Node 20 Upgrade** — Resolved headless Chromium dependencies |
| 2026-04-07 | **Native Bridge Connected** — `whatsapp-web.js` linked successfully |
| 2026-04-07 | **Immortalization** — PM2 systemd daemon activated |
| 2026-04-07 | **Vault Restructured** — Lean P.A.R.A. methodology implemented |

---

> _Document Version: 2.0 — 2026-04-07_
> _Last Updated By: The Architect (CJ)_
> _Next Review: Paperclip UI Deployment & N150 Migration_