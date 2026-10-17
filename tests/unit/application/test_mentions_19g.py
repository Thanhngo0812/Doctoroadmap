"""19g: frozen matching/ranking without query vectors in manifests."""
import json
import random
from pathlib import Path

import pytest

from doc2roadmap.application.use_cases.build_mentions import BuildMentions, dense_mentions
from doc2roadmap.domain import mentions
from doc2roadmap.domain.canonical import digest
from tests.legacy_v3 import real_upstream
from tests.unit.application.test_build_mentions import Embedding, Store


def test_real_fixture_preserves_matches_rankings_and_dense_scores(tmp_path):
    expected = json.loads(Path('tests/fixtures/mentions/baocao-canhan-before-19g.json').read_text(encoding='utf-8'))
    store, upstream = real_upstream(tmp_path)
    nodes = upstream.payload['nodes']
    chunks = store.load_latest_chunks('baocao-canhan').result.chunks
    vectors = list(json.loads(Path('tests/fixtures/a4/baocao-canhan/name-vectors.json').read_text(encoding='utf-8'))['vectors'].values())
    node_vectors = {node['node_id']: vectors[i] for i, node in enumerate(nodes) if node.get('learnable')}
    chunk_vectors = {chunk.chunk_id: vectors[i % len(vectors)] for i, chunk in enumerate(chunks)}
    assert digest([nodes, node_vectors, chunk_vectors]) == expected['input_hash']
    common, exact, legacy = mentions.document_mentions(nodes, chunks, threshold=.5)
    assert sorted(common) == expected['common_names']
    assert {key: sorted(value) for key, value in exact.items()} == expected['exact']
    assert {key: sorted(value) for key, value in legacy.items()} == expected['legacy']
    dense, scores = dense_mentions(node_vectors, chunk_vectors, top_k=3, min_z=0.)
    ranks = {node: sorted(chunk_vectors, key=lambda chunk: (-scores[node, chunk], chunk)) for node in node_vectors}
    assert digest(ranks) == expected['ranks_hash']
    mention_map = mentions.build_mention_map(nodes, chunks, exact, dense, scores)
    assert digest(mention_map) == '00c96ea9b8c46e8585678c32a32ab57b7eb9eea390f25ec9646ac2f3c90ce68d'
    clean = {chunk: {node: {key: value for key, value in row.items() if key != 'dense_z'}
                     for node, row in rows.items()} for chunk, rows in mention_map.items()}
    assert digest(clean) == expected['map_without_z_hash']
    for chunk, rows in expected['selected_z'].items():
        for node, value in rows.items():
            assert mention_map[chunk][node]['dense_z'] == pytest.approx(value, abs=1e-12, rel=0)


def test_shared_scan_keeps_unicode_legacy_and_longest_match_and_normalizes_chunks_once(monkeypatch):
    from tests.unit.domain.test_mentions import node, chunk
    nodes = [node('long', 'Kỹ thuật'), node('short', 'Kỹ'), node('cjk', '概念'), node('symbol', 'μ')]
    chunks = [chunk('one', 'Kĩ thuật và các概念ở đây dùng μ.'), chunk('two', 'Không có tên nào.')]
    common = mentions.document_common_names(nodes, chunks, threshold=.75)
    expected = [mentions.exact_mentions(nodes, chunks, common_names=common, _legacy=legacy) for legacy in (False, True)]
    normalize, calls = mentions._mention_normalize, []
    def count(value):
        if value in {row.text for row in chunks}:
            calls.append(value)
        return normalize(value)
    monkeypatch.setattr(mentions, '_mention_normalize', count)
    actual_common, exact, legacy = mentions.document_mentions(nodes, chunks, threshold=.75)
    assert actual_common == common and [exact, legacy] == expected
    assert exact == {'one': {'long', 'cjk'}} and legacy == {'one': {'long'}}
    assert calls == [row.text for row in chunks]


def test_nearly_constant_cosines_preserve_python_scores_and_id_tie_break():
    rng = random.Random(19)
    for _ in range(6):
        values = [rng.random() for _ in range(16)]
        chunks = {str(i): rng.sample(values, len(values)) for i in range(4)}
        selected, scores = dense_mentions({'n': [1.] * 16}, chunks, top_k=1, min_z=0.)
        assert selected == {'0': {'n'}}
        assert scores == {('n', str(i)): 0. for i in range(4)}


class CacheStore(Store):
    def save_graph(self, *args, **kwargs):
        artifact = super().save_graph(*args, **kwargs)
        artifact.manifest.update(kwargs['manifest_fields'])
        return artifact


class CountingEmbedding(Embedding):
    def embed(self, requests):
        self.calls.extend(requests)
        return [[1., 0.] if request.text.startswith('Alpha') else [0., 1.] for request in requests]


def test_mentions_do_not_store_query_vectors_and_keep_stage_cache():
    store, embedding = CacheStore(), CountingEmbedding()
    first, _ = BuildMentions(store, embedding).execute('doc')
    first_hash = digest(first.payload['mention_map'])
    assert first.manifest['source_hash'] == '1926a3252fb2c604eb4cf18a903400c6ac68f4abb67109ab0776c9c8220f5ca8'
    assert first.manifest['config_hash'] == '163034bb595d75159776ddb32dd7339c478e38a1a8a806fb1a78913ac4aed090'
    assert len(embedding.calls) == 2
    assert 'query_embedding_cache' not in first.payload
    assert 'query_embedding_cache' not in first.manifest
    cached, reused = BuildMentions(store, embedding).execute('doc')
    assert reused and cached is first and len(embedding.calls) == 2
    # A semantic config change reruns queries; no per-query cache is persisted.
    second, reused = BuildMentions(store, embedding, dense_top_k=4).execute('doc')
    assert not reused and len(embedding.calls) == 4
    assert digest(second.payload['mention_map']) == first_hash
    assert first.manifest['config_hash'] != second.manifest['config_hash']
    assert second.payload['stats']['embedding_request_count'] == 2
    assert 'query_embedding_cache' not in second.manifest


def test_explicit_upstream_never_reads_query_history_even_when_planning():
    store, embedding = CacheStore(), CountingEmbedding()
    def forbidden(*args):
        pytest.fail('query-cache removal must not traverse old graph artifacts')
    store.load_latest_graph = store.load_graph = forbidden
    stage = BuildMentions(store, embedding)
    plan = stage.plan('doc', upstream=store.graph)
    assert plan.remaining_items == 2 and not embedding.calls and store.saved is None
    artifact, _ = stage.execute('doc', upstream=store.graph)
    assert len(embedding.calls) == 2
    assert artifact.payload['stats']['embedding_request_count'] == 2
    assert 'query_embedding_cache' not in artifact.manifest
    assert all(request.task_type == 'RETRIEVAL_QUERY' for request in embedding.calls)


def test_cluster_semantic_vectors_are_not_query_cache():
    store, embedding = CacheStore(), CountingEmbedding()
    store.graph.payload['node_vectors'] = {'a': [0., 1.], 'b': [1., 0.]}
    store.graph.manifest['config'] = {'embedding_task': 'SEMANTIC_SIMILARITY',
                                     'embedding_model_id': embedding.embedding_model_id}
    artifact, _ = BuildMentions(store, embedding).execute('doc')
    assert len(embedding.calls) == 2
    assert artifact.payload['mention_map']['c1']['a']['dense_z'] == 1.
