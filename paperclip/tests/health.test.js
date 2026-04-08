// Basic health endpoint test
import { test } from 'node:test';
import assert from 'node:assert';

test('GET /health returns 200', async () => {
  const res = await fetch('http://localhost:3100/health');
  assert.strictEqual(res.status, 200);
  const body = await res.json();
  assert.strictEqual(body.status, 'ok');
  assert.strictEqual(body.service, 'vanguard-paperclip');
  assert.ok(Array.isArray(body.agents));
  assert.ok(typeof body.queue === 'object');
});

test('GET / returns paperclip info', async () => {
  const res = await fetch('http://localhost:3100/');
  assert.strictEqual(res.status, 200);
  const body = await res.json();
  assert.strictEqual(body.service, 'vanguard-paperclip');
});
