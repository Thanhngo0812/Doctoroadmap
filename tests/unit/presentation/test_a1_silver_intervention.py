import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
pytest.importorskip('joblib')
from doi_chung_nhan_r12 import intervene


def test_intervention_changes_known_rows_only_and_preserves_inputs():
    labels=np.array([1,0,-1,-1])
    predicted=np.array([False,True,False,True])
    np.testing.assert_array_equal(intervene(labels,predicted),[True,False,False,True])
    np.testing.assert_array_equal(labels,[1,0,-1,-1])
    np.testing.assert_array_equal(predicted,[False,True,False,True])


def test_intervention_rejects_shape_broadcasting_and_invalid_labels():
    for labels,predicted in [([1],[True,False]),([[1],[0]],[True,False]),([2],[True])]:
        with pytest.raises(ValueError):
            intervene(labels,predicted)
