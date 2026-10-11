import importlib.util
from pathlib import Path

import numpy as np
import pytest


def module():
    spec = importlib.util.spec_from_file_location('hoc_tieu_de', Path('scripts/doc-nhe/hoc_tieu_de.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def row(text, page=1, **kwargs):
    return dict(text=text, page=page, size=12, chars=len(text), tokens=len(text.split()),
                height=800, width=600, x0=50, x1=400, top=700, bottom=688,
                bold=False, italic=0, font='Times', math=0, mono=0,
                symbol_share=0, single=0, viet=1, **kwargs)


def node(text, kind='section_header', page=1, box=None):
    return dict(text=text, node_type=kind, page=page, bbox=box or [45, 710, 410, 680])


def test_unmatched_and_conflicting_rows_remain_unknown():
    m = module()
    rows = [row('Chương 1 Đại số'), row('Đại số', page=2), row('1'), row('Không được căn'),
            row('Một đoạn văn'), row('Hai nhãn'), row('Lƣu ý')]
    tree = {'nodes': [node('Chương 1 Đại số'), node('Một đoạn văn dài hơn', 'text'),
                      node('Hai nhãn'), node('Hai nhãn', 'text'), node('Lưu ý')]}
    y, detail = m.silver_labels(rows, tree)
    assert y.tolist() == [1, -1, -1, -1, 0, -1, 1]
    assert detail['counts']['unmatched'] == 3 and detail['counts']['ambiguous'] == 1


def test_alignment_uses_same_page_geometry():
    y, _ = module().silver_labels([row('Đại số')], {'nodes': [node('Đại số', box=[45, 510, 410, 480])]})
    assert y.tolist() == [-1]


def test_features_ignore_labels_and_cross_page_neighbors():
    m = module()
    rows = [row('Một dòng'), row('Tiêu đề', page=2)]
    before = m.feature_matrix(rows, 12)
    rows[0]['label'] = 1
    rows[1]['label'] = 0
    after = m.feature_matrix(rows, 12)
    np.testing.assert_array_equal(before, after)
    previous = [i for i, name in enumerate(m.FEATURE_NAMES) if name.startswith('prev_')]
    np.testing.assert_array_equal(after[1, previous], np.zeros(len(previous)))
    assert after[1, m.FEATURE_NAMES.index('has_prev')] == 0
    assert np.isfinite(after).all()


def test_lobo_excludes_heldout_and_unknown_labels():
    m = module()
    data = {name: {'X': np.array([[value], [value+1]]), 'y': np.array([1, -1])}
            for name, value in (('a', 10), ('b', 20), ('c', 30))}
    x, y, names = m.training_arrays(data, heldout='b')
    assert names == ['a', 'c']
    assert x[:, 0].tolist() == [10, 30] and y.tolist() == [1, 1]


def test_manifest_rejects_non_allowlisted_paths(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'read', lambda path: {'books': [
        {'file': 'train/allowed.pdf', 'split': 'train'},
        {'file': 'test/forbidden.pdf', 'split': 'test'},
    ]})
    assert m.allowed_path(m.ROOT / 'document-data/train/allowed.pdf') == (
        m.ROOT / 'document-data/train/allowed.pdf').resolve()
    for path in ('document-data/test/forbidden.pdf', 'document-data/train/../../doc-1.pdf', tmp_path / 'book.pdf'):
        with pytest.raises(ValueError):
            m.allowed_path(path)
    with pytest.raises(ValueError):
        m.allowed_path('doc-2.pdf', external=True)


def test_model_roundtrip_and_dataset_fingerprint(tmp_path, monkeypatch):
    m = module()
    # The ML environment is optional for the production unit suite.
    joblib = pytest.importorskip('joblib')
    pytest.importorskip('sklearn')
    x = np.tile(np.arange(20)[:, None], (1, len(m.FEATURE_NAMES)))
    y = np.arange(20) > 9
    model = m.fit_model(x, y, 'logistic')
    joblib.dump(model, tmp_path / 'model.joblib')
    np.testing.assert_array_equal(m.probability(model, x, 'logistic'), m.probability(joblib.load(tmp_path / 'model.joblib'), x, 'logistic'))
    m.write(tmp_path / 'datasets/a.json', {'fingerprint': 'old'})
    monkeypatch.setattr(m, 'code_fingerprint', lambda: 'new')
    with pytest.raises(ValueError, match='fingerprint'):
        m.load_data(tmp_path, {'books': [{'id': 'a'}]})


def test_manifest_rejects_changed_pinned_input(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    monkeypatch.setattr(m, 'allowed_path', lambda path, **kwargs: path)
    book = {'id': 'a', 'split': 'train'}
    for name in ('pdf', 'tree', 'chunk_manifest'):
        book[name] = name + '.json'
        m.write(tmp_path / book[name], {'version': 1})
        book[name + '_sha256'] = m.digest(tmp_path / book[name])
    m.write(tmp_path / 'run/manifest.json', {'books': [book]})
    assert m.manifest(tmp_path / 'run')['books'][0]['id'] == 'a'
    m.write(tmp_path / book['tree'], {'version': 2})
    with pytest.raises(ValueError, match='Pinned input changed'):
        m.manifest(tmp_path / 'run')


def test_review_gate_requires_complete_matching_sample(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path('scripts/doc-nhe').resolve()))
    import chay
    m = module()
    m.write(tmp_path / 'alignment-review-80.json', list(range(80)))
    with pytest.raises(ValueError, match='Review the 80'):
        chay.reviewed(tmp_path)
    review = {'sample_sha256': m.digest(tmp_path / 'alignment-review-80.json'),
              'reviews': [{'sample': i} for i in range(1, 81)]}
    m.write(tmp_path / 'alignment-review-80-reviewed.json', review)
    chay.reviewed(tmp_path)
    review['reviews'].pop()
    m.write(tmp_path / 'alignment-review-80-reviewed.json', review)
    with pytest.raises(ValueError, match='incomplete'):
        chay.reviewed(tmp_path)
    review['reviews'].append({'sample': 80})
    review['sample_sha256'] = 'different'
    m.write(tmp_path / 'alignment-review-80-reviewed.json', review)
    with pytest.raises(ValueError, match='different sample'):
        chay.reviewed(tmp_path)


def test_lightgbm_fixed_seed_is_repeatable():
    pytest.importorskip('lightgbm')
    m = module()
    rng = np.random.default_rng(42)
    x = rng.normal(size=(160, len(m.FEATURE_NAMES)))
    y = (x[:, 0] + x[:, 1] > 0).astype(int)
    first = m.fit_model(x, y, 'lightgbm')
    second = m.fit_model(x, y, 'lightgbm')
    np.testing.assert_array_equal(m.probability(first, x, 'lightgbm'), m.probability(second, x, 'lightgbm'))
