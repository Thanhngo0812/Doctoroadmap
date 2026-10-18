"""Run the explicit Phase B audit suite; never discover the entire repository."""
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def main():
    tests = sorted(path for path in (ROOT / 'tests/unit/application').glob('test_phase_b*.py')
                   if path.name != 'test_phase_b_gop_graph_19e.py')
    tests += [ROOT / path for path in (
        'tests/unit/application/test_sa45_sessions_audit_regressions.py',
        'tests/unit/domain/test_learning_graph.py',
        'tests/unit/infrastructure/test_phase_b_llm.py',
        'tests/unit/infrastructure/test_phase_b_sa30_timing.py',
        'tests/unit/presentation/test_phase_b2_cli.py',
        'tests/unit/presentation/test_phase_b_preview.py',
        'tests/unit/test_architecture.py',
    )]
    assert tests and all(path.is_file() for path in tests)
    args = [str(path.relative_to(ROOT)) for path in tests]
    args += ['-q', '-p', 'no:cacheprovider', '--basetemp', 'tmp/sa45-final-tests',
             '--junitxml', 'tmp/sa45-final-tests.xml']
    print(f'Explicit audit suite: {len(tests)} test files; no repository-wide discovery.', flush=True)
    return subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pytest', *args], cwd=ROOT).returncode


if __name__ == '__main__':
    raise SystemExit(main())
