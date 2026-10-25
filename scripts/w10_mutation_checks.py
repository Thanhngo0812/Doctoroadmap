"""Sequential falsifiable W10 guards. Run with no gate/browser server on this tree."""
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get('W10_MUTATION_RUN', 'mutations')
assert re.fullmatch(r'mutations[a-z0-9-]*', RUN)
OUT = ROOT / 'report/w10-evidence' / RUN
BACK = 'src/web/backend/wayfinder/'
FRONT = 'src/web/frontend/src/'
TEST = 'src/web/backend/tests/test_content_w10.py::test_w10_'
cases = [
    [
        "result-owner",
        "src/web/backend/wayfinder/application/learning_gateway.py",
        "if not row or row.get('owner') != actor.user_id or row.get('doc_id') != course.doc_id:",
        "if not row or False or row.get('doc_id') != course.doc_id:",
        "quiz_public_snapshot_has_no_answers_and_submission_preserves_shuffled_mapping"
    ],
    [
        "content-book",
        "src/web/backend/wayfinder/application/learning_gateway.py",
        "if not row or row.get('owner') != actor.user_id or row.get('doc_id') != course.doc_id:",
        "if not row or row.get('owner') != actor.user_id or False:",
        "saved_content_cannot_be_opened_through_another_book"
    ],
    [
        "document-scope",
        "src/web/backend/wayfinder/application/learning_gateway.py",
        "if len(modules) > self.runtime.settings.document_max_modules:",
        "if len(modules) > 6:",
        "document_six_modules_rejected_before_model_and_eleventh_request_is_rate_limited"
    ],
    [
        "document-rate",
        "src/web/backend/wayfinder/infrastructure/document_requests.py",
        "if len(times) >= self.settings.documents_per_hour:",
        "if len(times) > self.settings.documents_per_hour:",
        "document_six_modules_rejected_before_model_and_eleventh_request_is_rate_limited"
    ],
    [
        "atomic-submit",
        "src/web/backend/wayfinder/application/learning_gateway.py",
        "# Core submission and progress writes share this short PostgreSQL transaction.\n        with self.runtime.store.atomic():",
        "# Core submission and progress writes share this short PostgreSQL transaction.\n        from contextlib import nullcontext\n        with nullcontext():",
        "submission_rolls_back_both_attempt_and_progress_when_core_write_fails"
    ],
    [
        "idempotent-submit",
        "src/web/backend/wayfinder/application/learning_gateway.py",
        "if row.get('submission'):\n                if row['submission']['answers'] != answers:",
        "if False:\n                if row['submission']['answers'] != answers:",
        "quiz_public_snapshot_has_no_answers_and_submission_preserves_shuffled_mapping"
    ],
    [
        "selected-reason",
        "src/web/backend/wayfinder/application/content_view.py",
        "'is_correct', 'explanation', 'why_wrong'",
        "'is_correct', 'explanation'",
        "wrong_answer_returns_only_selected_why_wrong_and_library_score"
    ],
    [
        "ui-core-group",
        "src/web/frontend/src/ContentLibrary.tsx",
        "rows.filter(row => row.group === group)",
        "rows.filter(row => row.origin === (group === 'here' ? 'button' : 'assistant'))",
        "react"
    ],
    [
        "ui-early-choice",
        "src/web/frontend/src/ContentPages.tsx",
        "answers: answersRef.current",
        "answers: {}",
        "react"
    ]
]


def main():
    assert not OUT.exists(), 'Retain the previous mutation run'
    OUT.mkdir(parents=True)
    results = []
    for name, relative, before, after, test in cases:
        target = ROOT / relative; original = target.read_bytes(); source = original.decode('utf8')
        assert source.count(before) == 1, (name, 'mutation must have exactly one target', source.count(before))
        log, junit = OUT / (name+'.log'), OUT / (name+'.xml')
        if test == 'react':
            args = ['cmd', '/d', '/c', 'npm.cmd', '--prefix', 'src/web/frontend', 'test', '--', '--pool=threads', '--maxWorkers=1',
                'src/Content.test.tsx', '--reporter=junit', '--outputFile=../../../'+str(junit.relative_to(ROOT)).replace('\\','/')]
        else:
            args = [sys.executable, '-X', 'utf8', 'scripts/w05_run_tests.py', '-o', 'addopts=', '-q', TEST+test,
                '--basetemp=tmp/w10-'+RUN+'-'+name, '--junitxml='+str(junit.relative_to(ROOT))]
        try:
            target.write_text(source.replace(before, after), encoding='utf8')
            with log.open('wb') as output:
                native = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, env=os.environ).returncode
            tree = ET.parse(junit)
            failed = [row.attrib.get('name') for row in tree.findall('.//testcase') if row.find('failure') is not None]
            errors = tree.findall('.//testcase/error')
            row = dict(name=name, path=relative, sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(), sourceSha256=hashlib.sha256(original).hexdigest(), mutatedSha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                command=args, nativeExitCode=native, failedAssertions=failed, errors=len(errors))
            results.append(row)
            assert native == 1 and failed and not errors, row
        finally:
            target.write_bytes(original)
            assert target.read_bytes() == original
            results[-1]['restoredSha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            (OUT / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        print(name + ': RED; source restored', flush=True)
    return 0


if __name__ == '__main__': raise SystemExit(main())
