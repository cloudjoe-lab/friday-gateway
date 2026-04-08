// Job queue CRUD routes
import { Router } from 'express';
import { jobQueue } from '../services/queue.js';
import { ok, created, error } from '../utils/response.js';

const router = Router();

// POST /jobs — Enqueue a new job
router.post('/', (req, res) => {
  const { type, payload, priority, scheduledAt } = req.body;
  if (!type) return error(res, 'Missing required field: type', 400);

  const job = jobQueue.enqueue({ type, payload: payload || {}, priority, scheduledAt });
  created(res, job);
});

// GET /jobs — List jobs
router.get('/', (req, res) => {
  const { status, limit } = req.query;
  const jobs = jobQueue.list({ status, limit: parseInt(limit) || 100 });
  ok(res, { jobs, count: jobs.length });
});

// GET /jobs/:id — Get job details
router.get('/:id', (req, res) => {
  const job = jobQueue.get(req.params.id);
  if (!job) return error(res, 'Job not found', 404);
  ok(res, job);
});

// PATCH /jobs/:id — Update job (start, complete, fail)
router.patch('/:id', (req, res) => {
  const job = jobQueue.update(req.params.id, req.body);
  if (!job) return error(res, 'Job not found', 404);
  ok(res, job);
});

// DELETE /jobs/:id — Cancel pending job
router.delete('/:id', (req, res) => {
  const job = jobQueue.cancel(req.params.id);
  if (!job) return error(res, 'Job not found or cannot be cancelled', 400);
  ok(res, { cancelled: true, job });
});

export default router;
