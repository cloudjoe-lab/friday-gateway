// Abstract base class for sub-agents
export class BaseAgent {
  constructor({ name, type, url }) {
    this.name = name;
    this.type = type;
    this.url = url;
    this.status = 'idle';
  }

  async ping() {
    try {
      const response = await fetch(`${this.url}/health`);
      this.status = response.ok ? 'alive' : 'unhealthy';
      return response.ok;
    } catch {
      this.status = 'unreachable';
      return false;
    }
  }

  async sendCommand(command, payload) {
    const response = await fetch(`${this.url}/commands`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, payload }),
    });
    return response.json();
  }

  describe() {
    return {
      name: this.name,
      type: this.type,
      url: this.url,
      status: this.status,
    };
  }
}
