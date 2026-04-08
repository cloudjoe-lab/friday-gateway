// Agent registry routes
import { Router } from 'express';
import { heartbeatMonitor } from '../services/heartbeat.js';
import { ok, created, error } from '../utils/response.js';

const router = Router();

// POST /agents — Register a new agent
router.post('/', (req, res) => {
  const { name, url, type } = req.body;
  if (!name || !url) return error(res, 'Missing required fields: name, url', 400);

  const existing = heartbeatMonitor.get(name);
  if (existing) {
    // Re-register with new URL
    const agent = heartbeatMonitor.register(name, url, type || existing.type);
    return ok(res, { reregistered: true, agent });
  }

  const agent = heartbeatMonitor.register(name, url, type || 'generic');
  created(res, { registered: true, agent });
});

// GET /agents — List all agents
router.get('/', (req, res) => {
  heartbeatMonitor.checkHealth(); // Refresh stale status
  const agents = heartbeatMonitor.list();
  ok(res, { agents, count: agents.length });
});

// GET /agents/:name — Get agent
router.get('/:name', (req, res) => {
  const agent = heartbeatMonitor.get(req.params.name);
  if (!agent) return error(res, 'Agent not found', 404);
  ok(res, agent);
});

// PATCH /agents/:name — Update agent heartbeat
router.patch('/:name', (req, res) => {
  const { status } = req.body;
  const agent = heartbeatMonitor.heartbeat(req.params.name, status);
  if (!agent) return error(res, 'Agent not found', 404);
  ok(res, { updated: true, agent });
});

// DELETE /agents/:name — Unregister agent
router.delete('/:name', (req, res) => {
  const agent = heartbeatMonitor.unregister(req.params.name);
  if (!agent) return error(res, 'Agent not found', 404);
  ok(res, { unregistered: true, name: req.params.name });
});

export default router;
