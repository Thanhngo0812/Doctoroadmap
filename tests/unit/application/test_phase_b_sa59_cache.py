"""SA-59: graph/index cache and query-vector reuse keep results identical and never mix data."""
from collections import Counter
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.concept_index import IndexConcepts
from doc2roadmap.application.phase_b.retrieval import SearchContextCache, SearchDocumentB
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.infrastructure.embedding.query_cache import CachedQueryEmbedding

MODEL = 'fake-768'


class Embedding:
    identifier = 'fake'
    embedding_model_id = MODEL

    def __init__(self):
        self.calls = []

    def embed(self, requests):
        self.calls.append([(r.task_type, r.text) for r in requests])
        return [[1.0, 0.1 * len(r.text)] + [0.0] * 766 for r in requests]


class Store:
    """Artifact store as SearchDocumentB reads it. Graph version 2 moves chunk c1 to another module."""

    def __init__(self, root='store-a', rooted=True):
        if rooted:
            self.root = root
        self.counts, self.retrieval_model, self.retrieval_version = Counter(), {}, {}

    def _chunks(self, doc_id):
        return [NS(chunk_id=cid, text=f'{doc_id} {cid}', page=1, section_path=['S'], order_index=i,
                   parent_section_id='s', role='noi_dung') for i, cid in enumerate(('c1', 'c2'))]

    def load_graph(self, doc_id, version):
        self.counts['graph'] += 1
        module_of_c1 = 'm1' if version == 1 else 'm2'
        payload = {'doc_id': doc_id, 'nodes': [],
                   'modules': [{'module_id': 'm1', 'index': 0, 'title': 'A', 'node_ids': []},
                               {'module_id': 'm2', 'index': 1, 'title': 'B', 'node_ids': []}],
                   'chunk_module_map': {'c1': {'module_id': module_of_c1}, 'c2': {'module_id': 'm2'}}}
        return NS(version=version, payload=payload, manifest={'stage': 'stages', 'config': {'chunks_version': 1}})

    def load_latest_graph(self, doc_id):
        return self.load_graph(doc_id, 2)

    def load_chunks(self, doc_id, version):
        return NS(manifest={}, result=NS(chunks=self._chunks(doc_id)))

    def latest_retrieval_version(self, doc_id):
        return self.retrieval_version.get(doc_id, 1)

    def load_latest_retrieval(self, doc_id):
        self.counts['index'] += 1
        documents = [{'chunk_id': c.chunk_id, 'text': c.text, 'vector': [1.0, 0.1 * i] + [0.0] * 766,
                      'doc_id': doc_id, 'section_id': 's', 'page': 1, 'order_index': c.order_index,
                      'section_path': list(c.section_path)} for i, c in enumerate(self._chunks(doc_id))]
        return NS(manifest={'embedding_model_id': self.retrieval_model.get(doc_id, MODEL)},
                  payload={'documents': documents})


def search(store, embedding, doc_id, version, cache, query='một'):
    return SearchDocumentB(store, embedding, None, cache).search(
        query, doc_id=doc_id, graph_version=version, scope='ca_tai_lieu', k=2, allow_spend=True)


def modules(rows):
    return {row['chunk_id']: row['module_id'] for row in rows}


def test_same_graph_and_index_are_loaded_once_and_results_do_not_change():
    store, embedding = Store(), Embedding()
    cache = SearchContextCache()

    first = search(store, embedding, 'book', 1, cache)
    second = search(store, embedding, 'book', 1, cache)

    assert first == second
    assert store.counts == {'graph': 1, 'index': 1}
    assert first == search(Store(rooted=False), Embedding(), 'book', 1, cache)      # uncached path, same rows


def test_another_graph_version_is_loaded_not_served_from_the_first():
    store, embedding, cache = Store(), Embedding(), SearchContextCache()

    assert modules(search(store, embedding, 'book', 1, cache))['c1'] == 'm1'
    assert modules(search(store, embedding, 'book', 2, cache))['c1'] == 'm2'
    assert modules(search(store, embedding, 'book', 1, cache))['c1'] == 'm1'
    assert store.counts['graph'] == 2


def test_new_retrieval_version_invalidates_the_entry():
    store, embedding, cache = Store(), Embedding(), SearchContextCache()
    search(store, embedding, 'book', 1, cache)

    store.retrieval_version['book'] = 2
    store.retrieval_model['book'] = 'other-model'          # the new index was built with another model

    with pytest.raises(ValueError, match='không khớp'):
        search(store, embedding, 'book', 1, cache)
    assert store.counts['index'] == 2


def test_two_documents_with_the_same_versions_never_share_data():
    store, embedding, cache = Store(), Embedding(), SearchContextCache()

    one = search(store, embedding, 'alpha', 1, cache)
    two = search(store, embedding, 'beta', 1, cache)

    assert {row['text'] for row in one} == {'alpha c1', 'alpha c2'}
    assert {row['text'] for row in two} == {'beta c1', 'beta c2'}
    assert store.counts['graph'] == 2


def test_two_stores_with_the_same_ids_never_share_data():
    first, second = Store('store-a'), Store('store-b')
    cache = SearchContextCache()

    search(first, Embedding(), 'book', 1, cache)
    search(second, Embedding(), 'book', 1, cache)

    assert first.counts['graph'] == second.counts['graph'] == 1


def test_store_without_root_is_not_cached():
    store, embedding, cache = Store(rooted=False), Embedding(), SearchContextCache()
    search(store, embedding, 'book', 1, cache)
    search(store, embedding, 'book', 1, cache)
    assert store.counts['graph'] == 2


def test_unpinned_graph_version_is_not_cached():
    store, embedding, cache = Store(), Embedding(), SearchContextCache()
    search(store, embedding, 'book', None, cache)
    search(store, embedding, 'book', None, cache)
    assert store.counts['graph'] == 2


def test_cache_keeps_at_most_max_entries():
    store, embedding, cache = Store(), Embedding(), SearchContextCache(max_entries=1)
    search(store, embedding, 'alpha', 1, cache)
    search(store, embedding, 'beta', 1, cache)
    search(store, embedding, 'alpha', 1, cache)
    assert store.counts['graph'] == 3


def test_a_question_is_embedded_once_across_search_and_concept_lookup():
    delegate, store, cache = Embedding(), Store(), SearchContextCache()
    embedding = CachedQueryEmbedding(delegate)

    search(store, embedding, 'book', 1, cache, query='Song ánh là gì?')
    IndexConcepts(store, embedding, None).lookup({'model_id': MODEL, 'items': []}, 'Song ánh là gì?', allow_spend=True)

    assert delegate.calls == [[('RETRIEVAL_QUERY', 'Song ánh là gì?')]]


def test_query_cache_batches_misses_and_leaves_documents_alone():
    delegate = Embedding()
    embedding = CachedQueryEmbedding(delegate)
    embedding.embed([EmbeddingRequest('a', 'RETRIEVAL_QUERY')])

    vectors = embedding.embed([EmbeddingRequest('a', 'RETRIEVAL_QUERY'), EmbeddingRequest('bb', 'RETRIEVAL_QUERY'),
                               EmbeddingRequest('a', 'RETRIEVAL_DOCUMENT'), EmbeddingRequest('ccc', 'RETRIEVAL_QUERY')])

    assert delegate.calls[1] == [('RETRIEVAL_QUERY', 'bb'), ('RETRIEVAL_DOCUMENT', 'a'), ('RETRIEVAL_QUERY', 'ccc')]
    assert [v[1] for v in vectors] == pytest.approx([0.1, 0.2, 0.1, 0.3])      # answers stay in request order
    assert embedding.last_cached == 1
    embedding.embed([EmbeddingRequest('a', 'RETRIEVAL_DOCUMENT')])
    assert len(delegate.calls) == 3                                              # a document text is sent again


def test_cached_vector_cannot_be_changed_by_the_caller():
    embedding = CachedQueryEmbedding(Embedding())
    first = embedding.embed([EmbeddingRequest('a', 'RETRIEVAL_QUERY')])[0]
    first[0] = 99.0
    assert embedding.embed([EmbeddingRequest('a', 'RETRIEVAL_QUERY')])[0][0] == 1.0


def test_usage_row_prices_only_what_was_sent():
    store, cache, rows = Store(), SearchContextCache(), []
    embedding = CachedQueryEmbedding(Embedding())
    phase = NS(append_usage=rows.append)
    for _ in range(2):
        SearchDocumentB(store, embedding, phase, cache).search(
            'một hai ba', doc_id='book', graph_version=1, scope='ca_tai_lieu', k=2, allow_spend=True)

    assert rows[0]['cost_usd'] > 0 and rows[0]['input_tokens'] > 0
    assert rows[1]['cost_usd'] == 0 and rows[1]['input_tokens'] == 0


def test_json_store_names_latest_retrieval_version_without_loading_it(tmp_path):
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    store = JsonArtifactStore(tmp_path)
    assert store.latest_retrieval_version('book') is None
    for version in (1, 3, 2):
        (tmp_path / 'retrieval' / 'book' / f'v{version}').mkdir(parents=True)
    assert store.latest_retrieval_version('book') == 3


def test_runtime_shares_one_query_embedding_and_builds_the_concept_index_once(tmp_path, monkeypatch):
    import doc2roadmap.composition_phase_b as composition
    from doc2roadmap.config import Settings

    class Gemini(Embedding):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.kwargs = kwargs

    built = []
    monkeypatch.setattr(composition, 'GeminiEmbedding', Gemini)
    monkeypatch.setattr(IndexConcepts, 'execute', lambda self, doc, version, **kw: built.append((doc, version)) or
                        {'model_id': MODEL, 'items': []})
    runtime = composition.PhaseBRuntime(settings=Settings(_env_file=None, artifact_dir=tmp_path), allow_spend=True,
                                        mode='gemini', store_path=tmp_path / 'b.json')
    graph = NS(doc_id='book', graph_version=1, lookup_concept=lambda name: {'matches': []})

    runtime.lookup(graph, 'câu một')
    runtime.lookup(graph, 'câu hai')
    runtime.lookup(NS(doc_id='book', graph_version=2, lookup_concept=lambda name: {'matches': []}), 'câu ba')

    assert runtime.query_embedding() is runtime.query_embedding()
    assert built == [('book', 1), ('book', 2)]
