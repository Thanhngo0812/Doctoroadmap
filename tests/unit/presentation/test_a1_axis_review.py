import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
from kiem_nhan_r10 import validate


def entry(key='book:1',**extra):
    return dict(id=key,layout_role='table_cell',content_kind='math',confidence='high',evidence='Formula inside a table cell.',**extra)


def test_missing_duplicate_and_unselected_reviews_cannot_pass():
    for reviews in ([],[entry(),entry()],[entry('other:1')]):
        with pytest.raises(ValueError):
            validate(['book:1'],reviews)


def test_axes_are_independent_and_unknown_content_is_allowed():
    assert validate(['book:1'],[entry()]) == {'table_cell/math':1}
    r=entry()
    r['content_kind']='unknown'
    assert validate(['book:1'],[r]) == {'table_cell/unknown':1}


def test_invalid_axis_empty_evidence_and_gold_claim_rejected():
    for field,value in [('layout_role','formula'),('content_kind','heading'),('evidence',' '),('confidence','gold')]:
        r=entry()
        r[field]=value
        with pytest.raises(ValueError):
            validate(['book:1'],[r])
