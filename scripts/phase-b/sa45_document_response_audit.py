"""Audit six historical responses through B2; deliberately no old prompt matching.

This is response-only replay, not a replay of current model decisions or latency.
No provider adapter is constructed. Only pinned development documents are loaded.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


ROOT = Path(__file__).resolve().parents[2]
PINS = [('doc-1', 37), ('nhap-mon-ml', 37), ('naive-bayes', 37),
        ('doc-6', 8), ('xstk-ch3-1', 46), ('doc-4', 12)]


class ResponseOnly:
    is_replay = True
    model_id = 'gemini-3.1-flash-lite'

    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def ask_json(self, prompt, *, response_schema, system_prompt=''):
        self.calls += 1
        assert self.calls == 1
        return SimpleNamespace(payload=deepcopy(self.payload), usage={})


def main():
    spec = importlib.util.spec_from_file_location('sa30_replay_helpers', Path(__file__).with_name('sa30_documents_replay.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    fixture = json.loads(helper._merge_document_fixture().read_text(encoding='utf-8'))
    operations = [row for row in json.loads(helper.LIVE.read_text(encoding='utf-8'))['operations']
                  if row['kind'] == 'document']
    assert [(row['doc_id'], row['graph_version']) for row in operations] == PINS
    assert len(fixture['sessions']) == len(PINS)
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ROOT / 'artifacts'), mode='offline', allow_spend=False)
    store = InMemoryPhaseBStore()
    rows = []
    for operation, session in zip(operations, fixture['sessions']):
        calls = session['calls']
        assert len(calls) == 1 and calls[0]['kind'] == 'json'
        old_context = json.loads(calls[0]['prompt'].split('\nUse Markdown', 1)[0])
        request = f"Tạo bản ôn tập ngắn về {operation['concept']}, mỗi ý có trích dẫn."
        assert old_context['request'] == request
        assert operation['node_id'] in old_context['scope']['node_ids']
        model = ResponseOnly(calls[0]['reply']['payload'])
        graph = runtime.graph(operation['doc_id'], operation['graph_version'])
        result = DocumentUseCase(model, store, settings=runtime.b_settings,
                                 retriever=helper._document_search(operation)).create(
            graph.doc_id, graph.graph_version, graph, request, operation['node_id'],
            owner='sa45-audit', allow_spend=True)
        offset_errors = []
        for citation in result['citations']:
            chunk = graph.chunks[citation['chunk_id']]
            start = citation['char_start'] - chunk.char_start
            end = citation['char_end'] - chunk.char_start
            if chunk.text[start:end] != citation['quote']:
                offset_errors.append(citation['label'])
        raw_quotes = {row['label']: row.get('quote') for row in model.payload['citations']}
        rows.append({'doc_id': graph.doc_id, 'graph_version': graph.graph_version, 'result': result,
                     'repaired_quotes': sum(raw_quotes.get(row['label']) != row['quote'] for row in result['citations']),
                     'offset_errors': offset_errors, 'response_replay_calls': model.calls})
    output = {'kind': 'response_only_replay', 'prompt_match': False, 'http_calls': 0,
              'cost_usd': sum(row['cost_usd'] for row in store.usage_rows()),
              'results': rows, 'usage_rows': store.usage_rows()}
    path = ROOT / 'tmp/sa45-document-response-audit.json'
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'documents': len(rows), 'ready': sum(row['result']['status'] == 'ready' for row in rows),
                      'repaired_quotes': sum(row['repaired_quotes'] for row in rows),
                      'offset_errors': sum(len(row['offset_errors']) for row in rows),
                      'cost_usd': output['cost_usd'], 'http_calls': 0, 'output': str(path)}))


if __name__ == '__main__':
    main()
