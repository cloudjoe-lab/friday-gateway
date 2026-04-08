// Cron-like job scheduler service
import cron from 'node-cron';
import { jobQueue } from './queue.js';
import { config } from '../config/index.js';

export class Scheduler {
  constructor() {
    this.tasks = new Map();
    this.logger = console;
  }

  log(level, ...args) {
    const ts = new Date().toISOString().slice(11, 19);
    this.logger[level](`[SCHEDULER ${ts}]`, ...args);
  }

  addTask(name, cronExpr, handler) {
    if (this.tasks.has(name)) {
      this.log('warn', `Task '${name}' already exists — replacing.`);
      this.tasks.get(name).stop();
    }
    const task = cron.schedule(cronExpr, async () => {
      this.log('info', `Firing scheduled task: ${name}`);
      try {
        const job = jobQueue.enqueue({
          type: `scheduled.${name}`,
          payload: { task: name, firedAt: new Date().toISOString() },
        });
        await handler(job);
      } catch (err) {
        this.log('error', `Scheduled task '${name}' failed:`, err.message);
      }
    });
    this.tasks.set(name, { task, cronExpr, handler });
    this.log('info', `Scheduled task registered: ${name} (${cronExpr})`);
    return task;
  }

  removeTask(name) {
    const entry = this.tasks.get(name);
    if (!entry) return false;
    entry.task.stop();
    this.tasks.delete(name);
    this.log('info', `Scheduled task removed: ${name}`);
    return true;
  }

  listTasks() {
    return Array.from(this.tasks.entries()).map(([name, { cronExpr }]) => ({
      name,
      cron: cronExpr,
    }));
  }

  stopAll() {
    for (const [name, entry] of this.tasks) {
      entry.task.stop();
    }
    this.log('info', 'All scheduled tasks stopped.');
  }
}

export const scheduler = new Scheduler();

// ─── Built-in morning briefing placeholder ────────────────────────────────
scheduler.addTask('morning-briefing', '0 8 * * *', async (job) => {
  // Phase 3.5: Connect to Friday gateway for briefing dispatch
  console.log('[SCHEDULER] Morning briefing fired — stub (Phase 3.5 will wire to Friday)');
});
