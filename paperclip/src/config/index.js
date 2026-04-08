import 'dotenv/config';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export const config = {
  // Port this Vanguard instance listens on
  port: parseInt(process.env.VANGUARD_PORT || '3009', 10),
  host: process.env.VANGUARD_HOST || '0.0.0.0',
  env: process.env.NODE_ENV || 'development',
  // Where to find the Paperclip server (the frontend/api)
  paperclipUrl: `http://localhost:${process.env.PAPERCLIP_PORT || '3100'}`,
  // Where to find Friday/Hermes core
  fridayUrl: process.env.FRIDAY_URL || 'http://localhost:3000',
  logLevel: process.env.LOG_LEVEL || 'info',
  logDir: join(process.env.HOME || '/home/krsna', 'friday-gateway', 'paperclip-logs'),
};
