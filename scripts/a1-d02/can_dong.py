"""Align actual chunker output to canonical PDFium rows via page/bbox provenance."""
from collections import defaultdict
import time
from unittest.mock import patch

from doc2roadmap.domain import chunking
from doc2roadmap.domain.normalization import normalize_text
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter

ROLE={'title':'tieu_de','section_header':'tieu_de','paragraph':'than_bai','text':'than_bai',
      'list_item':'danh_sach','formula':'cong_thuc','table':'bang','caption':'chu_thich_hinh',
      'page_header':'dau_trang','page_footer':'chan_trang','footnote':'chu_thich_cuoi_trang',
      'code':'ma_lenh','figure':'chu_trong_hinh'}


def overlap(a,b):
    area=max(0,a[2]-a[0])*max(0,a[1]-a[3])
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[1],b[1])-max(a[3],b[3]))
    return intersection/area if area else 0.


def chunk_and_align(tree,lines,key,counter,settings,*,source_ids=None,raw_roles=None,evaluation_excluded=(),on_chunked=None):
    nodes=sorted(tree.nodes,key=lambda n:n.reading_order)
    heads=[n for n in nodes if n.node_type in chunking.HEADING_TYPES and normalize_text(n.text)]
    kept=[];blocks=[];guard=chunking._false_heading_reason;factory=chunking._LeafBlock
    def record_guard(*args,**kwargs):
        value=guard(*args,**kwargs);kept.append(value is None);return value
    def record_block(*args,**kwargs):
        value=factory(*args,**kwargs);blocks.append(value);return value
    with patch.object(chunking,'_false_heading_reason',record_guard),patch.object(chunking,'_LeafBlock',record_block):
        output=chunking.chunk_document(tree,key,counter,UnicodeSentenceSplitter(),**settings)
    pipeline_peak=on_chunked() if on_chunked else None
    alignment_started=time.perf_counter()
    if len(kept)!=len(heads) or sum(kept)!=len(output.sections)-1:
        raise ValueError('Chunker heading acceptance changed; inspect alignment instrumentation')
    accepted={id(n):s for n,s in zip((n for n,k in zip(heads,kept) if k),output.sections[1:])}
    page_nodes=defaultdict(list)
    for i,node in enumerate(nodes):
        if node.bbox:page_nodes[node.page].append((i,node))
    row_to_node={};unmatched=[];ambiguous=[]
    for line in lines:
        if source_ids is not None:
            choices=[i for i in source_ids if line['id'] in source_ids[i]]
            if len(choices)>1:raise ValueError('One canonical row belongs to multiple S1 nodes')
        else:
            hits=[(overlap(line['bbox'],node.bbox),-(node.bbox[2]-node.bbox[0])*(node.bbox[1]-node.bbox[3]),i)
                  for i,node in page_nodes[line['trang']] if node.node_type!='figure']
            hits=[h for h in hits if h[0]>=.5]
            choices=[max(hits)[2]] if hits else []
            if len(hits)>1:ambiguous.append(line['id'])
        if choices:row_to_node[line['id']]=choices[0]
        else:unmatched.append(line['id'])
    node_lines=defaultdict(list)
    for line in lines:
        if line['id'] in row_to_node:node_lines[row_to_node[line['id']]].append(line)
    owner={id(block.node):block.owner.section_id for block in blocks}
    root=output.sections[0].section_id
    section_for=lambda sid:None if sid==root else sid
    predicted={};heading_records=[];orders=defaultdict(list)
    for i,node in enumerate(nodes):
        rows=node_lines[i];section=accepted.get(id(node));kind=(raw_roles or {}).get(i,node.node_type)
        if section:
            heading_records.append(dict(id=section.section_id,dong=[r['id'] for r in rows],
                cha=section_for(section.parent_section_id),cap=section.level,text=section.title))
        for line in rows:
            role='tieu_de' if section else ROLE.get(kind,'khac')
            if node.node_type in chunking.HEADING_TYPES and not section:role='than_bai'
            predicted[line['id']]=dict(role=role,leaf=section.section_id if section else section_for(owner.get(id(node),root)))
            if role not in {'dau_trang','chan_trang','so_trang','chu_trong_hinh'}:orders[str(line['trang'])].append(line['id'])
    # Instrumented block offsets refer to actual normalized_full_text, including overlap splits.
    node_index={id(n):i for i,n in enumerate(nodes)};spans=defaultdict(list);unaligned_text=[]
    for block in blocks:
        rows=node_lines[node_index[id(block.node)]];cursor=0
        for line in rows:
            text=normalize_text(line['text']);position=block.text.find(text,cursor)
            if position<0:
                unaligned_text.append(line['id']);continue
            spans[line['id']].append((block.char_start+position,block.char_start+position+len(text)))
            cursor=position+len(text)
    chunks=[dict(id=c.chunk_id,page=c.page,heading=section_for(c.parent_section_id),
                 dong=[key for key,ranges in spans.items() if any(a<c.char_end and c.char_start<b for a,b in ranges)])
            for c in output.chunks]
    return output,dict(headings=heading_records,lines=predicted,reading_order=dict(orders),chunks=chunks,pipeline_peak_rss_mb=pipeline_peak,
        evaluation_excluded=list(evaluation_excluded),alignment=dict(unmatched=unmatched,ambiguous=ambiguous,
        unaligned_chunk_text=sorted(set(unaligned_text)),source_lines=len(lines),aligned_lines=len(predicted),
        seconds=time.perf_counter()-alignment_started))
