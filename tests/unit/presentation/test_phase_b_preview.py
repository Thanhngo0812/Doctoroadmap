import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.models import Chunk, ChunkingResult, DocumentNode, DocumentTree, Section
from doc2roadmap.presentation.preview.server import PreviewServer


@pytest.fixture
def runtime(tmp_path):
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=tmp_path, _env_file=None), mode='offline')
    store = runtime.artifacts
    text = 'Ma trận là bảng các số được xếp thành hàng và cột. Hạng ma trận mô tả tính độc lập của các hàng.'
    tree = DocumentTree([DocumentNode('text', text, 0, page=1)])
    parse = store.save_parse('doc-1', 'source', 'parser', 'parse', {}, tree)
    section = Section('s', 'doc-1', '2.1 Ma trận', 1, 1, None, ['Ma trận'], 0)
    chunk = Chunk('c', 'doc-1', 0, 0, 1, 0, len(text), 's', ['Ma trận'], 1,
                  ['text'], text, None, [], 30, 'test')
    store.save_chunks('doc-1', 'source', 'chunks', {}, parse.version,
                      ChunkingResult('doc-1', [section], [chunk], text))
    nodes = [{'node_id': 'n' + str(i), 'name': name, 'learnable': True, 'module_id': 'module_001',
              'teaching_status': 'taught', 'teaching_chunk_ids': ['c'], 'display_prerequisites': [],
              'anchor': {'chunk_id': 'c', 'sentence': text.split('. ')[i % 2].rstrip('.') + '.'}}
             for i, name in enumerate(['Ma trận', 'Hạng ma trận', 'Hàng ma trận'])]
    payload = {'stage': 'stages', 'doc_id': 'doc-1', 'nodes': nodes,
               'modules': [{'module_id': 'module_001', 'index': 0, 'title': 'Ma trận',
                            'node_ids': [node['node_id'] for node in nodes]}],
               'sequence': [node['node_id'] for node in nodes], 'requires_edges': [],
               'chunk_module_map': {'c': {'module_id': 'module_001'}}}
    store.save_graph('doc-1', 'source', 'graph', {'chunks_version': 1}, payload,
                     upstream_version=None, manifest_fields={'stage': 'stages'})
    store.save_retrieval('doc-1', 'source', 'index', {}, {'documents': [
        {'chunk_id': 'c', 'text': text, 'section_id': 's', 'doc_id': 'doc-1', 'vector': [1.0],
         'page': 1, 'order_index': 0}]}, upstream_version=1)
    return runtime


@pytest.fixture
def server(runtime):
    server = PreviewServer(runtime, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join(5)


def request(url, body=None, headers=None):
    payload = json.dumps(body).encode() if body is not None else None
    with urlopen(Request(url, data=payload, headers={'Content-Type': 'application/json', **(headers or {})}), timeout=10) as response:
        return response.read().decode()


def events(text):
    return [json.loads(frame[6:]) for frame in text.split('\n\n') if frame.startswith('data: ')]


def test_preview_serves_only_its_page_and_development_documents(server):
    service, base = server
    assert service.server_address[0] == '127.0.0.1'
    docs = json.loads(request(base + '/api/docs'))
    assert docs['mode'] == 'offline'
    assert [doc['doc_id'] for doc in docs['documents']] == ['doc-1']
    assert 'lang="vi"' in request(base + '/')
    for path in ('/.env', '/../../.env', '/api/roadmap?doc_id=d01-t01'):
        with pytest.raises(HTTPError) as error:
            request(base + path)
        assert error.value.code in {400, 404}


def test_stream_endpoints_use_real_use_cases_and_never_return_quiz_answers(server):
    _, base = server
    args = {'doc_id': 'doc-1', 'graph_version': 1}
    lecture = events(request(base + '/api/lecture', {**args, 'node_id': 'n0'}))
    assert lecture[0]['event'] == 'skeleton'
    assert lecture[-1]['event'] == 'failure'
    assert lecture[-1]['lecture']['contract_version'] == 'lecture-3'
    assert lecture[-1]['lecture']['status'] == 'failed'
    assert lecture[-1]['lecture']['failure']['reason_code'] == 'khong_co_mo_hinh'
    assert not any(event['event'] in {'item', 'delta'} for event in lecture)
    quiz = events(request(base + '/api/quiz', {**args, 'scope': {'kind': 'roadmap'}}))
    assert quiz[-1]['event'] == 'final'
    public = quiz[-1]['quiz']
    assert public['contract_version'] == 'quiz-2'
    assert public['home_scope'] == {'kind': 'roadmap'}
    assert public['origin'] == 'button'
    assert public['session_id'] is None
    for item in public['items']:
        assert 'explanation' not in item
        for option in item['options']:
            assert set(option) == {'option_id', 'text'}
    session = json.loads(request(base + '/api/session', {**args, 'scope': {'kind': 'module',
        'node_ids': ['n0', 'n1', 'n2'], 'module_id_at_creation': 'module_001', 'graph_version_at_creation': 1}}))
    answer = events(request(base + '/api/ask', {**args, 'session_id': session['session_id'],
        'question': 'Ma trận là gì?'}))
    assert answer[-1]['answer']['status'] == 'answered'
    assert answer[-1]['answer']['sources'][0]['chunk_id'] == 'c'
    assert 'answer_md' in answer[-1]['answer'] and 'validation' not in answer[-1]['answer']


def test_preview_ask_passes_focus_node_id_and_reads_the_lecture_cache_without_writing_to_it(server):
    service, base = server
    args = {'doc_id': 'doc-1', 'graph_version': 1}
    session = json.loads(request(base + '/api/session', {**args, 'scope': {'kind': 'module',
        'node_ids': ['n0', 'n1', 'n2'], 'module_id_at_creation': 'module_001', 'graph_version_at_creation': 1}}))
    focused = events(request(base + '/api/ask', {**args, 'session_id': session['session_id'],
        'question': 'giải thích phần này', 'focus_node_id': 'n1'}))[-1]['answer']
    assert focused['focus_node_id'] == 'n1' and focused['linked_node_ids'] == ['n1']
    ignored = events(request(base + '/api/ask', {**args, 'session_id': session['session_id'],
        'question': 'giải thích phần này', 'focus_node_id': 'không-có'}))[-1]['answer']
    assert ignored['focus_node_id'] is None
    log = service.runtime.store.get_record('assistant_validation', ignored['answer_id'])
    assert log['focus_ignored'] is True and 'warnings' not in ignored
    store = service.runtime.store
    assert store.list_records('lecture_failure') == []
    assert {row['purpose'] for row in store.usage_rows()} <= {'assistant'}


def test_preview_relays_ready_lecture_items_after_the_skeleton_gate(server):
    service, base = server

    def scripted_lecture(graph, node_id, *, on_event, **_kwargs):
        skeleton = {'contract_version': 'lecture-2', 'doc_id': graph.doc_id,
                    'graph_version': graph.graph_version, 'node_id': node_id,
                    'status': 'generating', 'definition': {}, 'prerequisites': [],
                    'next_up': [], 'sections': [], 'usage': {}}
        on_event({'event': 'skeleton', 'lecture': skeleton})
        item = {'kind': 'giai_thich', 'text': 'Câu ví dụ [S1]',
                'citations': [{'label': 'S1', 'chunk_id': 'c', 'quote': 'Ma trận là bảng'}]}
        on_event({'event': 'item', 'item': item})
        on_event({'event': 'final', 'lecture': {**skeleton, 'status': 'ready',
            'sections': [{'kind': 'giai_thich', 'items': [item]}]}})

    service.runtime.lecture = scripted_lecture
    rows = events(request(base + '/api/lecture', {
        'doc_id': 'doc-1', 'graph_version': 1, 'node_id': 'n0'}))
    assert [row['event'] for row in rows] == ['skeleton', 'item', 'final']
    assert rows[1]['item']['text'] == rows[-1]['lecture']['sections'][0]['items'][0]['text']


def test_preview_progress_and_roadmap_contracts(server):
    _, base = server
    args = {'doc_id': 'doc-1', 'graph_version': 1}
    before = json.loads(request(base + '/api/progress?' + 'doc_id=doc-1&graph_version=1'))
    assert before['contract_version'] == 'progress-1'
    assert before['modules'][0] == {'module_id': 'module_001', 'learned': 0, 'total': 3}
    after = json.loads(request(base + '/api/progress', {**args, 'node_id': 'n0', 'learned': True}))
    assert after['node_id'] == 'n0' and after['source'] == 'learner'
    assert after['state'] == 'learned'
    roadmap = json.loads(request(base + '/api/roadmap?doc_id=doc-1&graph_version=1'))
    assert roadmap['modules'][0]['progress'] == {'module_id': 'module_001', 'learned': 1, 'total': 3}

    sessions = json.loads(request(base + '/api/sessions?doc_id=doc-1&filter=roadmap_page'))
    assert sessions['sessions'] == []
    library = json.loads(request(base + '/api/library?doc_id=doc-1&scope_filter=all'))
    assert library['contract_version'] == 'library-1'


def test_preview_artifact_ids_are_bound_to_the_selected_development_document(server):
    service, base = server
    store = service.runtime.store
    store.put_record('documents', 'guessed-doc-artifact', {
        'document_id': 'guessed-doc-artifact', 'owner': 'local',
        'doc_id': 'outside-development', 'title': 'PRIVATE DOCUMENT MARKER',
        'markdown': 'PRIVATE DOCUMENT BODY',
    })
    store.put_record('quiz_attempt', 'guessed-quiz-attempt', {
        'attempt_id': 'guessed-quiz-attempt', 'owner': 'local',
        'doc_id': 'outside-development', 'items': [], '_private': {},
    })
    store.put_record('session', 'guessed-session', {
        'session_id': 'guessed-session', 'owner': 'local', 'doc_id': 'outside-development',
    })

    for path in (
        '/api/document?doc_id=doc-1&graph_version=1&document_id=guessed-doc-artifact',
        '/api/document?doc_id=doc-1&graph_version=1&document_id=guessed-doc-artifact&format=md',
        '/api/quiz-attempt?doc_id=doc-1&graph_version=1&attempt_id=guessed-quiz-attempt',
        '/api/turns?doc_id=doc-1&graph_version=1&session_id=guessed-session',
    ):
        with pytest.raises(HTTPError) as error:
            request(base + path)
        assert error.value.code == 400
        assert 'PRIVATE DOCUMENT' not in error.value.read().decode()

    history = json.loads(request(base + '/api/history?doc_id=doc-1&graph_version=1'))
    assert history['attempts'] == []
    assert json.loads(request(base + '/api/history'))['attempts'] == []
    with pytest.raises(HTTPError) as error:
        request(base + '/api/usage?doc_id=outside-development')
    assert error.value.code == 400

    for path, body in (
        ('/api/submit', {'attempt_id': 'guessed-quiz-attempt', 'answers': {}}),
        ('/api/quiz-report', {'attempt_id': 'guessed-quiz-attempt', 'item_id': 'foreign-item'}),
    ):
        with pytest.raises(HTTPError) as error:
            request(base + path + '?doc_id=doc-1&graph_version=1', body)
        assert error.value.code == 400


def test_preview_renders_only_allowlisted_pdf_pages_and_checks_bounds(server):
    _, base = server
    with urlopen(base + '/api/page?doc_id=doc-1&graph_version=1&page=1', timeout=10) as response:
        assert response.headers.get_content_type() == 'image/png'
        assert response.read(8) == b'\x89PNG\r\n\x1a\n'
    with pytest.raises(HTTPError) as error:
        request(base + '/api/page?doc_id=doc-1&graph_version=1&page=9999')
    assert error.value.code == 400


def test_preview_session_delete_keeps_linked_document_in_library(server):
    service, base = server
    args = {'doc_id': 'doc-1', 'graph_version': 1}
    session = json.loads(request(base + '/api/session', {**args, 'scope': {
        'kind': 'module', 'node_ids': ['n0', 'n1'],
        'module_id_at_creation': 'module_001', 'graph_version_at_creation': 1}}))
    service.runtime.store.put_record('documents', 'saved-document', {
        'document_id': 'saved-document', 'owner': 'local', 'doc_id': 'doc-1',
        'graph_version': 1, 'title': 'Tài liệu đã lưu', 'status': 'ready',
        'home_scope': {'kind': 'module', 'node_ids': ['n0', 'n1'],
                       'module_id_at_creation': 'module_001', 'graph_version_at_creation': 1},
        'session_id': session['session_id'], 'origin': 'assistant', 'node_ids': ['n0'],
        'created_at': '2026-10-18T00:00:00+00:00', 'markdown': 'Nội dung kiểm tra',
    })
    service.runtime.store.put_record('documents', 'elsewhere-document', {
        'document_id': 'elsewhere-document', 'owner': 'local', 'doc_id': 'doc-1',
        'graph_version': 1, 'title': 'Tài liệu từ lộ trình', 'status': 'ready',
        'home_scope': {'kind': 'roadmap'}, 'session_id': None, 'origin': 'button',
        'node_ids': ['n1'], 'created_at': '2026-10-18T00:00:01+00:00', 'markdown': 'Nội dung khác',
    })
    deleted = json.loads(request(base + '/api/session-delete', {
        **args, 'session_id': session['session_id']}))
    assert deleted == {'deleted': True, 'session_id': session['session_id']}
    library = json.loads(request(base + '/api/library?doc_id=doc-1&graph_version=1&scope_filter=module:module_001'))
    items = {row['id']: row for row in library['items']}
    assert items['saved-document']['session_deleted'] is True
    assert items['saved-document']['group'] == 'here'
    assert items['elsewhere-document']['group'] == 'elsewhere'
    assert items['elsewhere-document']['label'] == 'tạo ở nơi khác'


def test_foreign_origin_is_rejected_even_on_localhost(server):
    _, base = server
    with pytest.raises(HTTPError) as error:
        request(base + '/api/docs', headers={'Origin': 'https://example.com'})
    assert error.value.code == 403


def test_new_cli_dispatches_without_calling_model_or_writing_on_dry_run(monkeypatch, capsys):
    from doc2roadmap.presentation.cli import main, phase_b
    calls = []
    class Runtime:
        def __init__(self, **kwargs):
            calls.append(kwargs)
        def naming(self, *args, **kwargs):
            assert kwargs['dry_run']
            return {'dry_run': True, 'calls_estimate': 4}
    monkeypatch.setattr(phase_b, 'PhaseBRuntime', Runtime)
    assert main.main(['phase-b', 'names', '--doc-id', 'doc-1', '--dry-run']) == 0
    assert json.loads(capsys.readouterr().out)['calls_estimate'] == 4
    assert calls[0]['allow_spend'] is False


def test_lecture_diagnostics_cli_summarizes_ledger_without_loading_graph_or_model(monkeypatch, capsys):
    from types import SimpleNamespace
    from doc2roadmap.presentation.cli import main, phase_b

    class Runtime:
        def __init__(self, **kwargs):
            self.store = SimpleNamespace(usage_rows=lambda doc_id: [
                {'purpose': 'lecture', 'doc_id': 'doc-1', 'cost_usd': 0.001},
                {'purpose': 'lecture_validation', 'doc_id': 'doc-1', 'generation_id': 'g',
                 'passed': False, 'validation_rules': ['K8'], 'dropped_by_rule': {'K6': 2}}])

    monkeypatch.setattr(phase_b, 'PhaseBRuntime', Runtime)
    assert main.main(['phase-b', 'lecture-diagnostics', '--doc-id', 'doc-1']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['dropped_by_rule'] == {'K6': 2}
    assert len(result['generations']) == 1


def test_why_here_cli_passes_shared_quote_settings(monkeypatch, capsys, tmp_path):
    from types import SimpleNamespace
    from doc2roadmap.presentation.cli import main, phase_b
    settings_file = tmp_path / 'settings.json'
    settings_file.write_text('{"quote_max_chars": 80}', encoding='utf-8')

    class Runtime:
        def __init__(self, *, b_settings, **kwargs):
            self.b_settings = b_settings

        def graph(self, doc_id, version):
            return SimpleNamespace(why_here=lambda node_id, *, settings: {'limit': settings.quote_max_chars})

    monkeypatch.setattr(phase_b, 'PhaseBRuntime', Runtime)
    assert main.main(['phase-b', 'graph-tool', 'why_here', 'n', '--doc-id', 'doc-1',
                      '--settings', str(settings_file)]) == 0
    assert json.loads(capsys.readouterr().out)['limit'] == 80
