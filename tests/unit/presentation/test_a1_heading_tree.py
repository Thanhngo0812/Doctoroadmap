import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import cay_tieu_de_r14 as tree
from tests.unit.presentation.test_heading_learning import row


def test_decoder_cannot_reopen_closed_subtree():
    preferences=[{-1:1},{0:2},{-1:3},{0:100,2:2}]
    def score(rows,i,candidates,parents):
        return [preferences[i].get(p,0) for p in candidates]
    predicted=tree.decode([row(str(i),1) for i in range(4)],score)
    assert predicted==[-1,0,-1,2]
    assert tree.metrics(predicted,predicted)['parent_accuracy']==1


def test_missing_parent_is_projected_to_nearest_retained_ancestor():
    marks=[dict(level=0,matching_rows=[0]),dict(level=1,matching_rows=[]),dict(level=2,matching_rows=[1])]
    entries=tree.project_outline(marks,[row('Root',1),row('Child',1)])
    assert [e['parent'] for e in entries]==[-1,0]
    assert entries[1]['native_parent']==1 and entries[1]['bookmark']==2


def test_group_split_and_features_do_not_read_target_labels():
    marks=[dict(level=0,matching_rows=[0]),dict(level=1,matching_rows=[1]),dict(level=0,matching_rows=[2])]
    entries=tree.project_outline(marks,[row('Chapter 1',1),row('1. Topic',1),row('Chapter 2',3)])
    train=tree.subset(entries,{0}); hold=tree.subset(entries,{2})
    assert set(tree.training_pairs(train)[2]).isdisjoint(e['bookmark'] for e in hold)
    rows=[e['row'] for e in entries]
    a=tree.pair_features(rows,1,0,[-1])
    entries[1]['parent']=-1
    np.testing.assert_array_equal(a,tree.pair_features(rows,1,0,[-1]))


def test_tree_metric_rejects_future_cycle_or_closed_branch():
    for parents in ([0],[-1,2,1],[-1,0,-1,0]):
        with pytest.raises(ValueError): tree.metrics(parents,parents)
    assert tree.metrics([-1,0,1],[-1,0,0])['ancestor_f1']==pytest.approx(.8)


def test_decoder_rejects_nan_and_wrong_score_shape():
    for values in ([float('nan')],[1,2]):
        with pytest.raises(ValueError): tree.decode([row('Heading',1)],lambda *args:values)


def test_number_signature_not_word_prefix_and_decimal_parent():
    assert tree.signature('Introduction')==(0,())
    assert tree.signature('Vitamin K')==(0,())
    assert tree.signature('1.2.3 Topic')==(4,(1,2,3))
