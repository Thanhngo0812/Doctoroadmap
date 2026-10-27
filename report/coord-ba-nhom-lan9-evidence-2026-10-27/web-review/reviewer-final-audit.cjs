const fs = require('node:fs');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const path = require('node:path');
const root = 'C:/Users/ngoco/Desktop/Doctoroadmap';
const worker = root + '/tmp/w16-usage-react';
const delivery = '6ee153864522eb1510e3ec88dc5e9c52e1cfe2ca';
const tested = '012abea28a32272a91aaccfa54823037652af28a';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const git = args => cp.execFileSync('git', args, { cwd: root, windowsHide: true });
const diff = git(['diff', '--name-only', tested, delivery, '--', 'src', 'scripts']).toString().trim();
const copied = json(__dirname + '/copied-source.json');
const copiedBad = copied.filter(row => hash(fs.readFileSync(__dirname + '/frontend/' + row.path.replace('src/web/frontend/', ''))) !== row.sha256).map(row => row.path);
const evidence = json(worker + '/report/w16-react-evidence/files-sha256.json');
const evidenceBad = evidence.files.filter(row => hash(fs.readFileSync(worker + '/' + row.path)) !== row.sha256).map(row => row.path);
const gates = ['gate-python-repeat', 'gate-react-final', 'gate-build-final', 'browser-final-run'].map(name => {
  const receipt = json(worker + '/report/w16-react-evidence/' + name + '/exit.json');
  const refs = Object.keys(receipt.sourceSha256);
  return { name, receipt, refs };
});
for (const gate of gates) {
  const input = gate.refs.map(file => tested + ':' + file).join('\n') + '\n';
  const output = cp.execFileSync('git', ['cat-file', '--batch'], { cwd: root, input, maxBuffer: 32 * 1024 * 1024, windowsHide: true });
  let offset = 0;
  gate.bad = [];
  gate.crlfCheckouts = 0;
  for (const file of gate.refs) {
    const eol = output.indexOf(10, offset);
    const header = output.subarray(offset, eol).toString();
    const match = header.match(/^\S+ blob (\d+)$/);
    if (!match) throw Error('Unexpected git blob header for ' + file);
    const size = Number(match[1]);
    const bytes = output.subarray(eol + 1, eol + 1 + size);
    const checkedOut = fs.readFileSync(worker + '/' + file);
    if (hash(checkedOut) !== gate.receipt.sourceSha256[file]) gate.bad.push({ file, reason: 'raw receipt differs from worker bytes' });
    if (!bytes.equals(checkedOut)) {
      const canonical = buffer => Buffer.from(buffer.toString('utf8').replace(/\r\n/g, '\n'));
      if (!bytes.includes(0) && !checkedOut.includes(0) && canonical(bytes).equals(canonical(checkedOut))) gate.crlfCheckouts++;
      else gate.bad.push({ file, reason: 'checkout differs from tested Git blob beyond CRLF' });
    }
    offset = eol + 1 + size + 1;
  }
}
const xmls = ['usage-baseline', 'usage-restored', 'focus-baseline', 'focus-abort-mutant', 'focus-restored', 'max-null', 'limited-blocks-cache', 'timezone-local', 'events-baseline', 'events-stale-mutant', 'events-restored'];
const tests = Object.fromEntries(xmls.map(name => {
  const xml = fs.readFileSync(__dirname + '/' + name + '.xml', 'utf8');
  return [name, { native: json(__dirname + '/' + name + '.json').code, cases: (xml.match(/<testcase\b/g) || []).length, failures: (xml.match(/<failure\b/g) || []).length, errors: (xml.match(/<error\b/g) || []).length, skipped: (xml.match(/<skipped\b/g) || []).length }];
}));
const audit = { delivery, tested, mainPin: 'e52bf4f245e9e6c0454ee83760ea4bf8ad55adff', productChangesAfterTest: diff.split('\n').filter(Boolean), copiedSource: { files: copied.length, bad: copiedBad }, authorEvidence: { files: evidence.files.length, bad: evidenceBad }, gates: gates.map(g => ({ name: g.name, commit: g.receipt.commit, native: g.receipt.nativeExitCode, files: g.refs.length, crlfCheckouts: g.crlfCheckouts, bad: g.bad })), tests, mutations: json(__dirname + '/mutation-results.json'), focusMutation: json(__dirname + '/focus-mutation-proof.json'), eventMutation: json(__dirname + '/events-mutation-proof.json'), externalCostUsd: 0 };
fs.writeFileSync(__dirname + '/reviewer-final-audit.json', JSON.stringify(audit, null, 2) + '\n');
console.log(JSON.stringify(audit, null, 2));
if (diff || copiedBad.length || evidenceBad.length || gates.some(g => g.bad.length || g.receipt.nativeExitCode !== 0)) process.exitCode = 1;
