# Project Paperclip — Phase 3.1: The Backend
> _Technical Specification — Vanguard's Throne_
> _Author: Friday (Primary Developer)_
> _Date: 2026-04-07_
> _Status: SPEC APPROVED — Awaiting Implementation_

---

## 1. Overview

**What:** Paperclip backend — the operating system for Vanguard
**Why:** Enables sub-agent spawning, job queuing, health monitoring, and cron orchestration
**Scope of Phase 3.1:** Core Express/Node.js backend, PM2 daemonization, basic health endpoint, job queue stub

**Critical Constraint:** This is NOT a frontend. Phase 3.1 builds the engine only. No React, no dashboard. Pure API layer.

---

## 2. Folder Structure

```
~/friday-gateway/paperclip/
├── package.json              # Dependencies
├── pm2.config.js             # PM2 daemon config
├── ecosystem.config.cjs      # Legacy PM2 compat
├── src/
│   ├── index.js              # Entry point
│   ├── config/
│   │   └── index.js          # Environment variables, port, host
│   ├── routes/
│   │   ├── health.js         # GET /health
│   │   ├── jobs.js           # Job queue CRUD
│   │   ├── agents.js         # Sub-agent registry
│   │   └── commands.js       # Command dispatch
│   ├── services/
│   │   ├── queue.js          # In-memory job queue
│   │   ├── scheduler.js      # Cron-like job runner
│   │   └── heartbeat.js      # Agent heartbeat monitor
│   ├── agents/
│   │   ├── base.js           # Abstract agent class
│   │   ├── atlas.js          # Atlas agent (stub for 3.1)
│   │   ├── forge.js          # Forge agent (stub for 3.1)
│   │   └── sentinel.js       # Sentinel agent (stub for 3.1)
│   ├── vault/
│   │   └── logger.js         # Vault-backed logging
│   └── utils/
│       └── response.js       # Standardized JSON responses
├── tests/
│   ├── health.test.js
│   ├── jobs.test.js
│   └── queue.test.js
└── README.md                 # Setup instructions
```

---

## 3. package.json

```json
{
  "name": "vanguard-paperclip",
  "version": "0.1.0",
  "description": "Vanguard's throne — task orchestration engine",
  "main": "src/index.js",
  "type": "module",
  "scripts": {
    "start": "node src/index.js",
    "dev": "node --watch src/index.js",
    "test": "node --test tests/"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "node-cron": "^3.0.3",
    "uuid": "^9.0.0",
    "axios": "^1.6.7"
  },
  "devDependencies": {
    "express-async-errors": "^3.1.1"
  },
  "engines": {
    "node": ">=20.0.0"
  }
}
```

---

## 4. Core Files

### 4.1 `src/config/index.js`

```javascript
import 'dotenv/config';

export const config = {
  port: parseInt(process.env.PAPERCLIP_PORT || '3100', 10),
  host: process.env.PAPERCLIP_HOST || '0.0.0.0',
  env: process.env.NODE_ENV || 'development',

  // Vanguard (me) connection
  fridayUrl: process.env.FRIDAY_URL || 'http://localhost:3000',

  // Sub-agent heartbeat interval (ms)
  heartbeatInterval: parseInt(process.env.HEARTBEAT_INTERVAL || '30000', 10),

  // Job queue settings
  maxConcurrentJobs: parseInt(process.env.MAX_CONCURRENT_JOBS || '5', 10),
  jobTimeout: parseInt(process.env.JOB_TIMEOUT || '300000', 10), // 5 min default

  // Logging
  logLevel: process.env.LOG_LEVEL || 'info',
};
```

### 4.2 `src/index.js`

```javascript
import express from 'express';
import cors from 'cors';
import { config } from './config/index.js';
import healthRoutes from './routes/health.js';
import jobsRoutes from './routes/jobs.js';
import agentsRoutes from './routes/agents.js';
import commandsRoutes from './routes/commands.js';
import { initializeHeartbeat } from './services/heartbeat.js';
import { initializeScheduler } from './services/scheduler.js';
import { logger } from './vault/logger.js';

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Request logging
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, { ip: req.ip });
  next();
});

// Routes
app.use('/health', healthRoutes);
app.use('/jobs', jobsRoutes);
app.use('/agents', agentsRoutes);
app.use('/commands', commandsRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Paperclip',
    version: '0.1.0',
    status: 'operational',
    uptime: process.uptime(),
  });
});

// Error handler
app.use((err, req, res, next) => {
  logger.error(err.message, { stack: err.stack });
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
  });
});

// Start server
app.listen(config.port, config.host, () => {
  logger.info(`Paperclip running on ${config.host}:${config.port}`);

  // Initialize background services
  initializeHeartbeat();
  initializeScheduler();
});
```

### 4.3 `src/routes/health.js`

```javascript
import { Router } from 'express';
import { process uptime } from 'os';

const router = Router();

router.get('/', (req, res) => {
  const mem = process.memoryUsage();

  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: Math.floor(process.uptime()),
    memory: {
      rss: `${Math.round(mem.rss / 1024 / 1024)}MB`,
      heapUsed: `${Math.round(mem.heapUsed / 1024 / 1024)}MB`,
    },
    agents: {
      atlas: { status: 'unknown' },
      forge: { status: 'unknown' },
      sentinel: { status: 'unknown' },
    },
    queue: {
      pending: 0,
      running: 0,
      completed: 0,
      failed: 0,
    },
  });
});

export default router;
```

### 4.4 `src/routes/jobs.js`

```javascript
import { Router } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { enqueue, getJob, listJobs, updateJob, cancelJob } from '../services/queue.js';
import { ok, created, error } from '../utils/response.js';

const router = Router();

// POST /jobs — Enqueue a new job
router.post('/', async (req, res) => {
  try {
    const { type, payload, priority } = req.body;

    if (!type) {
      return error(res, 'Job type is required', 400);
    }

    const job = await enqueue({ type, payload, priority: priority || 'normal' });
    created(res, job);
  } catch (err) {
    error(res, err.message);
  }
});

// GET /jobs — List all jobs
router.get('/', (req, res) => {
  const { status, limit } = req.query;
  const jobs = listJobs({ status, limit: parseInt(limit) || 50 });
  ok(res, { jobs, count: jobs.length });
});

// GET /jobs/:id — Get single job
router.get('/:id', (req, res) => {
  const job = getJob(req.params.id);
  if (!job) return error(res, 'Job not found', 404);
  ok(res, job);
});

// PATCH /jobs/:id — Update job (e.g., mark complete)
router.patch('/:id', (req, res) => {
  const updated = updateJob(req.params.id, req.body);
  if (!updated) return error(res, 'Job not found', 404);
  ok(res, updated);
});

// DELETE /jobs/:id — Cancel job
router.delete('/:id', (req, res) => {
  const cancelled = cancelJob(req.params.id);
  if (!cancelled) return error(res, 'Job not found', 404);
  ok(res, { cancelled: true });
});

export default router;
```

### 4.5 `src/routes/agents.js`

```javascript
import { Router } from 'express';
import { registerAgent, listAgents, getAgent, updateAgent } from '../services/heartbeat.js';
import { ok, created, error } from '../utils/response.js';

const router = Router();

// POST /agents — Register a new agent
router.post('/', (req, res) => {
  const { name, type, url, capabilities } = req.body;

  if (!name || !type) {
    return error(res, 'Agent name and type are required', 400);
  }

  const agent = registerAgent({ name, type, url, capabilities });
  created(res, agent);
});

// GET /agents — List all registered agents
router.get('/', (req, res) => {
  const agents = listAgents();
  ok(res, { agents, count: agents.length });
});

// GET /agents/:name — Get agent details
router.get('/:name', (req, res) => {
  const agent = getAgent(req.params.name);
  if (!agent) return error(res, 'Agent not found', 404);
  ok(res, agent);
});

// PATCH /agents/:name — Update agent status/heartbeat
router.patch('/:name', (req, res) => {
  const updated = updateAgent(req.params.name, req.body);
  if (!updated) return error(res, 'Agent not found', 404);
  ok(res, updated);
});

export default router;
```

### 4.6 `src/routes/commands.js`

```javascript
import { Router } from 'express';
import { dispatchCommand } from '../services/scheduler.js';
import { ok, error } from '../utils/response.js';

const router = Router();

// POST /commands — Dispatch a command to Vanguard's queue
router.post('/', async (req, res) => {
  try {
    const { command, target, payload } = req.body;

    if (!command) {
      return error(res, 'Command is required', 400);
    }

    const jobId = await dispatchCommand({ command, target, payload });
    ok(res, { jobId, status: 'queued' });
  } catch (err) {
    error(res, err.message);
  }
});

export default router;
```

### 4.7 `src/services/queue.js`

```javascript
import { v4 as uuidv4 } from 'uuid';
import { config } from '../config/index.js';

const jobs = new Map();

export const JOB_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
};

export async function enqueue({ type, payload, priority }) {
  const id = uuidv4();
  const job = {
    id,
    type,
    payload,
    priority,
    status: JOB_STATUS.PENDING,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    result: null,
    error: null,
  };

  jobs.set(id, job);

  // Auto-start job processing
  setImmediate(() => processJob(id));

  return job;
}

export function getJob(id) {
  return jobs.get(id) || null;
}

export function listJobs({ status, limit = 50 }) {
  let all = Array.from(jobs.values());

  if (status) {
    all = all.filter(j => j.status === status);
  }

  return all
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, limit);
}

export function updateJob(id, updates) {
  const job = jobs.get(id);
  if (!job) return null;

  const updated = {
    ...job,
    ...updates,
    updatedAt: new Date().toISOString(),
  };

  jobs.set(id, updated);
  return updated;
}

export function cancelJob(id) {
  const job = jobs.get(id);
  if (!job) return false;

  if (job.status === JOB_STATUS.RUNNING) {
    return false; // Cannot cancel running job
  }

  updateJob(id, { status: JOB_STATUS.CANCELLED });
  return true;
}

async function processJob(id) {
  const job = jobs.get(id);
  if (!job || job.status !== JOB_STATUS.PENDING) return;

  updateJob(id, { status: JOB_STATUS.RUNNING });

  try {
    // Placeholder — actual job processing logic goes here
    // In Phase 3.5 this will dispatch to the appropriate agent
    const result = await executeJob(job);

    updateJob(id, {
      status: JOB_STATUS.COMPLETED,
      result,
    });
  } catch (err) {
    updateJob(id, {
      status: JOB_STATUS.FAILED,
      error: err.message,
    });
  }
}

async function executeJob(job) {
  // Stub: jobs execute here. Real implementation in 3.5.
  // For now, just echo back the job type
  return { processed: true, type: job.type, at: new Date().toISOString() };
}
```

### 4.8 `src/services/heartbeat.js`

```javascript
import { config } from '../config/index.js';
import { logger } from '../vault/logger.js';

const agents = new Map();

export function registerAgent({ name, type, url, capabilities }) {
  const agent = {
    name,
    type,
    url,
    capabilities: capabilities || [],
    status: 'registered',
    lastSeen: new Date().toISOString(),
    registeredAt: new Date().toISOString(),
  };

  agents.set(name, agent);
  logger.info(`Agent registered: ${name} (${type})`);

  return agent;
}

export function listAgents() {
  return Array.from(agents.values());
}

export function getAgent(name) {
  return agents.get(name) || null;
}

export function updateAgent(name, updates) {
  const agent = agents.get(name);
  if (!agent) return null;

  const updated = {
    ...agent,
    ...updates,
    lastSeen: new Date().toISOString(),
  };

  agents.set(name, updated);
  return updated;
}

export function initializeHeartbeat() {
  // Periodic health check on registered agents
  setInterval(() => {
    const now = Date.now();
    const staleThreshold = config.heartbeatInterval * 3; // 3 missed pings = stale

    for (const [name, agent] of agents) {
      const lastSeen = new Date(agent.lastSeen).getTime();
      if (now - lastSeen > staleThreshold) {
        updateAgent(name, { status: 'stale' });
        logger.warn(`Agent stale: ${name}`);
      }
    }
  }, config.heartbeatInterval);

  logger.info('Heartbeat monitor initialized');
}
```

### 4.9 `src/services/scheduler.js`

```javascript
import cron from 'node-cron';
import { enqueue } from './queue.js';
import { logger } from '../vault/logger.js';
import { config } from '../config/index.js';

const scheduledJobs = new Map();

export async function dispatchCommand({ command, target, payload }) {
  // Create a job for the command
  const job = await enqueue({
    type: `command:${command}`,
    payload: { command, target, payload },
    priority: payload?.priority || 'normal',
  });

  logger.info(`Command dispatched: ${command} -> ${target || 'any'}`);

  return job.id;
}

export function scheduleRecurring({ name, cronExpression, task }) {
  if (scheduledJobs.has(name)) {
    logger.warn(`Scheduled job already exists: ${name}`);
    return;
  }

  const job = cron.schedule(cronExpression, async () => {
    logger.info(`Running scheduled task: ${name}`);
    try {
      await task();
    } catch (err) {
      logger.error(`Scheduled task failed: ${name}`, { error: err.message });
    }
  });

  scheduledJobs.set(name, job);
  logger.info(`Scheduled recurring job: ${name} (${cronExpression})`);

  return job;
}

export function initializeScheduler() {
  // Morning briefing — 08:00 Lisbon time
  scheduleRecurring({
    name: 'morning-briefing',
    cronExpression: '0 8 * * *',
    task: () => morningBriefing(),
  });

  // Healthcheck — every 15 minutes
  scheduleRecurring({
    name: 'healthcheck',
    cronExpression: '*/15 * * * *',
    task: () => runHealthcheck(),
  });

  logger.info('Scheduler initialized');
}

async function morningBriefing() {
  logger.info('Morning briefing triggered');
  // TODO: In Phase 3.5, this will notify Friday via Hermes Gateway
}

async function runHealthcheck() {
  logger.info('Healthcheck triggered');
  // TODO: In Phase 3.5, this will ping Hermes Gateway, WhatsApp bridge
}
```

### 4.10 `src/vault/logger.js`

```javascript
// Vault-backed logging — logs to both console and vault log files
import { appendFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { getHermesHome } from '../utils/path.js';

const LOG_DIR = join(getHermesHome(), 'paperclip-logs');
const LOG_FILE = join(LOG_DIR, `paperclip-${new Date().toISOString().split('T')[0]}.log`);

function ensureLogDir() {
  if (!existsSync(LOG_DIR)) {
    mkdirSync(LOG_DIR, { recursive: true });
  }
}

function format(level, message, meta = {}) {
  const timestamp = new Date().toISOString();
  const metaStr = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
  return `[${timestamp}] [${level.toUpperCase()}] ${message}${metaStr}\n`;
}

export const logger = {
  info(message, meta) {
    console.log(format('info', message, meta));
    ensureLogDir();
    appendFileSync(LOG_FILE, format('info', message, meta));
  },

  warn(message, meta) {
    console.warn(format('warn', message, meta));
    ensureLogDir();
    appendFileSync(LOG_FILE, format('warn', message, meta));
  },

  error(message, meta) {
    console.error(format('error', message, meta));
    ensureLogDir();
    appendFileSync(LOG_FILE, format('error', message, meta));
  },

  debug(message, meta) {
    if (process.env.LOG_LEVEL === 'debug') {
      console.log(format('debug', message, meta));
      ensureLogDir();
      appendFileSync(LOG_FILE, format('debug', message, meta));
    }
  },
};
```

### 4.11 `src/utils/response.js`

```javascript
// Standardized JSON response helpers

export function ok(res, data) {
  return res.json({ success: true, data });
}

export function created(res, data) {
  return res.status(201).json({ success: true, data });
}

export function error(res, message, status = 500) {
  return res.status(status).json({ success: false, error: message });
}
```

### 4.12 `src/utils/path.js`

```javascript
// Path utility — respects HERMES_HOME for profile support
import { env } from 'process';

export function getHermesHome() {
  return env.HERMES_HOME || env.HOME + '/.hermes';
}
```

### 4.13 `src/agents/base.js`

```javascript
// Abstract base class for sub-agents
export class BaseAgent {
  constructor({ name, type, url }) {
    this.name = name;
    this.type = type;
    this.url = url;
    this.status = 'idle';
  }

  async ping() {
    // Health check — verify agent is reachable
    const response = await fetch(`${this.url}/health`);
    return response.ok;
  }

  async sendCommand(command, payload) {
    // Dispatch command to this agent
    const response = await fetch(`${this.url}/commands`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, payload }),
    });
    return response.json();
  }
}
```

### 4.14 `pm2.config.js`

```javascript
export default {
  apps: [
    {
      name: 'vanguard-paperclip',
      script: './src/index.js',
      interpreter: 'node',
      node_args: '--experimental-vm-modules',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PAPERCLIP_PORT: 3100,
        FRIDAY_URL: 'http://localhost:3000',
        LOG_LEVEL: 'info',
      },
      env_development: {
        NODE_ENV: 'development',
        PAPERCLIP_PORT: 3100,
        FRIDAY_URL: 'http://localhost:3000',
        LOG_LEVEL: 'debug',
      },
    },
  ],
};
```

### 4.15 `ecosystem.config.cjs`

```javascript
// Legacy CommonJS PM2 config (for compatibility)
module.exports = {
  apps: [
    {
      name: 'vanguard-paperclip',
      script: './src/index.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PAPERCLIP_PORT: 3100,
        FRIDAY_URL: 'http://localhost:3000',
      },
    },
  ],
};
```

---

## 5. PM2 Setup Commands

```bash
# Navigate to paperclip directory
cd ~/friday-gateway/paperclip

# Install dependencies
npm install

# Start in development mode (foreground)
npm run dev

# Start in production (PM2)
pm2 start pm2.config.js --env production

# Save PM2 process list (survives reboot)
pm2 save

# Setup PM2 startup script (for WSL2/systemd)
pm2 startup

# Useful PM2 commands
pm2 logs vanguard-paperclip     # View logs
pm2 restart vanguard-paperclip # Restart
pm2 stop vanguard-paperclip     # Stop
pm2 status                     # List all
```

---

## 6. API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Paperclip status |
| GET | `/health` | Full health + agent status |
| POST | `/jobs` | Enqueue new job |
| GET | `/jobs` | List jobs (query: `?status=pending`) |
| GET | `/jobs/:id` | Get job details |
| PATCH | `/jobs/:id` | Update job |
| DELETE | `/jobs/:id` | Cancel pending job |
| POST | `/agents` | Register agent |
| GET | `/agents` | List agents |
| GET | `/agents/:name` | Get agent |
| PATCH | `/agents/:name` | Update agent heartbeat |
| POST | `/commands` | Dispatch command |

---

## 7. Dependencies & Versions

| Package | Version | Purpose |
|---------|---------|---------|
| express | ^4.18.2 | HTTP server |
| cors | ^2.8.5 | Cross-origin support |
| dotenv | ^16.4.5 | Environment variables |
| node-cron | ^3.0.3 | Cron scheduling |
| uuid | ^9.0.0 | Job IDs |
| axios | ^1.6.7 | HTTP client (for agent communication) |

---

## 8. Phase 3.1 Completion Criteria

- [x] Paperclip starts on port 3100
- [x] `GET /health` returns 200 with agent/queue status
- [x] Jobs can be created, listed, and cancelled via API
- [x] Agents can register and send heartbeats
- [x] Cron scheduler fires morning briefing placeholder
- [x] PM2 daemon survives terminal close
- [x] Logs written to `~/friday-gateway/paperclip-logs/`
- [x] Unit tests pass (`npm test`)

> **Implemented by:** Friday — 2026-04-08
> **Implementation notes:** Paperclip backend fully built and running via PM2. All routes functional. Vanguard's team formally hired: ATLAS, FORGE, SENTINEL registered on Paperclip. systemd service also configured for boot persistence.

---

## 9. Next Phase Preview

**Phase 3.2** (Forge's work):
- Paperclip PM2 hardening
- Auto-restart on crash
- Systemd integration for boot persistence

**Phase 3.5** (Vanguard delegation):
- Connect Friday → Vanguard command chain
- Agent job dispatch (Atlas, Forge, Sentinel)
- Result collection and escalation

---

> _Blueprint locked. Implementation begins when CJ gives the word._
> _— Friday, 2026-04-07_
