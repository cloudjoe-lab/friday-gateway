// Command dispatch routes
import { Router } from 'express';
import { jobQueue } from '../services/queue.js';
import { heartbeatMonitor } from '../services/heartbeat.js';
import { ok, error } from '../utils/response.js';
import axios from 'axios';

const router = Router();

// POST /commands — Dispatch command to an agent
router.post('/', async (req, res) => {
  const { target, command, payload, waitForResult = false } = req.body;
  if (!target || !command) {
    return error(res, 'Missing required fields: target, command', 400);
  }

  // Find target agent
  const agent = heartbeatMonitor.get(target);
  if (!agent) {
    return error(res, `Agent '${target}' not found or not registered`, 404);
  }

  // Enqueue job for this command
  const job = jobQueue.enqueue({
    type: `command.${command}`,
    payload: { target, command, payload },
    priority: payload?.priority || 'normal',
  });

  // Dispatch to agent if reachable
  let result = null;
  let dispatchOk = false;
  try {
    const response = await axios.post(`${agent.url}/commands`, {
      command,
      payload,
      jobId: job.id,
    }, { timeout: 10000 });
    result = response.data;
    dispatchOk = true;
  } catch (err) {
    result = { dispatch_error: err.message, agent_reachable: false };
  }

  // Mark job as dispatched
  jobQueue.update(job.id, { status: dispatchOk ? 'dispatched' : 'dispatch_failed', result });

  ok(res, {
    job,
    dispatched: dispatchOk,
    result,
  });
});

// GET /commands/types — List available command types
router.get('/types', (req, res) => {
  ok(res, {
    commands: [
      'healthcheck',
      'status',
      'vault_index',
      'vault_sync',
      'gateway_restart',
      'gateway_health',
      'cron_trigger',
      'mqtt_publish',
      'surreal_query',
      'delegate_task',
    ],
  });
});

export default router;
