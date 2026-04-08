// In-memory job queue service
import { v4 as uuidv4 } from 'uuid';

export class JobQueue {
  constructor() {
    this.jobs = new Map();
  }

  enqueue({ type, payload, priority = 'normal', scheduledAt = null }) {
    const id = `job_${uuidv4().replace(/-/g, '').slice(0, 12)}`;
    const now = new Date().toISOString();
    const job = {
      id,
      type,
      payload,
      priority,
      status: scheduledAt ? 'scheduled' : 'pending',
      scheduledAt,
      createdAt: now,
      updatedAt: now,
      startedAt: null,
      completedAt: null,
      result: null,
      error: null,
    };
    this.jobs.set(id, job);
    return job;
  }

  get(id) {
    return this.jobs.get(id) || null;
  }

  list({ status = null, limit = 100 } = {}) {
    let jobs = Array.from(this.jobs.values());
    if (status) {
      jobs = jobs.filter(j => j.status === status);
    }
    return jobs
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      .slice(0, limit);
  }

  update(id, updates) {
    const job = this.jobs.get(id);
    if (!job) return null;
    const updated = { ...job, ...updates, updatedAt: new Date().toISOString() };
    this.jobs.set(id, updated);
    return updated;
  }

  complete(id, result) {
    return this.update(id, {
      status: 'completed',
      completedAt: new Date().toISOString(),
      result,
    });
  }

  fail(id, error) {
    return this.update(id, {
      status: 'failed',
      completedAt: new Date().toISOString(),
      error: String(error),
    });
  }

  start(id) {
    return this.update(id, {
      status: 'running',
      startedAt: new Date().toISOString(),
    });
  }

  cancel(id) {
    const job = this.jobs.get(id);
    if (!job) return null;
    if (job.status === 'running' || job.status === 'completed') {
      return null; // Cannot cancel running or completed jobs
    }
    return this.update(id, { status: 'cancelled' });
  }

  stats() {
    const jobs = Array.from(this.jobs.values());
    return {
      total: jobs.length,
      pending: jobs.filter(j => j.status === 'pending').length,
      running: jobs.filter(j => j.status === 'running').length,
      completed: jobs.filter(j => j.status === 'completed').length,
      failed: jobs.filter(j => j.status === 'failed').length,
      cancelled: jobs.filter(j => j.status === 'cancelled').length,
      scheduled: jobs.filter(j => j.status === 'scheduled').length,
    };
  }
}

export const jobQueue = new JobQueue();
