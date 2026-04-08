// GET /health — Full health + agent status
import { Router } from 'express';
import { config } from '../config/index.js';
import { jobQueue } from '../services/queue.js';
import { heartbeatMonitor } from '../services/heartbeat.js';
import { scheduler } from '../services/scheduler.js';

const router = Router();

router.get('/', (req, res) => {
  const agentHealth = heartbeatMonitor.checkHealth();
  const queueStats = jobQueue.stats();
  const tasks = scheduler.listTasks();

  res.json({
    status: 'ok',
    service: 'vanguard-paperclip',
    version: '0.1.0',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    env: config.env,
    paperclip: {
      url: config.paperclipUrl,
      port: config.port,
      host: config.host,
    },
    queue: queueStats,
    agents: agentHealth,
    scheduledTasks: tasks,
  });
});

export default router;
