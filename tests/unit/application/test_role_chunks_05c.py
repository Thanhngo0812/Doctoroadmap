"""Role refreshes on synthetic version histories; all writes stay in tmp_path."""
from copy import deepcopy

import pytest

from doc2roadmap.domain.canonical import digest
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from tests.unit.application.test_a4_pipeline import fixture_store
from tests.unit.application.test_canonical_gop import DOC, gop
from tests.unit.application.test_label_chunk_roles import stored


def save_roles(store, base, key, role='noi_dung', origin=None, source_hash=None):
    value = deepcopy(base.result)
    for chunk in value.chunks:
        chunk.role = role
    return store.save_chunks(base.result.doc_id, source_hash or base.manifest['source_hash'], key,
        base.manifest['config'], base.manifest['parse_version'], value,
        manifest_fields={'semantic_roles': True,
                         'roles_from_chunks_version': base.version if origin is None else origin})


def test_labeled_a3_input_uses_latest_relabel_from_its_original_chunks(tmp_path):
    store, base = stored(tmp_path)
    first = save_roles(store, base, 'first', 'mo_dau')
    newer = save_roles(store, base, 'newer')
    before = {p: p.read_bytes() for p in tmp_path.rglob('*.json')}
    selected = store.load_role_chunks('roles', first.version)
    assert (base.version, first.version, newer.version) == (1, 2, 3)
    assert selected.version == newer.version
    assert all(chunk.role == 'noi_dung' for chunk in selected.result.chunks)
    assert before == {p: p.read_bytes() for p in tmp_path.rglob('*.json')}


def test_unlabeled_05b_input_still_uses_labels_from_that_version(tmp_path):
    store, base = stored(tmp_path)
    first = save_roles(store, base, 'first', 'mo_dau')
    assert store.load_role_chunks('roles', base.version).version == first.version
    newer = save_roles(store, base, 'newer')
    assert store.load_role_chunks('roles', base.version).version == newer.version


def test_no_newer_sibling_returns_requested_labels_not_an_older_sibling(tmp_path):
    store, base = stored(tmp_path)
    save_roles(store, base, 'older', 'mo_dau')
    current = save_roles(store, base, 'current')
    assert store.load_role_chunks('roles', current.version).version == current.version
    unrelated = save_roles(store, base, 'unrelated', 'bai_tap', origin=99)
    assert unrelated.version > current.version
    assert store.load_role_chunks('roles', current.version).version == current.version


@pytest.mark.parametrize('field', ['chunk_id', 'text', 'char_start', 'char_end', 'source_hash'])
@pytest.mark.parametrize('labeled_input', [False, True])
def test_newer_labels_cannot_change_chunk_identity_or_source(tmp_path, field, labeled_input):
    store, base = stored(tmp_path)
    first = save_roles(store, base, 'first')
    corrupt = save_roles(store, base, 'corrupt')
    if field == 'source_hash':
        manifest = {**corrupt.manifest, 'source_hash': 'different-source'}
        store._write(corrupt.path / 'manifest.json', manifest)
    else:
        chunks = [chunk.to_dict() for chunk in corrupt.result.chunks]
        chunks[0][field] = chunks[0][field] + 1 if field.startswith('char_') else 'changed'
        store._write(corrupt.path / 'chunks.json', chunks)
    with pytest.raises(ValueError, match='identity or source'):
        store.load_role_chunks('roles', first.version if labeled_input else base.version)


def test_canonical_and_cli_dry_run_follow_new_sibling_without_invalidating_a3(tmp_path, monkeypatch, capsys):
    import json
    from doc2roadmap.presentation.cli.main import main

    fixture = fixture_store(tmp_path / 'fixture')
    candidates = fixture.load_latest_candidates(DOC)
    original = fixture.load_chunks(DOC, candidates.manifest['upstream_version'])
    store = JsonArtifactStore(tmp_path / 'store')
    base = store.save_chunks(DOC, original.manifest['source_hash'], original.manifest['config_hash'],
        original.manifest['config'], original.manifest['parse_version'], original.result)
    first = save_roles(store, base, 'first-roles', 'mo_dau')
    a3 = store.save_candidates(DOC, candidates.manifest['source_hash'], candidates.manifest['config_hash'],
        candidates.manifest['config'], candidates.payload, upstream_version=first.version)
    candidate_bytes = {p: p.read_bytes() for p in a3.path.glob('*.json')}
    chunk_bytes = {p: p.read_bytes() for p in base.path.glob('*.json')}
    _, model, use_case = gop(tmp_path, store=store)
    old, _ = use_case.execute(DOC)
    assert not model.anchor_calls and old.manifest['config']['anchor_chunks_version'] == first.version
    cached = use_case.plan(DOC)['anchor'].to_dict()
    assert cached['status'] == 'reused' and f'anchor_chunks_version={first.version}' in cached['note']
    newer = save_roles(store, base, 'new-roles')
    before = {p: p.read_bytes() for p in (tmp_path / 'store').rglob('*.json')}
    monkeypatch.setattr('doc2roadmap.presentation.cli.main.build_artifact_store', lambda: store)
    monkeypatch.setattr('doc2roadmap.presentation.cli.main.build_canonical', lambda **kwargs: use_case)
    monkeypatch.setattr('doc2roadmap.presentation.cli.main.load_gold', lambda *a, **k: {'documents': {DOC: {}}})
    calls = len(model.calls), len(model.anchor_calls)
    assert main(['a4', '--doc-id', DOC, '--gold', 'fake.json', '--dry-run']) == 0
    anchor_plan = json.loads(capsys.readouterr().out)['phases']['anchor']
    assert anchor_plan['status'] == 'unknown'
    assert f'anchor_chunks_version={newer.version}' in anchor_plan['note']
    assert calls == (len(model.calls), len(model.anchor_calls))
    assert before == {p: p.read_bytes() for p in (tmp_path / 'store').rglob('*.json')}
    changed, reused = use_case.execute(DOC)
    assert not reused and changed.manifest['config']['anchor_chunks_version'] == newer.version
    assert changed.manifest['config_hash'] != old.manifest['config_hash']
    assert model.anchor_calls and len(model.calls) == calls[0]  # merge/description logs reused
    assert any(n.get('teaching_status') == 'taught' for n in changed.payload['nodes'])
    assert candidate_bytes == {p: p.read_bytes() for p in a3.path.glob('*.json')}
    assert chunk_bytes == {p: p.read_bytes() for p in base.path.glob('*.json')}
    assert digest(store.load_latest_candidates(DOC).payload) == digest(candidates.payload)
