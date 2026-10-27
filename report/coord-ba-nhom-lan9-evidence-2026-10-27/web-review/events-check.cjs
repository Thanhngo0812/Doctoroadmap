const fs = require('node:fs/promises');
const cp = require('node:child_process');
const util = require('node:util');
const crypto = require('node:crypto');
const run = util.promisify(cp.execFile);
const front = __dirname + '/frontend';
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
async function check(label) {
  const args = ['C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w16-usage-react/src/web/frontend/node_modules/vitest/vitest.mjs', 'run', 'src/Assistant.events-independent.test.tsx', '--config', front + '/vite.config.mjs', '--configLoader', 'native', '--reporter=junit', '--outputFile=' + __dirname + '/' + label + '.xml'];
  let code = 0, stdout = '', stderr = ''; const start = Date.now();
  try { ({ stdout, stderr } = await run(process.execPath, args, { cwd: front, windowsHide: true, maxBuffer: 12e6 })); }
  catch (cause) { code = cause.code; stdout = cause.stdout || ''; stderr = cause.stderr || ''; }
  await fs.writeFile(__dirname + '/' + label + '.log', stdout + '\n' + stderr);
  await fs.writeFile(__dirname + '/' + label + '.json', JSON.stringify({ label, code, args, cwd: front, elapsedMS: Date.now() - start }, null, 2) + '\n');
  console.log(JSON.stringify({ label, code })); return code;
}
async function main() {
  const source = await fs.readFile(front + '/src/Assistant.final-usage-race.test.tsx', 'utf8');
  const imports = source.slice(0, source.indexOf("it('review:"));
  const helper = source.slice(source.indexOf('async function conversationWithDelayedUsage()'), source.indexOf("it.each(['success'"));
  const test = `
it('independent: only the current usage callback emits a payload-free refresh event', async () => {
  const c = await conversationWithDelayedUsage();
  const events: Event[] = []; const record = (event: Event) => events.push(event);
  window.addEventListener('wayfinder:usage-changed', record);
  try {
    await c.send('First');
    await act(async () => { c.final(0); c.streams[0].close(); });
    await waitFor(() => expect(c.usage).toHaveLength(1));
    await c.send('Second');
    await act(async () => { c.final(1); c.streams[1].close(); });
    await waitFor(() => expect(c.usage).toHaveLength(2));
    await act(async () => c.usage[1].resolve(json({ learner_today: { used_ratio: .8, limited: false } })));
    expect(screen.getByText(/80%/)).toBeVisible(); expect(events).toHaveLength(1);
    expect(events[0]).toBeInstanceOf(Event); expect(events[0]).not.toHaveProperty('detail');
    await act(async () => c.usage[0].resolve(json({ learner_today: { used_ratio: .2, limited: false } })));
    expect(screen.getByText(/80%/)).toBeVisible(); expect(events).toHaveLength(1);
    expect(screen.getByRole('textbox', { name: 'Câu hỏi' })).toBeEnabled();
  } finally { window.removeEventListener('wayfinder:usage-changed', record); }
});
`;
  await fs.writeFile(front + '/src/Assistant.events-independent.test.tsx', imports + helper + test);
  if (await check('events-baseline') !== 0) throw Error('event baseline failed');
  const target = front + '/src/useAssistant.ts', original = await fs.readFile(target);
  const from = 'if (!controller.signal.aborted && active.current === request) { setUsage(amount); notifyUsageChanged(); }';
  const to = 'if (!controller.signal.aborted && active.current === request) setUsage(amount); notifyUsageChanged();';
  const changed = original.toString().replace(from, to);
  if (changed === original.toString()) throw Error('event mutation missing');
  let code;
  try { await fs.writeFile(target, changed); code = await check('events-stale-mutant'); }
  finally { await fs.writeFile(target, original); }
  const restored = await fs.readFile(target);
  await fs.writeFile(__dirname + '/events-mutation-proof.json', JSON.stringify({ mutantCode: code, sourceSha256: hash(original), mutatedSha256: hash(Buffer.from(changed)), restoredSha256: hash(restored), independentProbeSha256: hash(Buffer.from(imports + helper + test)), helperProvenance: 'Copied author HTTP/SSE conversation fixture only; added event-count/payload assertions independently.' }, null, 2) + '\n');
  if (code === 0) throw Error('event mutant survived');
  if (await check('events-restored') !== 0) throw Error('event restore failed');
}
main().catch(cause => { console.error(cause); process.exitCode = 1; });
