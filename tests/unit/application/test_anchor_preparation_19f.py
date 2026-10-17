from types import SimpleNamespace

from doc2roadmap.application.use_cases.canonical_anchors import prepare_anchors
from doc2roadmap.domain import anchors
from doc2roadmap.domain.canonical import digest
from tests.legacy_v3 import real_upstream
from tests.unit.application.test_canonical_gop import DOC, gop


def test_real_fixture_anchor_candidates_keep_the_frozen_before_hash(tmp_path):
    store, upstream = real_upstream(tmp_path)
    chunks = store.load_chunks(DOC, upstream.manifest['config']['chunks_version']).result.chunks
    core = prepare_anchors(upstream.payload['nodes'], chunks)
    assert digest(core.candidates_of) == 'f6207a4d9dd6f34490168538ed21727a97f6b399fd35e8143a3a5d0b1f48338b'
    assert digest(core.outside_of) == 'd941a4dd2cc4641e0b80499fd5d47c7657568b54ef9eab7f2be0cc7f14173271'


def test_document_text_is_normalized_once_and_nested_names_stay_independent(monkeypatch):
    text = 'không gian v12 có một cơ sở và không gian con có một cơ sở.'
    chunk = SimpleNamespace(chunk_id='body', text=text, order_index=0, role='noi_dung', section_path=[])
    nodes = [{'node_id': name, 'name': name, 'learnable': True}
             for name in ('Không gian', 'Không gian con', '𝑉_12')]
    calls = []
    original = anchors.unicodedata.normalize
    def counted(form, value):
        if value == text:
            calls.append(form)
        return original(form, value)
    monkeypatch.setattr(anchors.unicodedata, 'normalize', counted)
    core = prepare_anchors(nodes, [chunk])
    assert all(core.candidates_of[node['node_id']] for node in nodes)
    assert calls.count('NFKC') == 1
    assert calls.count('NFC') == 1  # normalized source text is passed through normalize_text once
    assert calls.count('NFD') == 2


def test_canonical_manifest_measures_cpu_without_putting_time_into_cache_or_payload(tmp_path):
    _, _, stage = gop(tmp_path)
    artifact, _ = stage.execute(DOC)
    phases = artifact.manifest['phase_measurements']
    assert {'build_nodes', 'additional_nominations', 'nomination_graph', 'prepare_anchors'} <= phases.keys()
    assert all(phases[name]['runtime_seconds'] >= 0 for name in phases)
    assert 'runtime_seconds' not in str(artifact.manifest['config'])
    assert 'runtime_seconds' not in str(artifact.payload)
