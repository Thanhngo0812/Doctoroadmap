import sys
from pathlib import Path
sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import loc_bien_r13 as margin
from tests.unit.presentation.test_a1_margin_filter import edge


def series():
    rows=[]
    for p in range(1,13):
        rows.extend([edge('Database lecture notes '+str(p),p,910,897),
                     edge('Changing chapter '+str(p),p,870,857),
                     edge('Body text '+str(p*p),p,500,487)])
    for r in rows:
        r['height']=1000
    return rows


def test_outer_paginated_title_outside_fixed_band_removed():
    rows=series()
    expected=[r for i,r in enumerate(rows) if i%3]
    assert margin.prepare_rows(rows)[0]==expected
    assert margin.prepare_rows(expected)[0]==expected


def test_interior_sequence_and_tightly_attached_line_survive():
    rows=series()
    for r in rows:
        if r['text'].startswith('Changing'):
            r.update(top=896,bottom=882)
    assert margin.prepare_rows(rows)[0]==rows


def test_short_sparse_wrong_offset_and_numeric_formula_survive():
    rows=series()[:27]
    assert margin.prepare_rows(rows)[0]==rows
    rows=series()
    for r in rows:
        r['page']*=3
    assert margin.prepare_rows(rows)[0]==rows
    rows=[edge('5 3',p,910,897) for p in range(1,13)]
    for r in rows:
        r['height']=1000
    assert margin.prepare_rows(rows)[0]==rows


def test_interior_same_style_is_not_dropped_with_edge_series():
    rows=series()
    interior=edge('Database lecture notes 5',5,600,587)
    interior['height']=1000
    rows.append(interior)
    assert interior in margin.prepare_rows(rows)[0]
