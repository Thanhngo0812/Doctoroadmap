import importlib.util
from pathlib import Path
from types import SimpleNamespace


def module():
    spec = importlib.util.spec_from_file_location('heading_eval', Path('scripts/doc-nhe/danh_gia.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def node(text, page=1):
    return {'node_type': 'section_header', 'text': text, 'page': page}


def test_heading_match_rejects_wrong_page():
    assert module().heading_score([node('Tổng quan', 1)], [node('Tổng quan', 9)])['recall'] == 0


def test_heading_match_uses_token_boundaries():
    assert module().heading_score([node('11 Tổng quan')], [node('1')])['precision'] == 0


def test_heading_match_is_one_to_one():
    score = module().heading_score([node('Tổng quan')], [node('Tổng quan')] * 3)
    assert score['precision'] == 1 / 3 and score['recall'] == 1


def test_leaf_match_requires_content_overlap():
    a = SimpleNamespace(text='alpha', page=1, section_path=['Tổng quan'])
    b = SimpleNamespace(text='beta', page=1, section_path=['Tổng quan'])
    assert module().leaf_score([a], [b])['share'] == 0
