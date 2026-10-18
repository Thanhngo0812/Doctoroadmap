import argparse
from types import SimpleNamespace

import pytest

from doc2roadmap.presentation.cli import phase_b


def parse(*args):
    parser = argparse.ArgumentParser()
    phase_b.configure(parser.add_subparsers(dest='command', required=True))
    return parser.parse_args(['phase-b', *args])


def test_ask_cli_requires_saved_session_and_has_no_module_argument():
    args = parse('ask', '--doc-id', 'doc-1', '--session-id', 'session', 'Câu hỏi')
    assert args.session_id == 'session' and args.question == 'Câu hỏi'
    assert not hasattr(args, 'module_id')
    with pytest.raises(SystemExit):
        parse('ask', '--doc-id', 'doc-1', 'Câu hỏi')
    with pytest.raises(SystemExit):
        parse('ask', '--doc-id', 'doc-1', '--session-id', 's', '--module-id', 'm', 'Câu hỏi')


def test_session_progress_scope_and_library_cli_call_public_use_cases(monkeypatch):
    calls = []
    graph = SimpleNamespace(doc_id='doc-1', graph_version=2,
                            modules={'m': {'node_ids': ['n'], 'index': 0}})
    class UseCase:
        def __getattr__(self, name):
            def invoke(*args):
                calls.append((name, args))
                return {'called': name}
            return invoke
    runtime = SimpleNamespace(graph=lambda *_: graph, b_settings=phase_b.BSettings(),
                              sessions=lambda _: UseCase(), progress=lambda _: UseCase(), library=lambda _: UseCase())
    monkeypatch.setattr(phase_b, 'PhaseBRuntime', lambda **_: runtime)
    phase_b.run(parse('session-create', '--doc-id', 'doc-1', '--owner', 'alice', '--scope', 'm'))
    assert calls[-1] == ('create_session', ('alice', 'doc-1', {'kind': 'module', 'node_ids': ['n'],
                                                             'module_id_at_creation': 'm', 'graph_version_at_creation': 2}))
    phase_b.run(parse('progress-set', '--doc-id', 'doc-1', '--owner', 'alice', '--node-id', 'n', '--not-learned'))
    assert calls[-1] == ('set_progress', ('alice', 'doc-1', 'n', False))
    phase_b.run(parse('session-turns', '--doc-id', 'doc-1', '--session-id', 's'))
    assert calls[-1] == ('list_turns', ('local', 's'))
    phase_b.run(parse('library', '--doc-id', 'doc-1', '--filter', 'module:m'))
    assert calls[-1] == ('list_library', ('local', 'doc-1', 'module:m'))
    assert phase_b.run(parse('scope-resolve', '--doc-id', 'doc-1', '--scope', 'm'))['module_id'] == 'm'
