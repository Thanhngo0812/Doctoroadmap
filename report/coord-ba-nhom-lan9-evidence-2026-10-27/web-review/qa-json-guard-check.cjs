const assert = require('node:assert/strict');
const cp = require('node:child_process');
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = 'C:/Users/ngoco/Desktop/Doctoroadmap';
const commit = process.argv[2];
if (!commit) throw Error('Pass the commit to test');
const source = cp.execFileSync('git', ['show', commit + ':scripts/w16_web_check.cjs'], { cwd: root }).toString();
const before = cp.execFileSync('git', ['show', '2d36ed7b:scripts/w16_web_check.cjs'], { cwd: root }).toString();
const inspect = source.slice(source.indexOf('  function inspectPayload('), source.indexOf('  const browser = await'));
const binding = source.slice(source.indexOf("    await context.exposeBinding('__w16RecordJson'"), source.indexOf('    const streams = new Map();'));
const init = source.slice(source.indexOf('    await context.addInitScript('), source.indexOf('    const page = await context.newPage();'));
const finalAssertions = source.match(/assert\.deepEqual\(audit\.pendingRejections,\[\]\);assert\.deepEqual\(audit\.privacyFailures,\[\]\);/)[0];
const checkFinalAudit = new Function('audit', 'assert', finalAssertions);
const base = 'http://qa.invalid';
const url = base + '/api/v1/courses/c/documents/d';
async function candidate(label, body, readErrorName, signalAborted) {
  const audit = { http: [], privacyFailures: [] }, appCaught = [];
  const response = { url, body: {}, status: 200, headers: { get: () => 'application/json' }, clone: () => ({ text: async () => {
    if (readErrorName) { const error = new Error('Synthetic body read failure'); error.name = readErrorName; throw error; }
    return body;
  } }) };
  const window = { fetch: async () => response };
  const context = {
    exposeBinding: async (name, callback) => { window[name] = row => Promise.resolve().then(() => callback({}, row)); },
    addInitScript: async (callback, options) => callback(options),
  };
  await vm.runInNewContext('(async () => {' + inspect + binding + init + '})()', { context, window, audit, stage: 'probe', base, assert, URL, crypto, Response, ReadableStream, TextDecoder });
  try { await window.fetch(url, { method: 'GET', signal: { aborted: signalAborted } }); }
  catch (error) { appCaught.push({ name: error.name, message: error.message }); }
  const pendingRejections = [];
  audit.pendingRejections = pendingRejections;
  let finalAccepted = true;
  try { checkFinalAudit(audit, assert); }
  catch { finalAccepted = false; }
  return { label, finalAccepted, appCaught, http: audit.http, privacyFailures: audit.privacyFailures, pendingRejections };
}
async function previousReadFailure() {
  const pending = [], audit = { http: [] }; let onResponse;
  const handler = before.slice(before.indexOf("    page.on('response',"), before.indexOf('    return page;', before.indexOf("    page.on('response',")));
  const page = { on: (_, callback) => { onResponse = callback; } };
  vm.runInNewContext(inspect + handler, { page, audit, pending, stage: 'probe', base, assert, URL });
  onResponse({ url: () => url, headers: () => ({ 'content-type': 'application/json' }), text: async () => { throw new TypeError('Synthetic body read failure'); }, request: () => ({ method: () => 'GET', resourceType: () => 'fetch' }), status: () => 200 });
  return { pendingRejections: (await Promise.allSettled(pending)).filter(row => row.status === 'rejected').map(row => String(row.reason)) };
}
async function main() {
  const cases = [];
  cases.push(await candidate('safe JSON', '{"title":"safe"}', null, false));
  cases.push(await candidate('private JSON', '{"validation":"private"}', null, false));
  cases.push(await candidate('malformed JSON', '{broken', null, false));
  cases.push(await candidate('expected AbortError', null, 'AbortError', true));
  cases.push(await candidate('unexpected AbortError', null, 'AbortError', false));
  cases.push(await candidate('unexpected TypeError', null, 'TypeError', false));
  const old = await previousReadFailure();
  assert.equal(cases[0].finalAccepted, true);
  assert.equal(cases[1].finalAccepted, false);
  assert.equal(cases[2].finalAccepted, false);
  assert.equal(cases[3].finalAccepted, true);
  assert.equal(cases[4].appCaught.length, 1);
  assert.equal(cases[5].appCaught.length, 1);
  assert.equal(old.pendingRejections.length, 1);
  const result = { commit, sourceSha256: crypto.createHash('sha256').update(source).digest('hex'), extraction: 'Actual inspectPayload, __w16RecordJson binding, fetch wrapper and final audit assertions; fake fetch body only; application catches rejection as React does.', cases, previousReadFailure: old, unexpectedErrorsAcceptedByFinalAudit: cases.slice(4).every(row => row.finalAccepted), externalCostUsd: 0 };
  fs.writeFileSync(__dirname + '/qa-json-guard-' + commit.slice(0, 8) + '.json', JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
  assert.equal(cases[4].finalAccepted, false, 'unexpected AbortError must fail final audit even when the application catches it');
  assert.equal(cases[5].finalAccepted, false, 'unexpected TypeError must fail final audit even when the application catches it');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
