import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path('scripts/doc-nhe').resolve()))
import hoc_r4 as r4
from tests.unit.presentation.test_heading_learning import row


def test_features_do_not_use_labels_or_book_identity_and_do_not_cross_pages():
    rows = [row('item_value = f(x);'), row('Một dòng', page=2)]
    before = r4.feature_matrix(rows, 12)
    for r in rows:
        r.update(label=1, gold='heading', book='some-publisher')
    np.testing.assert_array_equal(before, r4.feature_matrix(rows, 12))
    assert before.shape == (2, 133)
    np.testing.assert_array_equal(before[1, [r4.FEATURES.index('prev_' + n) for n in r4.EXTRA]], np.zeros(20))
    assert np.isfinite(before).all()


def test_morphology_preserves_repetition_and_operator_signal():
    a, b = r4.morphology('x + x'), r4.morphology('x x x')
    assert a[r4.EXTRA.index('operators')] > b[r4.EXTRA.index('operators')]
    assert r4.morphology('thing_name = f(x);')[r4.EXTRA.index('semicolon')] > 0
    assert r4.morphology('Vitamin K')[r4.EXTRA.index('operators')] == 0


def assert_style_distinguishes_common_body_from_rare_style():
    rows = [row('A long body text ' * 8, page=i) for i in range(1, 5)]
    special = row('A heading', page=4)
    special['font'], special['bold'] = 'Times-Bold', True
    rows.append(special)
    result = r4.feature_matrix(rows, 12)
    assert result[0, r4.FEATURES.index('self_style_share')] == pytest.approx(.8)
    assert result[-1, r4.FEATURES.index('self_style_share')] == pytest.approx(.2)
    assert result[0, r4.FEATURES.index('self_style_long_share')] == 1
    assert result[-1, r4.FEATURES.index('self_style_long_share')] == 0


def test_style_signal_and_mutation(monkeypatch):
    assert_style_distinguishes_common_body_from_rare_style()
    real = r4.feature_matrix
    def broken(rows, body):
        result = real(rows, body)
        result[:, r4.FEATURES.index('self_style_share')] = 0
        return result
    monkeypatch.setattr(r4, 'feature_matrix', broken)
    with pytest.raises(AssertionError):
        assert_style_distinguishes_common_body_from_rare_style()


def test_publisher_split_and_unknown_exclusion_are_observable():
    data = {k: {'book': {'publisher': p}, 'X': np.array([[i], [i+100]]), 'y': np.array([1, -1])}
            for i, (k, p) in enumerate((('a', 'P'), ('b', 'P'), ('c', 'Q')))}
    jobs = dict(r4.splits(sorted(data), data))
    assert jobs['publisher-00'] == ('a', 'b')
    x, y, names = r4.base.training_arrays(data, jobs['publisher-00'])
    assert names == ['c'] and x.tolist() == [[2]] and y.tolist() == [1]
    assert r4.binary_r3([{'label': s} for s in ('heading', 'formula', 'unknown', 'diagram_text')]).tolist() == [1, 0, -1, -1]


def test_fit_roundtrip_with_frozen_config(tmp_path):
    joblib = pytest.importorskip('joblib')
    pytest.importorskip('lightgbm')
    x = np.repeat(np.arange(200)[:, None], len(r4.FEATURES), axis=1)
    y = (np.arange(200) > 99).astype(int)
    model = r4.fit(x, y, 'E1')
    joblib.dump(model, tmp_path / 'model.joblib')
    np.testing.assert_array_equal(model.predict_proba(x), joblib.load(tmp_path / 'model.joblib').predict_proba(x))
    assert (model.predict(x) == y).mean() > .95
