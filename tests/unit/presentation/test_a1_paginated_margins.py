import sys
from pathlib import Path

sys.path.insert(0,str(Path('scripts/doc-nhe').resolve()))
import loc_le_r8c as margin
from tests.unit.presentation.test_a1_margin_filter import edge


def test_running_text_with_page_number_at_either_end_removed():
    rows=[]
    for page in range(5,13):
        rows += [edge('Some book 2005 Page '+str(page-4),page,40,28),
                 edge(str(page+1)+' Matrix and mappings',page)]
    assert margin.prepare_rows(rows)[0] == []


def test_variable_chapter_numbers_without_dense_pagination_survive():
    rows=[edge('Chapter '+str(i),i*10) for i in range(1,8)]
    rows += [edge('5 3',3,60,48),edge('1436,3',8,60,48)]
    assert margin.prepare_rows(rows)[0] == rows


def test_same_sequence_outside_margin_and_changed_style_are_not_removed():
    rows=[edge('Text '+str(i),i) for i in range(1,7)]
    body=edge('Text 3',3,600,580)
    title=edge('Text 3',3)
    title.update(size=24,bold=True)
    rows += [body,title]
    assert margin.prepare_rows(rows)[0] == [body,title]


def test_number_not_following_pages_and_short_series_retained():
    rows=[edge('Chapter '+str(i),2*i) for i in range(1,8)]
    rows += [edge('Other '+str(i),i) for i in range(1,5)]
    assert margin.prepare_rows(rows)[0] == rows
