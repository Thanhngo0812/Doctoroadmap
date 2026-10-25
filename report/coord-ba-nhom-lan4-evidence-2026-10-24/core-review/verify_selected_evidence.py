"""Check selected committed W15 evidence; no DB or provider access."""
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build')
EVIDENCE = ROOT / 'report/w15-evidence'
manifest = json.loads((EVIDENCE / 'operator-20261024/manifest.json').read_text(encoding='utf-8'))
entries = {row['path']: row for row in manifest['files']}
selected = [
    'runs/operator-full-20261024-01-exit.json',
    'runs/operator-full-20261024-01.xml',
    'runs/operator-approved-scope-20261024-03-exit.json',
    'runs/operator-approved-scope-20261024-03.xml',
    'runs/approved-mutations-final-20261024-01-exit.json',
    'mutations/approved-final-20261024-01/mutations.json',
    'sql/operator-approved-scope-20261024-03/postport-success-False.json',
    'sql/operator-approved-scope-20261024-03/doc6-real-web-cache-only.json',
    'sql/operator-approved-scope-20261024-03/real-dry-run-doc-6.json',
    'sql/operator-approved-scope-20261024-03/real-dry-run-candidate.json',
]
for relative in selected:
    data = (EVIDENCE / relative).read_bytes()
    row = entries[relative]
    assert len(data) == row['bytes'] and sha256(data).hexdigest() == row['sha256'], relative

full_native = json.loads((EVIDENCE / selected[0]).read_text(encoding='utf-8'))
assert full_native['exit_code'] == 0
assert full_native['commit'] == 'ffd070d7c22688ef1ce00558fae2858f62752aad'
for relative, expected in full_native['source_sha256'].items():
    assert sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative

junit = {}
for label, relative in [('full', selected[1]), ('scope', selected[3])]:
    cases = list(ET.parse(EVIDENCE / relative).getroot().iter('testcase'))
    junit[label] = dict(total=len(cases), failures=sum(case.find('failure') is not None for case in cases),
                        errors=sum(case.find('error') is not None for case in cases),
                        skipped=sum(case.find('skipped') is not None for case in cases))
assert junit['full'] == dict(total=2536, failures=0, errors=0, skipped=2)
assert junit['scope'] == dict(total=76, failures=0, errors=0, skipped=0)
mutations = json.loads((EVIDENCE / selected[5]).read_text(encoding='utf-8'))
assert len(mutations) == 29
assert all(row['exit_code'] == 1 and row['assertion_failures'] > 0 and row['setup_errors'] == 0
           and row['source_restored'] is True for row in mutations)

success = json.loads((EVIDENCE / selected[6]).read_text(encoding='utf-8'))
assert success['synthetic_usage'] is True and success['provider_calls'] == 0
assert success['receipt']['status'] == 'succeeded'
assert all(Decimal(str(row['cost_usd'])) == row['input_tokens'] == row['output_tokens'] == 0
           for row in success['traces'])
assert sum(Decimal(str(row['cost_usd'])) for row in success['ledger']) == Decimal(str(success['build']['spent_usd']))
doc6 = json.loads((EVIDENCE / selected[7]).read_text(encoding='utf-8'))
assert doc6['provider_calls'] == 0 and doc6['ready_at_zero_cost_proven'] is False
assert doc6['build']['status'] == 'failed'
assert doc6['receipt_before_web_error_mapping']['error']['error_type'] == 'SpendNotAllowed'
for relative in selected[8:]:
    dry = json.loads((EVIDENCE / relative).read_text(encoding='utf-8'))
    assert dry['provider_calls'] == 0 and dry['queued'] is False and dry['collector_receipts'] == 1
    assert dry['result']['status'] == 'dry_run' and all(value == 0 for value in dry['sql_counts'].values())

print(json.dumps({'selected_manifest_entries_verified': len(selected), 'current_source_hashes_verified': len(full_native['source_sha256']),
                  'junit': junit, 'recorded_assertion_kills': len(mutations), 'synthetic_ledger_single_count': True,
                  'doc6_cache_miss_not_free_success': True, 'dry_runs_no_queue_or_provider': True,
                  'provider_calls_by_review': 0, 'database_connections_by_review': 0}, indent=2))
