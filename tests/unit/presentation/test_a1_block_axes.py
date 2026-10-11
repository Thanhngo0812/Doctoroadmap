import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts/doc-nhe'))
import nhan_khoi_r3b as r3b


def test_layout_does_not_imply_prose_and_diagram_text_is_not_a_caption():
    assert r3b.axes('heading') == ('heading', 'unknown')
    assert r3b.axes('text') == ('body', 'unknown')
    assert r3b.axes('code') == ('body', 'code')
    assert r3b.axes('diagram_text') == ('diagram_text', 'unknown')


def metadata(spans):
    return {'schema_version': 1, 'items': [{'text': 'Figure 1', 'source_ref': '#/texts/0', 'owners': [], 'provenance': spans}]}


def span(origin='BOTTOMLEFT', chars=None):
    return {'page': 1, 'bbox': [0, 100, 100, 90], 'coord_origin': origin, 'charspan': chars}


def test_caption_projection_requires_its_own_known_geometry():
    rows = [{'text': 'Figure 1', 'page': 1, 'x0': 0, 'x1': 100, 'top': 100, 'bottom': 90}]
    good = r3b.project_captions(rows, metadata([span(chars=[0, 8])]))
    assert len(good['labels']) == 1
    assert good['labels'][0]['source_refs'] == ['#/texts/0']
    for spans in ([], [span(), span()], [span('TOPLEFT')], [span(chars=[0, 3])]):
        rejected = r3b.project_captions(rows, metadata(spans))
        assert rejected['labels'] == [] and rejected['rejected']


def test_proposals_never_replace_machine_label_or_become_gold():
    entry = {'id': 'book:1', 'label': 'formula'}
    reviewed = r3b.attach_review([entry], [{'id': 'book:1', 'proposed_label': 'code', 'evidence': 'SQL syntax on rendered page'}])[0]
    assert entry == {'id': 'book:1', 'label': 'formula'}
    assert reviewed['label'] == 'formula'
    assert reviewed['review_proposal']['content_kind'] == 'code'
    assert reviewed['review_proposal']['status'] == 'agent_proposed_not_gold'
    with pytest.raises(ValueError):
        r3b.attach_review([entry], [{'id': 'other:1', 'proposed_label': 'code', 'evidence': ''}])
