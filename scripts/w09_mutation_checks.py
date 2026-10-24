"""Sequential falsifiable W09 guards. Run with no gate/browser server on this tree."""
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get('W09_MUTATION_RUN', 'mutations')
assert re.fullmatch(r'mutations[a-z0-9-]*', RUN)
OUT = ROOT / 'report/w09-evidence' / RUN
BACK = 'src/web/backend/wayfinder/'
FRONT = 'src/web/frontend/src/'
TEST = 'src/web/backend/tests/test_assistant_w09.py::test_w09_'
cases = [
    ('session-owner', BACK+'application/learning_gateway.py',
        "session = self.runtime.sessions(graph).get(actor.user_id, sid)", "session = self.runtime.store.get_record('session', sid)",
        'sessions_bind_actor_document_and_scope_from_published_graph'),
    ('scope-server', BACK+'application/learning_gateway.py',
        "[nid for nid in graph.modules[mid]['node_ids'] if nid in graph.learnable_nodes]", "scope.get('node_ids', [])",
        'sessions_bind_actor_document_and_scope_from_published_graph'),
    ('focus', BACK+'application/learning_gateway.py',
        'focus_node_id=focus, allow_spend=True', 'focus_node_id=None, allow_spend=True',
        'focus_reads_actual_lecture3_cache_and_a_cache_miss_never_generates'),
    ('tool-actor', BACK+'infrastructure/assistant_model.py',
        "if k not in {'owner', 'doc_id', 'graph_version'}", 'if True',
        'tools_create_real_quiz3_document3_with_server_identity_and_core_scope'),
    ('rate', BACK+'infrastructure/assistant_requests.py',
        'len(times) >= self.settings.assistant_turns_per_minute', 'len(times) >= 100',
        'rate_limit_counts_new_intents_across_courses_but_not_retries'),
    ('session-mutex', BACK+'infrastructure/assistant_requests.py',
        "c.execute('SELECT pg_advisory_lock(hashtextextended(%s,0))', ('web-session:' + sid,))", "c.execute('SELECT 1')",
        'two_concurrent_distinct_intents_are_serialized_not_coalesced'),
    ('personal-cap', BACK+'infrastructure/learning_runtime.py',
        'learner_daily_max_usd=1.0', 'learner_daily_max_usd=2.0',
        'daily_limit_is_shared_across_courses_and_separate_for_each_learner'),
    ('canonical-ledger', BACK+'infrastructure/learning_usage.py',
        'SELECT coalesce(sum(cost_usd),0) FROM usage_ledger WHERE learner_id=:owner',
        "SELECT coalesce(sum((extra->>'cost_usd')::float),0) FROM usage_ledger WHERE learner_id=:owner",
        'usage_ratio_has_one_ledger_and_does_not_double_count_build_receipts'),
    ('artifact-owner', BACK+'application/learning_gateway.py',
        "record.get('owner') != actor.user_id or record.get('doc_id')", "False or record.get('doc_id')",
        'artifact_card_and_content_recheck_owner_book_and_ready_state'),
    ('artifact-book', BACK+'application/learning_gateway.py',
        "or record.get('doc_id') != course.doc_id", 'or False',
        'artifact_card_and_content_recheck_owner_book_and_ready_state'),
    ('artifact-ready', BACK+'application/learning_gateway.py',
        "if record.get('status') != 'ready':", 'if False:',
        'artifact_card_and_content_recheck_owner_book_and_ready_state'),
    ('private-sse', BACK+'api/assistant.py',
        "'text': TOOL_LABELS.get(name, 'Đang xử lý yêu cầu…')", "'text': str(row)",
        'sse_dto_discards_tool_args_and_nested_admin_data_even_from_bad_gateway'),
    ('cache-only', BACK+'infrastructure/learning_runtime.py',
        'cache_only=True)', 'cache_only=False)',
        'focus_is_per_turn_and_cache_only_never_generates_lectures'),
    ('idempotency-deploy', BACK+'application/learning_gateway.py',
        "if previous.get('client_turn_id') == key:", 'if False:',
        'answer3_history_and_idempotency_keep_private_fields_on_server'),
    ('disconnect', BACK+'api/assistant.py',
        '        def emit(row):\n            if not disconnected.is_set():',
        "        def emit(row):\n            if disconnected.is_set():\n                raise RuntimeError('mutation aborts producer after disconnect')\n            if not disconnected.is_set():",
        'http_disconnect_completes_and_retry_reuses_the_saved_turn'),
    ('ui-focus', FRONT+'useAssistant.ts',
        '...(focus === undefined ? {} : { focus_node_id: focus })', '...{}', 'react'),
    ('ui-retry-id', FRONT+'useAssistant.ts',
        'retry: () => live && run(live.intent)', 'retry: () => live && run({ ...live.intent, client_turn_id: crypto.randomUUID() })', 'react'),
    ('ui-fabricated-link', FRONT+'AssistantAnswer.tsx',
        'text={text} sources={answer?.sources} onSource={onSource} allowLinks={false}',
        'text={text} sources={answer?.sources} onSource={onSource} allowLinks={true}', 'react'),
    ('ui-new-session', FRONT+'Assistant.tsx',
        'disabled={Boolean(chat.live?.busy) || sessionBusy || amount?.limited}',
        'disabled={Boolean(chat.live?.busy) || amount?.limited}', 'react'),
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
                'src/Assistant.test.tsx', '--reporter=junit', '--outputFile=../../../'+str(junit.relative_to(ROOT)).replace('\\','/')]
        else:
            args = [sys.executable, '-X', 'utf8', 'scripts/w05_run_tests.py', '-o', 'addopts=', '-q', TEST+test,
                '--basetemp=tmp/w09-'+RUN+'-'+name, '--junitxml='+str(junit.relative_to(ROOT))]
        try:
            target.write_text(source.replace(before, after), encoding='utf8')
            with log.open('wb') as output:
                native = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, env=os.environ).returncode
            tree = ET.parse(junit)
            failed = [row.attrib.get('name') for row in tree.findall('.//testcase') if row.find('failure') is not None]
            errors = tree.findall('.//testcase/error')
            row = dict(name=name, path=relative, sourceSha256=hashlib.sha256(original).hexdigest(),
                command=args, nativeExitCode=native, failedAssertions=failed, errors=len(errors))
            results.append(row)
            assert native == 1 and failed and not errors, row
        finally:
            target.write_bytes(original)
            assert target.read_bytes() == original
            (OUT / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        print(name + ': RED; source restored', flush=True)
    return 0


if __name__ == '__main__': raise SystemExit(main())
