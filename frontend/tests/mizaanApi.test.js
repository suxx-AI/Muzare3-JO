import test from 'node:test';
import assert from 'node:assert/strict';
import { sendMessage } from '../src/api/mizaanApi.js';

test('adapter sends the documented request and accepts a null dashboard', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8000/chat');
    assert.equal(options.method, 'POST');
    assert.deepEqual(JSON.parse(options.body), { message: 'مرحبا', session_id: 'demo-user' });
    return { ok: true, json: async () => ({ answer: 'أهلاً', dashboard: null }) };
  });
  assert.deepEqual(await sendMessage('مرحبا'), { answer: 'أهلاً', dashboard: null });
});

test('adapter exposes API errors and handles invalid replies', async (t) => {
  const mock = t.mock.method(globalThis, 'fetch', async () => ({ ok: false, json: async () => ({ detail: 'تعذر الحصول على رد' }) }));
  await assert.rejects(sendMessage('مرحبا'), /تعذر الحصول/);
  mock.mock.mockImplementation(async () => ({ ok: true, json: async () => ({}) }));
  await assert.rejects(sendMessage('مرحبا'), /إجابة نصية/);
  mock.mock.mockImplementation(async () => { throw new Error('offline'); });
  await assert.rejects(sendMessage('مرحبا'), /تعذر الاتصال/);
});
