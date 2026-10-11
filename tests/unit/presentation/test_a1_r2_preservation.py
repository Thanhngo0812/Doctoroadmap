"""Independent observable checks for A1 research, including old-behavior RED."""
import importlib.util
from itertools import product
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('a1_r2', ROOT / 'scripts/doc-nhe/cau_truc_r2.py')
R2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R2)
sys.path.insert(0, str(ROOT / 'scripts/doc-nhe'))
import do_r2 as replay


def row(text, top=600, font='Times'):
    return R2.baseline.describe([R2.baseline.Char(ch, 20+i*6, top-12, 26+i*6, top, font, 400)
                                 for i, ch in enumerate(text)], 1, 800, 600)


def compact(nodes):
    return ''.join(''.join(n['text'].split()) for n in nodes)


def assert_content_contract(parser):
    rows = [row('x x', 600), row('x x', 582), row('G A A T T C G G', 564)]
    expected = 'xxxxGAATTCGG'
    for flags in product((False, True), repeat=3):
        nodes, _ = parser(rows, [], 1, flags)
        assert compact(nodes) == expected


def test_regression_was_red_on_old_group_cleanup():
    with pytest.raises(AssertionError):
        assert_content_contract(R2.baseline.group_rows)


def test_heading_decisions_cannot_change_repeated_letters():
    assert_content_contract(R2.group_rows)


def test_literal_code_and_legacy_symbols_preserved():
    assert R2.normalize_row('<!-- x x x --> ƣ \uf061') == '<!-- x x x --> ư α'


def test_protected_types_with_independent_text_expectations():
    rows = [row('x = x + x', font='CMMI'), row('Hình 1. Minh hoạ', 540),
            row('print(value)', 480, font='Courier'), row('Nội dung thông thường', 420)]
    old, _ = R2.baseline.group_rows(rows, [], 1, [True]*4)
    assert [n['node_type'] for n in old] == ['section_header']*4
    new, _ = R2.group_rows(rows, [], 1, [True]*4, protect_types=True)
    assert [(n['node_type'], n['text']) for n in new] == [
        ('formula', 'x = x + x'), ('caption', 'Hình 1. Minh hoạ'),
        ('text', 'print(value)'), ('section_header', 'Nội dung thông thường')]


def test_provenance_is_partition_and_bbox_encloses_every_source():
    rows = [row('Nội dung thứ nhất', 600), row('nội dung tiếp theo', 582)]
    nodes, _ = R2.group_rows(rows, [], 1, [False, False])
    assert len(nodes) == 1  # actually exercise merge, not single-row nodes
    assert nodes[0]['source_rows'] == [0, 1]
    assert nodes[0]['bbox'] == [20, 600, max(r['x1'] for r in rows), 570]
    assert nodes[0]['text'] == 'Nội dung thứ nhất nội dung tiếp theo'


def test_filter_and_figures_remain_auditable_without_mutating_input():
    rows = [row('123', 25), row('Nội dung', 600)]
    figure = {'page': 1, 'bbox': (10, 100, 60, 200), 'top': 200}
    nodes, stats = R2.group_rows(rows, [figure], 1, [False])
    assert stats['repeated_lines_removed'] == 1
    assert [i for n in nodes for i in n['source_rows']] == [0]
    assert nodes[-1]['bbox'] == [10, 200, 60, 100]  # adapter contract: left, top, right, bottom
    assert nodes[-1]['source_figure'] == 0
    assert rows[0]['text'] == '123'
    with pytest.raises(ValueError, match='prediction'):
        R2.group_rows(rows, [], 1, [False, True])


@pytest.mark.parametrize('damage', ['text', 'duplicate', 'bbox', 'page', 'figure'])
def test_auditor_rejects_corrupted_output_even_with_success_flag(damage):
    rows = [row('Nội dung', 600)]
    figures = [{'page': 1, 'bbox': (10, 100, 60, 200), 'top': 200}]
    nodes, _ = R2.group_rows(rows, figures, 1, [False])
    replay.verify_nodes(rows, figures, nodes)
    if damage == 'text':
        nodes[0]['text'] += 'x'
    elif damage == 'duplicate':
        nodes[0]['source_rows'] += [0]
    elif damage == 'bbox':
        nodes[0]['bbox'][2] -= 1
    elif damage == 'page':
        nodes[0]['page'] = 2
    else:
        nodes.pop()
    nodes[0]['source_partition_text_bbox_figures_verified'] = True
    with pytest.raises(AssertionError):
        replay.verify_nodes(rows, figures, nodes)


@pytest.mark.parametrize('damage', ['in_sample', 'fingerprint', 'threshold', 'length'])
def test_frozen_prediction_rejects_invalid_provenance(damage):
    record = {'fingerprint': 'frozen', 'train_books': ['train'], 'heldout': ['held'],
              'threshold': .5, 'predictions': {'held': {'probability': [.2, .8]}}}
    assert replay.validate_prediction(record, 'held', 'frozen', 2) == [False, True]
    if damage == 'in_sample':
        record['train_books'].append('held')
    elif damage == 'fingerprint':
        record['fingerprint'] = 'changed'
    elif damage == 'threshold':
        record['threshold'] = .6
    else:
        record['predictions']['held']['probability'].pop()
    with pytest.raises(ValueError, match='prediction'):
        replay.validate_prediction(record, 'held', 'frozen', 2)
