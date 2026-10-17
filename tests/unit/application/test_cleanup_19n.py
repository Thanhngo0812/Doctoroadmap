import importlib
import pkgutil

import pytest

from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.domain.canonical import digest
from tests.unit.application.test_a4_pipeline import embedding, fixture_store
from tests.unit.application.test_canonical_gop import AnchorModel, DOC, gop


@pytest.mark.parametrize('mode,payload_hash,config_hash', [
    ('names', 'd3a5fd15b70878f6e42ed20a225165b1ef88a695084674e68a8342b4e96f9bf0',
     '0f968b149375e842e990a03993380848c69857f470df919d7ca6b1fffffb86dc'),
    ('prepare', '69d80e1fc461769b331605dcf38959c71443b1f5587616694d0e5e5548ddc94f',
     'bc5429b5fb6118264e183854789da967fa1270030cd8fc1c379c2a2889a5454f'),
    ('gop', '9de0e3c923b11b6bfccf4b6302ea1f2fa58b50207334ec532ed4827044c08462', None),
])
def test_cleanup_preserves_frozen_default_and_names_only_outputs(tmp_path, mode, payload_hash, config_hash):
    if mode == 'gop':
        _, _, stage = gop(tmp_path)
    else:
        stage = Canonicalize(fixture_store(tmp_path), embedding() if mode == 'prepare' else None)
    artifact, _ = stage.execute(DOC)
    assert digest(artifact.payload) == payload_hash
    if config_hash:
        assert artifact.manifest['config_hash'] == config_hash


def test_retired_full_v3_cannot_be_constructed():
    model = AnchorModel()
    with pytest.raises(TypeError, match='upstream_chain'):
        Canonicalize(object(), object(), reasoning=CanonicalReasoning(model, model), upstream_chain='v3')


@pytest.mark.parametrize('stop', ['provenance', 'teaching', 'identity'])
def test_cli_rejects_retired_stop_before_reading_artifacts(stop, capsys):
    from doc2roadmap.presentation.cli.main import _parser
    with pytest.raises(SystemExit) as caught:
        _parser().parse_args(['roadmap', '--doc-id', 'book', '--stop-after', stop])
    assert caught.value.code == 2 and stop in capsys.readouterr().err


def test_every_product_module_imports_after_cleanup():
    import doc2roadmap
    for info in pkgutil.walk_packages(doc2roadmap.__path__, doc2roadmap.__name__ + '.'):
        importlib.import_module(info.name)


def test_shared_verbatim_guard_still_rejects_changed_quotes():
    from doc2roadmap.domain.quotes import quote_is_verbatim
    from doc2roadmap.application.phase_b.common import quote_is_verbatim as phase_b_quote
    assert quote_is_verbatim('Alpha   là một.','Alpha là một. Đoạn khác.')
    assert not quote_is_verbatim('Alpha là hai.','Alpha là một.')
    assert not quote_is_verbatim('', 'Alpha là một.')
    assert phase_b_quote('Alpha là một.', 'Alpha là một.')
    assert not phase_b_quote('Alpha là hai.', 'Alpha là một.')


def test_a8_still_reads_frozen_v3_identity_artifact(tmp_path):
    from types import SimpleNamespace
    from tests.legacy_v3 import legacy_store
    from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges

    class Model:
        model_id = 'fixture-model'
        def start_session(self, prompt):
            return self
        def ask_json(self, prompt, *, response_schema):
            return SimpleNamespace(payload={'edges': [], 'flags': []})

    store, identity, _ = legacy_store(tmp_path)
    assert identity.payload['identity_map']
    result, _ = BuildMainEdges(store, Model()).execute(DOC, upstream=identity)
    assert result.payload['main_complete']
    assert result.payload['identity_map'] == identity.payload['identity_map']
    assert result.payload['completed_main_sessions']


def test_shared_review_loader_preserves_human_input_contract(tmp_path):
    import json
    from doc2roadmap.application.identity_review import load_identity_review
    path = tmp_path / 'review.json'
    path.write_text(json.dumps({'doc_id': DOC, 'decisions': [
        {'left': 'a', 'right': 'b', 'decision': 'Không gộp'}]}, ensure_ascii=False), encoding='utf-8')
    assert load_identity_review(path, doc_id=DOC) == {frozenset(('a', 'b')): 'Không gộp'}
    with pytest.raises(ValueError, match='không phải'):
        load_identity_review(path, doc_id='other')


def test_scorers_still_read_frozen_v3_and_apply_its_identity_map(tmp_path):
    import json
    from tests.legacy_v3 import legacy_store
    from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
    from doc2roadmap.application.use_cases.a8_gold import annotation_scope, list_chapters
    from doc2roadmap.application.use_cases.a8_score import score_from_store, score_roadmap_order

    store, identity, _ = legacy_store(tmp_path)
    roadmap, _ = BuildRoadmap(store).execute(DOC, upstream=identity)
    canonical = store.load_latest_canonical(DOC)
    chunks = store.load_chunks(DOC, roadmap.manifest['config']['chunks_version'])
    chapter = next(row['section_id'] for row in list_chapters(canonical.payload['nodes'],
        chunks.result.sections, chunks.result.chunks) if row['targets'])
    scope = annotation_scope(DOC, canonical.version, canonical.payload['nodes'], chunks.result.sections,
                             chunks.result.chunks, chapter=chapter)
    gold = tmp_path / 'gold.json'
    value = {'doc_id': DOC, 'canonical_version': canonical.version, 'chapter_level': 1,
             'chapter': scope['chapter'], 'concept_hash': scope['concept_hash'],
             'targets': [row['node_id'] for row in scope['concepts']], 'edges': []}
    gold.write_text(json.dumps(value), encoding='utf-8')
    assert score_from_store(store, DOC, roadmap.path / 'graph.json', [gold], samples=0,
                            remap_gold_ids=True)['gold']['edges'] == 0
    alias, representative = next(iter(roadmap.payload['identity_map'].items()))
    value['edges'] = [{'prerequisite': alias, 'target': representative}]
    gold.write_text(json.dumps(value), encoding='utf-8')
    before = gold.read_bytes()
    report = score_roadmap_order(roadmap.path / 'graph.json', [gold])
    assert report['identity_dropped_gold_edges'] == 1 and report['gold_edge_count'] == 0
    assert gold.read_bytes() == before
