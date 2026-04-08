// Vanguard Paperclip — Entry Point
// The throne that powers Vanguard's agent orchestration
import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import 'express-async-errors';

import { config } from './config/index.js';
import healthRouter from './routes/health.js';
import jobsRouter from './routes/jobs.js';
import agentsRouter from './routes/agents.js';
import commandsRouter from './routes/commands.js';
import { scheduler } from './services/scheduler.js';
import { heartbeatMonitor } from './services/heartbeat.js';

// ─── App Setup ────────────────────────────────────────────────────────────

const app = express();

app.use(cors());
app.use(express.json());

// Request logger
app.use((req, res, next) => {
  const ts = new Date().toISOString().slice(11, 19);
  console.log(`[${ts}] ${req.method} ${req.path}`);
  next();
});

// ─── Routes ─────────────────────────────────────────────────────────────

app.use('/health', healthRouter);
app.use('/jobs', jobsRouter);
app.use('/agents', agentsRouter);
app.use('/commands', commandsRouter);

// ─── Paperclip Status ────────────────────────────────────────────────────

app.get('/', (req, res) => {
  res.json({
    service: 'vanguard-paperclip',
    version: '0.1.0',
    status: 'operational',
    timestamp: new Date().toISOString(),
    paperclipUrl: config.paperclipUrl,
    endpoints: [
      'GET  /health     — Full health + agent + queue status',
      'POST /jobs       — Enqueue job',
      'GET  /jobs       — List jobs',
      'GET  /jobs/:id   — Get job',
      'PATCH /jobs/:id  — Update job',
      'DELETE /jobs/:id — Cancel job',
      'POST /agents     — Register agent',
      'GET  /agents     — List agents',
      'GET  /agents/:name — Get agent',
      'PATCH /agents/:name — Heartbeat',
      'DELETE /agents/:name — Unregister',
      'POST /commands   — Dispatch command',
      'GET  /commands/types — Available commands',
    ],
  });
});

// ─── Global Error Handler ───────────────────────────────────────────────

app.use((err, req, res, next) => {
  console.error('[ERROR]', err.stack || err.message);
  res.status(500).json({ success: false, error: err.message || 'Internal Server Error' });
});

// ─── Start ──────────────────────────────────────────────────────────────

// Start heartbeat monitor
heartbeatMonitor.startPeriodicCheck(30000);

// Start scheduler (morning briefing etc.)
console.log('[PAPERCLIP] Scheduled tasks:', scheduler.listTasks().map(t => t.name).join(', ') || 'none');

const server = app.listen(config.port, config.host, () => {
  console.log('╔══════════════════════════════════════════════╗');
  console.log('║     VANGUARD PAPERCUP — ONLINE              ║');
  console.log(`║     Port: ${config.port}  |  Env: ${config.env.padEnd(10)} |  Host: ${config.host}  ║`);
  console.log('╚══════════════════════════════════════════════╝');
  console.log(`[PAPERCLIP] Vault logs: ${config.logDir}/vault.log`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('[PAPERCLIP] SIGTERM — shutting down...');
  scheduler.stopAll();
  heartbeatMonitor.stop();
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  console.log('[PAPERCLIP] SIGINT — shutting down...');
  scheduler.stopAll();
  heartbeatMonitor.stop();
  server.close(() => process.exit(0));
});
