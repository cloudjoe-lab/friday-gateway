// Vault-backed logging service
// Logs are appended to ~/friday-gateway/paperclip-logs/vault.log
import { createWriteStream, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { config } from '../config/index.js';

const logDir = config.logDir;
if (!existsSync(logDir)) {
  mkdirSync(logDir, { recursive: true });
}

const vaultLogPath = join(logDir, 'vault.log');
const vaultStream = createWriteStream(vaultLogPath, { flags: 'a' });

export class VaultLogger {
  constructor(service) {
    this.service = service;
  }

  _format(level, ...args) {
    const ts = new Date().toISOString();
    const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
    return `[${ts}] [${this.service}] [${level}] ${msg}\n`;
  }

  info(...args) {
    const line = this._format('INFO', ...args);
    vaultStream.write(line);
    console.log(line.trim());
  }

  error(...args) {
    const line = this._format('ERROR', ...args);
    vaultStream.write(line);
    console.error(line.trim());
  }

  warn(...args) {
    const line = this._format('WARN', ...args);
    vaultStream.write(line);
    console.warn(line.trim());
  }

  debug(...args) {
    if (config.env === 'development') {
      const line = this._format('DEBUG', ...args);
      vaultStream.write(line);
      console.debug(line.trim());
    }
  }
}

export function createLogger(service) {
  return new VaultLogger(service);
}
