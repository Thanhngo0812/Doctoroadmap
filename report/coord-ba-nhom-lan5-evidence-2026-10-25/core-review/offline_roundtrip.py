"""Exercise real prepare JSON/path and execute validation offline; all composition is fake."""
from contextlib import nullcontext
from hashlib import sha256
import inspect
import json
from pathlib import Path
from types import SimpleNamespace as NS
import sys

sys.dont_write_bytecode = True
SOURCE = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build')
SCRATCH = Path(__file__).parent
sys.path[:0] = [str(SOURCE / 'src/web/backend/tests'), str(SOURCE / 'src/web/backend'), str(SOURCE / 'src')]
import w15_operator_run as operator
from wayfinder.domain.file_paths import safe_path

root = SCRATCH / 'offline-prepared-root'
(root / 'tmp').mkdir(parents=True, exist_ok=True)
content = b'Independent offline synthetic input; never a book/provider request'
(root / 'input.pdf').write_bytes(content)
digest = sha256(content).hexdigest()
manifest = root / 'report/w15-evidence/candidate.json'
manifest.parent.mkdir(parents=True, exist_ok=True)
manifest.write_text(json.dumps({'staged_copy': 'input.pdf', 'sha256': digest}), encoding='utf-8')
operator.ROOT = root
operator.subprocess = NS(check_output=lambda *a, **k: 'fake-offline-reviewed-profile')
created = []
engine = NS(execution_options=lambda **k: engine, connect=lambda: nullcontext(NS(execute=lambda stmt: created.append(str(stmt)))), dispose=lambda: None)
operator.create_database_engine = lambda *a, **k: engine
operator.upgrade_database = lambda *a: None
operator.test_database_url = lambda *a: 'fake://no-database'
def profile(run_dir, database):
    return NS(), NS()
operator.profile = profile
class Runtime:
    pipeline_version = 'fake-offline-reviewed-profile'
    phase_b_store = None
    def __init__(self, *a, **k):
        pass
    def pipeline_factory(self, *a, **k):
        assert k['allow_spend'] is False
        return NS()
    def close(self):
        pass
operator.RealBuildRuntime = Runtime
class DryRun:
    def __init__(self, *a, recorder, **k):
        self.recorder = recorder
    def execute(self, target, doc_id, *, dry_run):
        assert dry_run is True and target.read_bytes() == content and doc_id == 'u-' + digest[:20]
        result = NS(status='dry_run', model_calls=0, spent_usd=0,
                    to_dict=lambda: {'status': 'dry_run', 'model_calls': 0, 'spent_usd': 0})
        self.recorder(result)
        return result
operator.BuildDocument = DryRun

# Compile the old serializer into a separate in-memory namespace; never edit source.
old_source = inspect.getsource(operator.prepare).replace('run_dir.relative_to(ROOT).as_posix()', 'str(run_dir.relative_to(ROOT))')
assert old_source != inspect.getsource(operator.prepare)
old_namespace = dict(operator.__dict__)
exec(compile(old_source, '<offline-old-serializer>', 'exec'), old_namespace)
paths = [operator.prepare('candidate'), old_namespace['prepare']('candidate')]
reached = []
class ReachedComposition(Exception):
    pass
def stop_profile(run_dir, database):
    reached.append((run_dir, database))
    raise ReachedComposition
operator.profile = stop_profile
results = []
for path, old in zip(paths, [False, True], strict=True):
    saved = path.read_bytes()
    plan = json.loads(saved)
    permission = path.parent / 'fake-approval.json'
    permission.write_text(json.dumps({**{key: plan[key] for key in ('file_sha256', 'pipeline_version', 'database', 'embedding_price_profile')},
                                     'approved': True, 'approved_by': 'project-owner'}), encoding='utf-8')
    try:
        operator.execute(path, permission)
    except ReachedComposition:
        assert not old
        outcome = 'real execute reached fake composition sentinel'
    except ValueError as error:
        assert old and str(error) == 'Path escapes its root'
        outcome = 'old serializer reproduced Path escapes its root'
    else:
        raise AssertionError('Expected sentinel or rejection')
    assert path.read_bytes() == saved and not (path.parent / 'execution.json').exists()
    results.append({'old_serializer': old, 'run_dir': plan['run_dir'], 'outcome': outcome})
    if not old:
        assert '\\' not in plan['run_dir'] and plan['embedding_billing_verified'] is False and plan['approved'] is False
        for hostile in ('../outside', '/outside', 'C:/outside', 'tmp\\outside'):
            malicious = path.parent / 'hostile-plan.json'
            malicious.write_text(json.dumps({**plan, 'run_dir': hostile}), encoding='utf-8')
            try:
                operator.execute(malicious, permission)
            except ValueError as error:
                assert str(error) == 'Path escapes its root'
            else:
                raise AssertionError('Escaped run_dir reached composition')
assert len(reached) == 1 and len(created) == 2
print(json.dumps({'provider_calls': 0, 'database_connections': 0, 'old_red_new_green': True,
                  'hostile_paths_rejected': 4, 'results': results}, indent=2))
