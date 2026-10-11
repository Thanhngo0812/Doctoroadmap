import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
from can_sach_r11 import training_arrays


def sample():
    return {'a':{'X':np.arange(12).reshape(-1,1),'y':np.array([0]*9+[1]*2+[-1])},
            'b':{'X':np.arange(3).reshape(-1,1)+20,'y':np.array([0,1,1])},
            'held':{'X':np.array([[99]]),'y':np.array([1])}}


def test_every_training_book_and_its_classes_have_equal_mass():
    x,y,w,names=training_arrays(sample(),heldout='held')
    assert names==['a','b'] and len(x)==14
    assert w.sum()==pytest.approx(14)
    assert w[:11].sum()==pytest.approx(7)
    assert w[11:].sum()==pytest.approx(7)
    for indexes in (np.arange(11),np.arange(11,14)):
        for label in (0,1):
            assert w[indexes][y[indexes]==label].sum()==pytest.approx(3.5)


def test_unknown_and_heldout_cannot_change_training_weights():
    d=sample()
    before=training_arrays(d,heldout='held')
    d['held']={'X':np.zeros((100,1)),'y':np.zeros(100)}
    after=training_arrays(d,heldout='held')
    for a,b in zip(before[:3],after[:3],strict=True):
        np.testing.assert_array_equal(a,b)
    assert 11 not in before[0][:,0] and 99 not in before[0][:,0]


def test_single_class_book_keeps_equal_book_mass():
    d=sample()
    d['b']['y']=np.zeros(3,dtype=int)
    _,_,w,_=training_arrays(d,heldout='held')
    assert w[:11].sum()==pytest.approx(w[11:].sum())
