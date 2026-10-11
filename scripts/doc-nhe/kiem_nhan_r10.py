"""Validate the proposal batch before attaching any comparison to silver labels."""
from collections import Counter

LAYOUT={'heading','body','caption','footnote','list_item','table_cell','diagram_text','running_margin','unknown'}
CONTENT={'prose','math','code','mixed','unknown'}


def validate(selected_ids,reviews):
    ids=[r['id'] for r in reviews]
    if len(set(ids))!=len(ids) or set(ids)!=set(selected_ids) or len(ids)!=len(selected_ids):
        raise ValueError('Review IDs must match the complete selection exactly once')
    for r in reviews:
        if r['layout_role'] not in LAYOUT or r['content_kind'] not in CONTENT:
            raise ValueError('Invalid independent axis')
        if r['confidence'] not in {'low','medium','high'} or not r['evidence'].strip():
            raise ValueError('Evidence/confidence required; agent proposals cannot assert gold')
    return dict(Counter(r['layout_role']+'/'+r['content_kind'] for r in reviews))


def run():
    import hoc_tieu_de as base
    from nhan_khoi_r3b import axes
    source=base.ROOT/'tmp/pdfs/a1-r10'
    selection=base.read(source/'selection.json')
    path=base.ROOT/'report/v4-14-r10-review-2026-10-07.json'
    review=base.read(path)
    summary=validate([e['id'] for e in selection['entries']],review['entries'])
    assert review['status']=='complete_selected_batch_agent_proposals_not_gold'
    assert selection['script_sha256']==base.digest(base.ROOT/'scripts/doc-nhe/xem_nhan_r10.py')
    assert selection['protocol_sha256']==base.digest(base.ROOT/'report/v4-14-r10-giao-thuc-2026-10-07.md')
    pinned={b['id']:b for b in base.manifest(base.ROOT/'tmp/doc-nhe-v414')['books']}
    rendered=[]
    for i,e in enumerate(selection['entries']):
        prefix=source/f'{i:02d}-{e["book"]}-{e["page"]}'
        meta=base.read(prefix.with_suffix('.json'))
        assert meta['id']==e['id'] and meta['page']==e['page']
        assert meta['source_sha256']==pinned[e['book']]['pdf_sha256']
        assert meta['render_sha256']==base.digest(prefix.with_suffix('.png'))
        rendered.append(meta)
    # Read silver keys only after the complete independent-axis proposals are saved.
    silver={e['id']:e for e in base.read(base.ROOT/'tmp/a1-v414-r3/review-key.json')}
    comparisons=[]
    for r in review['entries']:
        s=silver[r['id']]
        role,kind=axes(s['label'])
        comparisons.append(dict(id=r['id'],partition=s['role'],proposal=r,silver_label=s['label'],
                                silver_axes=[role,kind],layout_disagreement=(role!=r['layout_role']) if role!='unknown' else None,
                                content_disagreement=(kind!=r['content_kind']) if kind!='unknown' and r['content_kind']!='unknown' else None))
    output=base.ROOT/'report/v4-14-r10-so-do-2026-10-07.json'
    assert not output.exists(), 'Do not overwrite a measurement'
    base.write(output,dict(api_usd=0,review_sha256=base.digest(path),selection_sha256=base.digest(source/'selection.json'),
                           code_sha256=base.digest(__file__),axes_counts=summary,rendered=rendered,comparisons=comparisons,
                           selected=len(review['entries']),total_reviewed_r3_r10=len(review['entries'])+14,remaining=271-len(review['entries'])-14))
    print('reviewed',len(review['entries']),'layout disagreements',sum(c['layout_disagreement'] is True for c in comparisons),
          'unknown silver',sum(c['layout_disagreement'] is None for c in comparisons))


if __name__=='__main__':
    run()
