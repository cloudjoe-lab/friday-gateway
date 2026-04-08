// Agent heartbeat monitor service
import { config } from '../config/index.js';

export class HeartbeatMonitor {
  constructor() {
    this.agents = new Map();
    this.logger = console;
    this.interval = null;
    this.timeoutSecs = 60; // Agent considered dead after 60s no heartbeat
  }

  log(level, ...args) {
    const ts = new Date().toISOString().slice(11, 19);
    this.logger[level](`[HEARTBEAT ${ts}]`, ...args);
  }

  register(name, url, type = 'generic') {
    const now = new Date().toISOString();
    this.agents.set(name, {
      name,
      url,
      type,
      status: 'alive',
      lastHeartbeat: now,
      registeredAt: now,
    });
    this.log('info', `Agent registered: ${name} (${type}) at ${url}`);
    return this.agents.get(name);
  }

  heartbeat(name, agentStatus = 'alive') {
    const agent = this.agents.get(name);
    if (!agent) {
      this.log('warn', `Heartbeat from unknown agent: ${name}`);
      return null;
    }
    agent.lastHeartbeat = new Date().toISOString();
    agent.status = agentStatus;
    return agent;
  }

  unregister(name) {
    const agent = this.agents.get(name);
    if (agent) {
      this.agents.delete(name);
      this.log('info', `Agent unregistered: ${name}`);
    }
    return agent;
  }

  list() {
    return Array.from(this.agents.values()).map(a => ({
      name: a.name,
      type: a.type,
      url: a.url,
      status: a.status,
      lastHeartbeat: a.lastHeartbeat,
      registeredAt: a.registeredAt,
      ageSecs: Math.floor((Date.now() - new Date(a.registeredAt).getTime()) / 1000),
    }));
  }

  get(name) {
    return this.agents.get(name) || null;
  }

  checkHealth() {
    const now = Date.now();
    const results = [];
    for (const [name, agent] of this.agents) {
      const lastTs = new Date(agent.lastHeartbeat).getTime();
      const elapsed = (now - lastTs) / 1000;
      if (elapsed > this.timeoutSecs) {
        agent.status = 'stale';
        this.log('warn', `Agent stale: ${name} (${elapsed.toFixed(0)}s since last heartbeat)`);
      } else {
        agent.status = 'alive';
      }
      results.push({ name, status: agent.status, elapsedSecs: Math.floor(elapsed) });
    }
    return results;
  }

  startPeriodicCheck(intervalMs = 30000) {
    this.interval = setInterval(() => this.checkHealth(), intervalMs);
    this.log('info', `Periodic health check started (every ${intervalMs / 1000}s)`);
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
      this.log('info', 'Periodic health check stopped.');
    }
  }
}

export const heartbeatMonitor = new HeartbeatMonitor();
