"""Run named foundation assertions against intentionally broken in-memory variants."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


TEST = 'tests/unit/application/test_phase_b2_foundation.py'
CASES = {
    'saved_module_id': ('test_scope_anchor_survives_split_and_stale_and_ties', '''
from doc2roadmap.domain import scope
scope.resolve_scope = lambda saved, graph, *a, **k: {'module_id': saved.get('module_id_at_creation'), 'stale': False, 'jaccard': 1.0}
'''),
    'delete_noop': ('test_store_delete_and_document_filter_contract', '''
from doc2roadmap.infrastructure.artifacts.phase_b_store import _PhaseBStore
_PhaseBStore.delete_record = lambda *a: None
'''),
    'ignore_doc_filter': ('test_store_delete_and_document_filter_contract', '''
from doc2roadmap.infrastructure.artifacts.phase_b_store import _PhaseBStore
original = _PhaseBStore.list_records
_PhaseBStore.list_records = lambda self, kind, owner=None, doc_id=None: original(self, kind, owner)
'''),
    'quiz_overwrites_learner': ('test_progress_manual_choice_wins_and_remaps_modules', '''
from doc2roadmap.application.phase_b.progress import ProgressUseCase
original = ProgressUseCase.mark_quiz_correct
def wrong(self, owner, doc_id, node_ids):
    for node_id in node_ids:
        self.store.delete_record('progress', self._key(owner, doc_id, node_id))
    return original(self, owner, doc_id, node_ids)
ProgressUseCase.mark_quiz_correct = wrong
'''),
    'daily_guard_disabled': ('test_daily_cap_owner_timezone_and_settings', '''
from doc2roadmap.application.phase_b.budget import DailySpendGuard
DailySpendGuard.check = lambda *a, **k: True
'''),
    'unowned_ledger_allowed': ('test_ledger_rejects_unowned_rows_before_persist', '''
from doc2roadmap.infrastructure.artifacts.phase_b_store import _PhaseBStore
_PhaseBStore.append_usage = lambda self, row: self._usage.append(dict(row))
'''),
    'common_guard_disabled': ('test_common_blocks_before_model_and_uses_injected_clock', '''
from doc2roadmap.application.phase_b.budget import DailySpendGuard
DailySpendGuard.check = lambda *a, **k: True
'''),
}


def main():
    Path('tmp/b2-mutants').mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (assertion, mutation) in CASES.items():
        target = TEST + '::' + assertion
        run = subprocess.run([sys.executable, '-c', mutation + '\nimport pytest\nraise SystemExit(pytest.main(' +
                              repr([target, '-q', '--basetemp', 'tmp/b2-mutants/' + name, '-p', 'no:cacheprovider']) + '))'],
                             text=True, capture_output=True)
        killed = run.returncode == 1 and 'FAILED' in run.stdout
        rows.append({'mutation': name, 'assertion': target, 'exit_code': run.returncode, 'killed': killed})
        if not killed:
            print(run.stdout[-2500:], run.stderr[-1000:])
    output = Path('tmp/phaseb-b2-foundation-mutations.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'mutants': len(rows), 'killed': sum(r['killed'] for r in rows), 'output': str(output)}))
    return 0 if all(r['killed'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
