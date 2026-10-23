"""SA-58: the assistant sends only scope values the real search accepts; multi-round recordings replay."""
import json
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.retrieval import SearchDocumentB
from doc2roadmap.application.ports.phase_b import ToolCall
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.llm.phase_b import RecordingToolModel, ReplayToolModel
from doc2roadmap.application.ports.phase_b import Done

import sa56_support as support
from sa56_support import Model, answer_turn, make_graph, session

MODEL_ID = 'fake-embedding'
ANSWER = 'Song ánh là ánh xạ vừa đơn ánh vừa toàn ánh. [S1]'


class FakeEmbedding:
    embedding_model_id = MODEL_ID

    def embed(self, requests):
        return [[1.0, 0.0] for _ in requests]


class FakeArtifacts:
    """The artifact store as SearchDocumentB reads it, built from the small synthetic graph."""

    def __init__(self):
        self.graph = make_graph()
        self.version = 1

    def _graph(self):
        return NS(version=1, manifest={'stage': 'stages', 'config': {'chunks_version': 1}},
                  payload=self.graph.payload)

    def load_latest_graph(self, doc_id):
        return self._graph()

    def load_graph(self, doc_id, version):
        return self._graph()

    def load_chunks(self, doc_id, version):
        return NS(manifest={}, result=NS(chunks=list(self.graph.chunks.values())))

    load_latest_chunks = lambda self, doc_id: self.load_chunks(doc_id, 1)

    def load_latest_retrieval(self, doc_id):
        documents = [{'chunk_id': c.chunk_id, 'text': c.text, 'vector': [1.0, 0.1 * i], 'doc_id': doc_id,
                      'section_id': 's', 'page': c.page, 'order_index': c.order_index,
                      'section_path': list(c.section_path)}
                     for i, c in enumerate(self.graph.chunks.values())]
        return NS(manifest={'embedding_model_id': MODEL_ID}, payload={'documents': documents})


def real_search(seen):
    """The callable composition_phase_b hands the assistant, with the real SearchDocumentB underneath."""
    searcher = SearchDocumentB(FakeArtifacts(), FakeEmbedding(), None)

    def search(query, *, scope, k, current_module_id=None):
        seen.append(scope)
        return searcher.search(query, doc_id='book', graph_version=1, current_module_id=current_module_id,
                               scope=scope, k=k, allow_spend=True)
    return search


def assistant(turns, scope_kind, seen):
    graph, store = make_graph(), InMemoryPhaseBStore()
    session(store, graph, scope_kind)
    model = Model(turns)
    return AssistantUseCase(graph, store, model, search=real_search(seen)), model


def ask(use_case, question='Song ánh là gì?'):
    return use_case.ask('book', 1, 's', question, owner='alice', allow_spend=True)


@pytest.mark.parametrize('scope_kind, expected', [('m3', 'uu_tien_module'), ('roadmap', 'ca_tai_lieu')])
def test_a_turn_runs_against_the_real_search_in_both_session_kinds(scope_kind, expected):
    seen = []
    use_case, _ = assistant([answer_turn()], scope_kind, seen)
    result = ask(use_case)
    assert result['status'] == 'answered' and '[S1]' in result['answer']
    assert seen == [expected]


def tool_search(args):
    seen = []
    turns = [[ToolCall('search_document', args, '1'), Done({})], answer_turn()]
    use_case, model = assistant(turns, 'm3', seen)
    result = ask(use_case)
    assert result['status'] in {'answered', 'partial'} and '[S1]' in result['answer']  # partial: a tool call was refused
    return result['tool_calls'][0]['result_summary'], seen, model


def test_search_tool_without_scope_uses_the_canonical_value():
    summary, seen, _ = tool_search({'query': 'song ánh'})
    assert 'hits' in summary and summary['hits']
    assert seen[-1] == 'uu_tien_module'


def test_search_tool_accepts_both_canonical_scopes():
    summary, seen, _ = tool_search({'query': 'song ánh', 'scope': 'ca_tai_lieu'})
    assert summary['hits'] and seen[-1] == 'ca_tai_lieu'


def test_search_tool_with_an_unknown_scope_returns_a_structured_error_and_the_turn_survives():
    summary, seen, model = tool_search({'query': 'song ánh', 'scope': 'ưu tiên module'})
    assert summary['error']['code'] == 'invalid_tool_call'
    assert seen == ['uu_tien_module']  # only the pre-round search reached the search; the tool call did not
    sent_back = json.dumps(model.calls[1][0], ensure_ascii=False)
    assert 'invalid_tool_call' in sent_back


def test_search_tool_declares_the_valid_scope_values():
    declaration = next(t for t in AssistantUseCase.TOOLS_FOR_TEST() if t['name'] == 'search_document') \
        if hasattr(AssistantUseCase, 'TOOLS_FOR_TEST') else None
    from doc2roadmap.application.phase_b.assistant import TOOLS
    declaration = next(t for t in TOOLS if t['name'] == 'search_document')
    assert declaration['parameters']['properties']['scope']['enum'] == ['uu_tien_module', 'ca_tai_lieu']
    assert 'uu_tien_module' in declaration['description'] and 'ca_tai_lieu' in declaration['description']


def test_a_two_round_turn_recorded_then_replayed_matches(tmp_path):
    path = tmp_path / 'rec.json'
    turns = [[ToolCall('search_document', {'query': 'song ánh'}, '1'), Done({})], answer_turn()]
    fixed_search = lambda query, **kwargs: [{'chunk_id': 'c4', 'text': support.DEF_SONG, 'page': 4, 'score': 1.0}]  # isolates the recording: scope handling is covered above
    graph, store = make_graph(), InMemoryPhaseBStore()
    session(store, graph, 'm3')
    recorder = RecordingToolModel(Model(turns), path, prompt_hash='sa58')
    live = ask(AssistantUseCase(graph, store, recorder, search=fixed_search))
    assert live['status'] == 'answered'

    recorded = json.loads(path.read_text(encoding='utf-8'))
    first = recorded['sessions'][0]['calls'][0]['messages']
    second = recorded['sessions'][0]['calls'][1]['messages']
    assert (len(first), len(second)) == (1, 3)  # round 1 as sent; later rounds do not rewrite it

    graph2, store2 = make_graph(), InMemoryPhaseBStore()
    session(store2, graph2, 'm3')
    replayed = ask(AssistantUseCase(graph2, store2, ReplayToolModel(path, prompt_hash='sa58'),
                                    search=fixed_search))
    assert replayed['answer'] == live['answer'] and '[S1]' in live['answer']
    assert [row['name'] for row in replayed['tool_calls']] == ['search_document']
