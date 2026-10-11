import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import loc_le_r8 as margin
import hoc_tieu_de as base
from tests.unit.presentation.test_heading_learning import row


def edge(text,page,top=760,bottom=745):
    r=row(text,page)
    r.update(top=top,bottom=bottom)
    return r


def assert_structural_headings_survive(prepare):
    rows=[edge('Chương '+str(i),i*10) for i in (1,2,3)]
    kept,_=prepare(rows)
    assert kept==rows


def test_old_digit_mask_really_deletes_chapter_headings():
    with pytest.raises(AssertionError):
        assert_structural_headings_survive(base.light.prepare_rows)
    assert_structural_headings_survive(margin.prepare_rows)


def test_matrix_rows_and_formula_decimal_not_page_numbers():
    rows=[edge(s,i,60,48) for i,s in enumerate(('5 3','2 5','1436,3','0 1 4/3'),1)]
    with pytest.raises(AssertionError):
        assert base.light.prepare_rows(rows)[0]==rows
    assert margin.prepare_rows(rows)[0]==rows


def test_exact_running_headers_and_consistent_page_numbers_removed():
    rows=[]
    for page in range(4,9):
        rows.extend([edge('My running textbook title',page),edge(str(page-3),page,40,28),row('Body sentence',page)])
    kept,_=margin.prepare_rows(rows)
    assert [r['text'] for r in kept]==['Body sentence']*5


def test_repeated_sparse_heading_and_single_digit_formula_are_retained():
    rows=[edge('Review questions',p) for p in (5,35,80)]
    rows+=[edge('1',p,60,48) for p in range(1,6)]
    assert margin.prepare_rows(rows)[0]==rows


def test_header_style_does_not_delete_same_text_chapter_title():
    rows=[edge('Chapter One',p) for p in range(1,6)]
    title=edge('Chapter One',1)
    title.update(size=24,font='Times-Bold',bold=True)
    rows.insert(0,title)
    assert margin.prepare_rows(rows)[0]==[title]


def test_grouping_does_not_apply_old_filter_again_after_new_filter():
    import cau_truc_r2 as structure
    from do_r2 import verify_nodes
    rows=[edge('Chương '+str(i),i*10) for i in (1,2,3)]
    for r in rows:
        r['letters']=sum(c.isalpha() for c in r['text'])
    nodes,_=structure.group_rows(rows,[],30,[True]*3,prepare_rows=margin.prepare_rows)
    assert [n['text'] for n in nodes]==[r['text'] for r in rows]
    verify_nodes(rows,[],nodes)
