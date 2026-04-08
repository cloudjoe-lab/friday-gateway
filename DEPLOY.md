# Deploy Friday Gateway to GitHub

## Quick Push (One Command)

When you have your GitHub PAT ready, run:

```bash
cd ~/friday-gateway
GITHUB_TOKEN=ghp_your_real_token_here ./push-to-github.sh
```

Or if you install `gh` CLI:
```bash
sudo apt install gh
gh auth login
cd ~/friday-gateway && ./push-to-github.sh
```

---

## What Was Built Today 🦾

### Vanguard Paperclip — Phase 3.1 Complete

A full agent orchestration engine was built from scratch in `~/friday-gateway/paperclip/`:

```
paperclip/
├── src/
│   ├── index.js              # Express API server (port 3100)
│   ├── routes/
│   │   ├── health.js         # GET /health
│   │   ├── jobs.js           # Job queue CRUD
│   │   ├── agents.js         # Agent registry
│   │   └── commands.js       # Command dispatch
│   ├── services/
│   │   ├── queue.js          # In-memory job queue
│   │   ├── scheduler.js      # Cron scheduler (morning briefing)
│   │   └── heartbeat.js      # Agent liveness monitor
│   └── agents/
│       ├── base.js           # BaseAgent class
│       ├── atlas.js          # Memory & Indexing
│       ├── forge.js          # Infrastructure
│       └── sentinel.js       # QA & Constitution
├── ecosystem.config.cjs       # PM2 daemon config
└── tests/health.test.js      # Health endpoint test
```

### Systems That Are Live

| Service | Status | How |
|---------|--------|-----|
| Mosquitto MQTT | ✅ Online | `~/friday-gateway/mqtt/start_broker.sh` |
| SurrealDB Bronze | ✅ Online | `~/friday-gateway/surrealdb/start-bronze.sh` |
| MQTT→SurrealDB Bridge | ✅ Online | `systemctl --user start mqtt-bridge` |
| Vanguard Paperclip | ✅ Online | `pm2 start ecosystem.config.cjs` (in paperclip/) |

### Commits Made

```
68fb87d docs: add comprehensive README with architecture overview
3e583f2 vault: add PARA system project files
f1e14a3 feat: Vanguard Paperclip — Phase 3.1 agent orchestration engine
6435923 scripts: add MQTT-to-SurrealDB bridge and supporting tools
7113a78 fix: remove RocksDB data files and binary tarball from repo
2f589c3 surrealdb: add Bronze Layer startup script and schema
1c6a191 docs: add architecture overview and MQTT broker spec
```

### To Update the Repo Later

```bash
cd ~/friday-gateway
git add .
git commit -m "your message"
./push-to-github.sh   # or: git push origin main
```

---

*Friday AI — 2026-04-08 🪷*
