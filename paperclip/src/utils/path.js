// Path utility — respects HERMES_HOME for profile support
import { env } from 'process';

export function getHermesHome() {
  return env.HERMES_HOME || env.HOME + '/.hermes';
}
