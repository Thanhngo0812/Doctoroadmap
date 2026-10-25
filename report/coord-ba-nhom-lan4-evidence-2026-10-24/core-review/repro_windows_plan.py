"""Read-only W15 plan/path counterexample. Never composes DB or providers."""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build')
spec = importlib.util.spec_from_file_location('review_file_paths', ROOT / 'src/web/backend/wayfinder/domain/file_paths.py')
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)

results = []
for filename in ('doc6-plan-at-ffd070d.json', 'candidate-plan-at-ffd070d.json'):
    plan_path = ROOT / 'report/w15-evidence/operator-20261024' / filename
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    stored = plan['run_dir']
    assert '\\' in stored, 'Counterexample must use the unmodified saved Windows plan'
    try:
        paths.safe_path(ROOT, stored)
    except ValueError as error:
        assert str(error) == 'Path escapes its root'
        observed = str(error)
    else:
        raise AssertionError('The unmodified Windows plan unexpectedly passed execute path validation')
    portable = paths.safe_path(ROOT, stored.replace('\\', '/'))
    assert portable.name.startswith('w15-operator-')
    results.append({'plan': filename, 'saved_run_dir': stored, 'actual_exception': observed,
                    'posix_control_passed': True})

print(json.dumps({'counterexample': 'prepare writes str(Path.relative_to), execute rejects its native Windows separators',
                  'provider_calls': 0, 'database_connections': 0, 'source_changes': 0,
                  'results': results}, ensure_ascii=False, indent=2))
