import sys
from pathlib import Path
import pytest
pytest.importorskip('joblib')
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
from do_cay_day_du_r15 import outline_score


def row(text): return dict(page=1,text=text)


def test_unmatched_predicted_parent_counts_as_error_not_root():
    entries=[dict(row=row('Child'),parent=-1)]
    score=outline_score([row('Extra'),row('Child')],[-1,0],entries)
    assert score['matched']==1 and score['parent_hits']==0 and score['unmatched_parent_errors']==1


def test_duplicate_heading_not_matched_twice_and_missing_reference_in_denominator():
    entries=[dict(row=row('Root'),parent=-1),dict(row=row('Child'),parent=0)]
    score=outline_score([row('Root'),row('Root')],[-1,-1],entries)
    assert score['matched']==0 and score['coverage']==0 and score['reference_headings']==2
    score=outline_score([row('Child')],[-1],entries)
    assert score['parent_hits']==1 and score['joint_hits_per_reference']==.5
