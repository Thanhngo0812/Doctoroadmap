"""Separate layout role from content kind; project only explicit caption geometry."""
from copy import deepcopy

import nhan_khoi_r3 as r3

LAYOUT = {'heading', 'body', 'caption', 'footnote', 'list_item', 'table_cell', 'diagram_text', 'unknown'}
CONTENT = {'prose', 'math', 'code', 'mixed', 'unknown'}


def axes(label):
    # A Docling text block need not be prose: formulas/code can be mislabelled.
    return {
        'heading': ('heading', 'unknown'), 'text': ('body', 'unknown'),
        'formula': ('body', 'math'), 'code': ('body', 'code'),
        'caption': ('caption', 'unknown'), 'footnote': ('footnote', 'unknown'),
        'list_item': ('list_item', 'unknown'), 'table': ('table_cell', 'unknown'),
        'diagram_text': ('diagram_text', 'unknown'), 'unknown': ('unknown', 'unknown'),
    }[label]


def caption_nodes(metadata):
    """Return reference nodes only when the whole caption has one known PDF bbox.

    Multipage/partial char spans need dedicated segmentation. Missing origins,
    TOPLEFT boxes without page dimensions, and asset boxes never become labels.
    """
    if metadata.get('schema_version') != 1:
        raise ValueError('Unsupported caption provenance schema')
    nodes, rejected = [], []
    for source in metadata['items']:
        spans = source['provenance']
        reason = None
        if len(spans) != 1:
            reason = 'missing_or_multiple_spans'
        else:
            p = spans[0]
            if p['coord_origin'] != 'BOTTOMLEFT' or p['bbox'] is None or p['page'] is None:
                reason = 'missing_or_unsupported_coordinates'
            elif p.get('charspan') is not None and p['charspan'] != [0, len(source['text'])]:
                reason = 'partial_text_span'
        if reason:
            rejected.append({'source_ref': source['source_ref'], 'reason': reason})
            continue
        nodes.append({'node_type': 'caption', 'text': source['text'], 'page': p['page'], 'bbox': p['bbox'],
                      'source_ref': source['source_ref'], 'owners': deepcopy(source['owners'])})
    return nodes, rejected


def project_captions(rows, metadata):
    nodes, rejected = caption_nodes(metadata)
    aligned = r3.align_rows(rows, nodes)
    labels = []
    for i, result in enumerate(aligned):
        if result['label'] != 'caption':
            continue
        refs = sorted({nodes[m['node']]['source_ref'] for m in result['matches'] if nodes[m['node']]['source_ref'] is not None})
        labels.append({'row': i, 'layout_role': 'caption', 'content_kind': 'unknown',
                       'label_source': 'docling_unreviewed', 'source_refs': refs,
                       'alignment_status': result['status']})
    return {'labels': labels, 'rejected': rejected}


def attach_review(entries, reviews):
    """Keep machine labels and agent proposals separate; no automatic gold promotion."""
    lookup = {e['id']: e for e in entries}
    if len(lookup) != len(entries):
        raise ValueError('Duplicate dataset IDs')
    used = set()
    result = deepcopy(entries)
    output = {e['id']: e for e in result}
    for review in reviews:
        key = review['id']
        if key in used or key not in lookup:
            raise ValueError('Duplicate or unknown review ID')
        used.add(key)
        role, kind = axes(review['proposed_label'])
        output[key]['review_proposal'] = {'layout_role': role, 'content_kind': kind,
                                         'status': 'agent_proposed_not_gold', 'evidence': review['evidence']}
    return result
