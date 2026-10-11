import sys
from pathlib import Path
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import so_muc_r17 as h3


def row(text,size=12): return dict(text=text,size=size,bold=True,font='test',italic=False,page=1)


def test_mixed_roman_decimal_prefix_gives_nested_parent():
    rows=[row('III Topic'),row('III.1 Subtopic'),row('III.1.1 Detail'),row('III.2 Other'),row('IV Next')]
    assert h3.rule(rows)==[-1,0,1,0,-1]


def test_c_is_letter_in_alphabet_series_but_i_ii_iii_remain_roman():
    rows=[row('A. First'),row('B. Second'),row('C. Third'),row('I- One',11),row('II- Two',11),row('III- Three',11)]
    assert h3.rule(rows)==[-1,-1,-1,2,2,2]
