"""SA-45: mutate guards in memory, run named assertions, leave source untouched."""
import json
from pathlib import Path
import subprocess
import sys


CASES = {
    'document_six_modules_allowed': (
        'tests/unit/application/test_phase_b_b2_artifacts.py::test_document_scope_over_five_modules_fails_before_calling_model',
        '''
import inspect, textwrap
from doc2roadmap.application.phase_b import documents
source = textwrap.dedent(inspect.getsource(documents.DocumentUseCase.create))
old = 'if len(set(module_ids)) > self.settings.document_max_modules:'
assert source.count(old) == 1
exec(source.replace(old, 'if False:'), documents.__dict__)
documents.DocumentUseCase.create = documents.create
'''),
    'roadmap_ignores_progress': (
        'tests/unit/application/test_phase_b_b2_artifacts.py::test_roadmap_quiz_prefers_learned_nodes_and_spreads_selection_by_module',
        '''
from doc2roadmap.application.phase_b.quiz import QuizUseCase
QuizUseCase._roadmap_sample = lambda self, concepts, owner, doc_id, limit, seed: concepts[:limit]
'''),
    'quiz_exposes_answer_flags': (
        'tests/unit/application/test_phase_b_quiz.py',
        '''
from doc2roadmap.application.phase_b.quiz import QuizUseCase
QuizUseCase._public_item = lambda self, item: dict(item)
'''),
    'empty_headings_retained': (
        'tests/unit/application/test_phase_b_sa30_documents.py::test_document_removes_heading_without_retained_body_and_punctuation_only_lines',
        '''
import inspect
from doc2roadmap.application.phase_b import postcheck
source = inspect.getsource(postcheck.check_text)
old = 'remove_headings.add(index)'
assert source.count(old) == 1
exec(source.replace(old, 'pass'), postcheck.__dict__)
'''),
}


def main():
    base = Path('tmp/sa45-artifact-mutants')
    base.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (target, mutation) in CASES.items():
        args = [target, '-q', '-p', 'no:cacheprovider', '--basetemp', str(base / name)]
        run = subprocess.run([sys.executable, '-c', mutation + '\nimport pytest\nraise SystemExit(pytest.main(' + repr(args) + '))'],
                             text=True, encoding='utf-8', errors='replace', capture_output=True)
        killed = run.returncode == 1 and 'FAILED' in run.stdout and 'AssertionError' in run.stdout
        rows.append({'mutation': name, 'assertion': target, 'killed': killed,
                     'exit_code': run.returncode, 'stdout_tail': run.stdout[-4500:], 'stderr': run.stderr[-1500:]})
    output = Path('tmp/sa45-artifact-mutations.json')
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'mutants': len(rows), 'killed': sum(row['killed'] for row in rows), 'output': str(output)}))
    return 0 if all(row['killed'] for row in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
