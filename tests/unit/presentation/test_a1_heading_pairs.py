import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path('scripts/doc-nhe').resolve()))
import noi_tieu_de_r5 as pairs
from do_r2 import verify_nodes
from tests.unit.presentation.test_heading_learning import row


def pair():
    a, b = row('A MAIN HEADING'), row('A subheading')
    a.update(top=700, bottom=688, font='Times-Bold', bold=True)
    b.update(top=684, bottom=672, font='Times', bold=False)
    return a, b


def test_old_rule_false_join_is_reproduced_and_typography_separates():
    a, b = pair()
    assert pairs.rule(a, b)  # old behavior really reaches the problematic branch
    assert not pairs.rule(a, b, typography=True)
    b.update(font=a['font'], bold=a['bold'])
    assert pairs.rule(a, b, typography=True)
    b['page'] = 2
    assert not pairs.rule(a, b, typography=True)


def test_unknown_geometry_and_ambiguous_alignment_not_negative_training():
    a, b = pair()
    def label(nodes, kind='heading'):
        return {'label': kind, 'matches': [{'node': n} for n in nodes]}
    assert pairs.pair_labels([a,b], [label([1]),label([1])]).tolist() == [-1,1]
    assert pairs.pair_labels([a,b], [label([1]),label([2])]).tolist() == [-1,0]
    assert pairs.pair_labels([a,b], [label([1]),label([1,2])]).tolist() == [-1,-1]
    assert pairs.pair_labels([a,b], [label([1]),label([], 'unknown')]).tolist() == [-1,-1]
    b['page'] = 2
    assert pairs.pair_labels([a,b], [label([1]),label([1])]).tolist() == [-1,-1]


def test_features_do_not_read_labels_and_have_no_cross_page_neighbors():
    a,b = pair()
    before = pairs.matrix([a,b])
    a['label'], b['gold'] = 1, 0
    np.testing.assert_array_equal(before, pairs.matrix([a,b]))
    assert np.isfinite(before).all()
    b['page'] = 2
    np.testing.assert_array_equal(pairs.matrix([a,b]), np.zeros((2,len(pairs.FEATURES))))


def test_regroup_only_changes_boundaries_and_auditor_catches_loss():
    a,b = pair()
    rows = [a,b]
    # Existing R2 may already have merged these into one heading.
    node = dict(node_type='section_header', text=a['text']+' '+b['text'], page=1, x0=50,
                level=2, source_rows=[0,1], bbox=[50,700,400,672])
    separate = pairs.regroup(rows, [node], [False,False])
    assert len(separate) == 2
    verify_nodes(rows, [], separate)
    together = pairs.regroup(rows, separate, [False,True])
    assert together == [node]
    verify_nodes(rows, [], together)
    together[0]['source_rows'].pop()
    with pytest.raises(AssertionError):
        verify_nodes(rows, [], together)
    with pytest.raises(ValueError):
        pairs.regroup(rows, [node], [True])


def test_chapter_label_can_join_its_same_style_title_but_not_a_new_number():
    a,b = pair()
    a['text'], b['text'] = 'Chương 1', 'ĐẠI SỐ'
    b.update(font=a['font'], bold=a['bold'])
    assert not pairs.rule(a,b)
    assert pairs.rule(a,b,typography=True)
    b['text'] = '1.1 Không gian vectơ'
    assert not pairs.rule(a,b,typography=True)
