"""Selected committed evidence checks only; no DB, provider or source mutations."""
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build')
EVIDENCE = ROOT / 'report/w15-evidence'
manifest = json.loads((EVIDENCE / 'r4-20261025/manifest.json').read_text(encoding='utf-8'))
entries = {row['path']: row for row in manifest['files']}
labels = ['r4-plan-red-20261025-01', 'r4-plan-green-20261025-01', 'r4-demo-red-20261025-01',
          'r4-demo-green-20261025-01', 'r4-full-20261025-02', 'r4-react-20261025-02', 'r4-build-20261025-02']
selected = [p for p in entries if p.startswith('runs/') and any(p == 'runs/' + label + ending for label in labels for ending in ['.xml', '-exit.json'])]
selected += ['mutations/r4-demo-20261025/mutations.json']
selected += ['mutations/r4-demo-20261025/' + label + '.xml' for label in ['portable-plan', 'unverified-embedding', 'unverified-grant', 'billing-basis']]
selected += ['sql/r4-full-20261025-02/' + name + '.json' for name in ['postport-success-False', 'doc6-real-web-cache-only', 'real-dry-run-doc-6', 'real-dry-run-candidate']]
for relative in selected:
    data = (EVIDENCE / relative).read_bytes()
    row = entries[relative]
    assert len(data) == row['bytes'] and sha256(data).hexdigest() == row['sha256'], relative
native = json.loads((EVIDENCE / 'runs/r4-full-20261025-02-exit.json').read_text(encoding='utf-8'))
assert native['commit'] == 'cfabaeb51a7212b9684eaef711fb568ac81673bc' and native['exit_code'] == 0
for relative, digest in native['source_sha256'].items():
    assert sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
counts = {}
for label in labels:
    if 'build' in label:
        continue
    cases = list(ET.parse(EVIDENCE / ('runs/' + label + '.xml')).getroot().iter('testcase'))
    counts[label] = {'tests': len(cases), 'failure': sum(case.find('failure') is not None for case in cases),
                     'error': sum(case.find('error') is not None for case in cases),
                     'skip': sum(case.find('skipped') is not None for case in cases)}
assert counts['r4-plan-red-20261025-01'] == dict(tests=1, failure=1, error=0, skip=0)
assert counts['r4-plan-green-20261025-01'] == dict(tests=1, failure=0, error=0, skip=0)
assert counts['r4-demo-red-20261025-01'] == dict(tests=2, failure=2, error=0, skip=0)
assert counts['r4-demo-green-20261025-01'] == dict(tests=39, failure=0, error=0, skip=0)
assert counts['r4-full-20261025-02'] == dict(tests=2643, failure=0, error=0, skip=2)
assert counts['r4-react-20261025-02'] == dict(tests=181, failure=0, error=0, skip=0)
mutations = json.loads((EVIDENCE / 'mutations/r4-demo-20261025/mutations.json').read_text(encoding='utf-8'))
assert len(mutations) == 4 and all(row['native_exit'] == 1 and row['assertion_failures'] > 0 and row['setup_errors'] == 0 and row['source_restored'] for row in mutations)
success = json.loads((EVIDENCE / 'sql/r4-full-20261025-02/postport-success-False.json').read_text(encoding='utf-8'))
assert success['provider_calls'] == 0 and success['synthetic_usage'] is True
assert all(Decimal(str(row['cost_usd'])) == row['input_tokens'] == row['output_tokens'] == 0 for row in success['traces'])
assert sum(Decimal(str(row['cost_usd'])) for row in success['ledger']) == Decimal(str(success['build']['spent_usd']))
for book in ['doc-6', 'candidate']:
    dry = json.loads((EVIDENCE / ('sql/r4-full-20261025-02/real-dry-run-' + book + '.json')).read_text(encoding='utf-8'))
    assert dry['provider_calls'] == 0 and dry['queued'] is False and dry['collector_receipts'] == 1
    assert all(value == 0 for value in dry['sql_counts'].values())
doc6 = json.loads((EVIDENCE / 'sql/r4-full-20261025-02/doc6-real-web-cache-only.json').read_text(encoding='utf-8'))
assert doc6['provider_calls'] == 0 and doc6['ready_at_zero_cost_proven'] is False and doc6['build']['status'] == 'failed'
request = json.loads((ROOT / 'tmp/w15-r4-approval-request.json').read_text(encoding='utf-8'))
assert request['owner_paid_approval_received'] is request['paid_run_executed'] is False
for attempt in request['attempts']:
    plan_bytes = (ROOT / attempt['plan']).read_bytes()
    assert sha256(plan_bytes).hexdigest() == attempt['plan_sha256']
    plan = json.loads(plan_bytes)
    assert plan['approved'] is False and plan['embedding_billing_verified'] is False and '\\' not in plan['run_dir']
    assert plan['prepared_commit'] == 'fb0c769ad146d1aa6a5b2b2e1648a12a359ad194'
    for key in ['file_sha256', 'pipeline_version', 'database', 'embedding_price_profile']:
        assert plan[key] == attempt[key]
print(json.dumps({'selected_manifest_entries': len(selected), 'current_source_sha_matches_full_native': len(native['source_sha256']),
                  'junit': counts, 'recorded_mutation_assertion_kills': len(mutations),
                  'synthetic_trace_not_double_billed': True, 'doc6_not_claimed_ready': True,
                  'local_plan_sha_verified': 2, 'owner_exact_run_paid_approval': False,
                  'database_connections': 0, 'provider_calls': 0}, indent=2))
