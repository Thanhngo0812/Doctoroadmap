import pytest

from doc2roadmap.domain.models import DocumentNode
from doc2roadmap.domain.document_structure import chapter_members, code_sequences, structure_profile
from tests.unit.domain.test_section_roles import chunk


@pytest.mark.parametrize('chapter,unit,exercise,result', [
    ('Chapitre','Sujet','Exercices','Proposition'), ('Глава','Тема','Упражнения','Теорема'),
    ('第','主题','练习','定理')])
def test_structure_uses_number_sequences_not_language_words(chapter,unit,exercise,result):
    nodes = []
    def add(kind,text):
        nodes.append(DocumentNode(kind,text,len(nodes),level=1 if kind=='section_header' else None))
    add('section_header','Préliminaires / Введение / 前言')
    add('text','Before the first numbered chapter.')
    for number in (1,2):
        add('section_header',f'{chapter} {number}')
        for j,letter in enumerate('ABC'):
            add('section_header',f'{number}{letter} {unit}')
            for k in range(1,4):
                add('section_header',f'{result} {number}.{j*3+k}')
                add('text','A short statement and explanation.')
            add('section_header',f'{exercise} {number}{letter}')
            add('text','A task for the reader.')
    add('section_header','Répertoire / Указатель / 索引')
    add('text','Alpha 12\nBeta 34\nGamma 56\nDelta 78')
    data = chunk(nodes)
    by_title = {s.title:s for s in data.sections}
    assert by_title['Préliminaires / Введение / 前言'].role == 'mo_dau'
    assert by_title['Répertoire / Указатель / 索引'].role == 'cuoi_sach'
    for number in (1,2):
        for letter in 'ABC':
            parent = by_title[f'{number}{letter} {unit}']
            assert parent.parent_section_id == by_title[f'{chapter} {number}'].section_id
            assert by_title[f'{exercise} {number}{letter}'].parent_section_id == parent.section_id
    assert not any(s.title.startswith(result+' ') for s in data.sections)
    assert f'{result} 1.1' in data.normalized_full_text


def test_single_letter_code_does_not_demote_real_decimal_sections():
    data = chunk([DocumentNode('section_header',t,i*2,level=1)
                  if i%2==0 else DocumentNode('text',t,i*2)
                  for i,t in enumerate(['Chapter 1','Body','1.1 Tập hợp','A real section body.',
                                         '2D convolution','A single code is not a sequence.'])])
    assert '1.1 Tập hợp' in {s.title for s in data.sections}


def test_uppercase_code_sequence_accepts_non_latin_letters():
    nodes = []
    for number in (1,2):
        for title in [f'Глава {number}', *(f'{number}{letter} Тема' for letter in 'ΑΒΓ')]:
            nodes.extend([DocumentNode('section_header',title,len(nodes),level=1),
                          DocumentNode('text','Explanation.',len(nodes)+1)])
    data = chunk(nodes)
    by_title = {s.title:s for s in data.sections}
    assert by_title['1Γ Тема'].parent_section_id == by_title['Глава 1'].section_id


def test_interleaved_exercise_family_is_not_another_chapter_family():
    headings = [(i, title, 1) for i, title in enumerate([
        'Chương 1', 'Bài tập chương 1', 'Chương 2', 'Bài tập chương 2',
        'Chương 3', 'Bài tập chương 3'])]
    assert chapter_members(headings) == {0, 2, 4}


def test_suffix_codes_complete_a_sequence_with_a_missing_primary_heading():
    assert code_sequences(['6A Sujet', 'Exercices 6A', 'Exercices 6B', '6C Sujet']) == {'6A','6B','6C'}


def test_proven_result_family_can_restart_in_a_chapter_without_letter_units():
    nodes = []
    def add(title):
        nodes.extend([DocumentNode('section_header',title,len(nodes),level=1),
                      DocumentNode('text','Short proof.',len(nodes)+1)])
    add('Chapitre 1')
    for j,letter in enumerate('ABC'):
        add(f'1{letter} Sujet')
        for k in range(1,4):
            add(f'1.{j*3+k} Proposition')
    add('Chapitre 2')
    for k in range(1,10):
        add(f'2.{k} Proposition')
    data=chunk(nodes)
    assert not any('Proposition' in s.title for s in data.sections)
    assert '2.9 Proposition' in data.normalized_full_text
    # A real reset per peer is contrary evidence and must leave headings intact.
    for n in nodes:
        if n.node_type=='section_header' and n.text.startswith('1.'):
            n.text='1.1 Proposition'
    assert not structure_profile(nodes)['results']
