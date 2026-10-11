import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/doc-nhe'))
spec = importlib.util.spec_from_file_location('block_labels', ROOT / 'scripts/doc-nhe/nhan_khoi_r3.py')
r3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r3)


def row(text, left=0, right=100, page=1):
    return dict(text=text, x0=left, x1=right, top=100, bottom=90, page=page)


def node(text, kind='text', box=None, page=1):
    return dict(text=text, node_type=kind, bbox=box or [0, 100, 100, 90], page=page)


def label(text, nodes):
    return r3.align_rows([row(text)], nodes)[0]['label']


def test_alignment_preserves_operator_case_and_repeated_symbols():
    assert label('x + x', [node('x - x', 'formula')]) == 'unknown'
    assert label('G G G', [node('G', 'formula')]) == 'unknown'
    assert label('X', [node('x', 'formula')]) == 'unknown'
    assert label('x + x', [node('x + x', 'formula')]) == 'formula'


def test_nearby_column_and_other_page_do_not_label_same_text():
    assert label('Vector space', [node('Vector space', 'section_header', [90, 100, 190, 90])]) == 'unknown'
    assert label('Vector space', [node('Vector space', 'section_header', page=2)]) == 'unknown'
    assert label('Vector space', [node('Vector space', 'section_header', [49, 100, 55, 90])]) == 'unknown'


def test_mixed_heading_and_body_never_label_entire_row_heading():
    assert label('Heading and body', [node('Heading', 'section_header'), node('Heading and body')]) == 'unknown'
    assert label('Heading', [node('Heading', 'section_header'), node('Heading', 'formula')]) == 'unknown'


def test_exact_multiline_and_raw_formula_sources():
    assert label('Vector space', [node('Chapter 1 Vector space continued', 'section_header')]) == 'heading'
    formula = node('[formula]', 'formula')
    formula['raw_text'] = 'x = y'
    assert label('x = y', [formula]) == 'formula'
    table = node('[table]', 'table')
    table['table_rows'] = [['G G G', 'C']]
    assert label('G G G', [table]) == 'table'


def test_absent_or_invalid_geometry_never_yields_a_label():
    absent = node('Vector space', 'section_header')
    absent['bbox'] = None
    assert label('Vector space', [absent]) == 'unknown'
    with pytest.raises(ValueError, match='bbox'):
        label('Vector space', [node('Vector space', 'section_header', [0, 90, 100, 100])])


def test_same_role_nodes_keep_all_provenance_not_a_fake_unique_parent():
    result = r3.align_rows([row('Long heading')], [node('Long heading', 'title'), node('Long heading', 'section_header')])[0]
    assert result['label'] == 'heading'
    assert [hit['node'] for hit in result['matches']] == [0, 1]


def test_sampling_is_reproducible_no_fallback_no_page_split_leakage():
    entries = [dict(id=f'b:{i}', book='b', row=i, page=i // 3 + 1,
                    label='text' if i % 2 else 'unknown') for i in range(40)]
    first = r3.sample_review(entries)
    assert first == r3.sample_review(list(reversed(entries)))
    assert len(first) == 6  # two text, four unknown, never fill absent classes
    roles = {}
    for entry in entries:
        roles.setdefault(entry['page'], set()).add(r3.review_role(entry['book'], entry['page']))
    assert all(len(v) == 1 for v in roles.values())


def test_output_cannot_overwrite_baseline_or_production(tmp_path):
    baseline = r3.ROOT / 'tmp/doc-nhe-v414'
    for path in (baseline, baseline / 'child', r3.ROOT / 'artifacts', r3.ROOT / 'tmp'):
        with pytest.raises(ValueError):
            r3.validate_output(path, baseline)
    r3.validate_output(r3.ROOT / 'tmp/a1-r3-test', baseline)


def test_old_word_only_alignment_fails_the_operator_contract():
    formula = node('[formula]', 'formula')
    formula['raw_text'] = 'x - x'
    old, _ = r3.learn.silver_labels([row('x + x')], {'nodes': [formula]})
    assert old.tolist() == [0]  # demonstrates the false match in frozen v1
    with pytest.raises(AssertionError):
        assert old.tolist() == [-1]
    assert label('x + x', [node('x - x', 'formula')]) == 'unknown'


def test_overlap_guard_mutation_is_detected(monkeypatch):
    monkeypatch.setattr(r3, 'coverage', lambda row, box: 1.0)
    with pytest.raises(AssertionError):
        test_nearby_column_and_other_page_do_not_label_same_text()


def test_operator_guard_mutation_is_detected(monkeypatch):
    monkeypatch.setattr(r3, 'tokens', r3.learn.tokens)
    with pytest.raises(AssertionError):
        test_alignment_preserves_operator_case_and_repeated_symbols()
