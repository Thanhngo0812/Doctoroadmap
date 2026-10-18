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
    assert lecture[-1]['event'] == 'final'
    assert lecture[-1]['lecture']['contract_version'] == 'lecture-1'
    assert not any(event['event'] == 'error' for event in lecture)
    quiz = events(request(base + '/api/quiz', {**args, 'module_id': 'module_001'}))
    assert quiz[-1]['event'] == 'final'
    public = quiz[-1]['quiz']
    assert public['contract_version'] == 'quiz-1'
    for item in public['items']:
        assert 'explanation' not in item
        for option in item['options']:
            assert set(option) == {'option_id', 'text'}
    answer = events(request(base + '/api/ask', {**args, 'module_id': 'module_001', 'question': 'Ma trận là gì?'}))
    assert answer[-1]['answer']['status'] == 'answered'
    assert answer[-1]['answer']['citations'][0]['chunk_id'] == 'c'


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
