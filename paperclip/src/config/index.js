import 'dotenv/config';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export const config = {
  port: parseInt(process.env.PAPERCLIP_PORT || '3100', 10),
  host: process.env.PAPERCLIP_HOST || '0.0.0.0',
  env: process.env.NODE_ENV || 'development',
  fridayUrl: process.env.FRIDAY_URL || 'http://localhost:3000',
  logLevel: process.env.LOG_LEVEL || 'info',
  logDir: join(process.env.HOME || '/home/krsna', 'friday-gateway', 'paperclip-logs'),
  paperclipUrl: `http://localhost:${process.env.PAPERCLIP_PORT || '3100'}`,
};
