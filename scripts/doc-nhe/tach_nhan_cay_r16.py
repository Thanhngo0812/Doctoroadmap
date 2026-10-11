"""Research-only replay of heading acceptance, separate from hierarchy."""
from dataclasses import asdict
from unittest.mock import patch
import hoc_tieu_de as base
import doc2roadmap.domain.chunking as chunking
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter
from doc2roadmap.domain.normalization import normalize_text
import so_chunk_doc_nhe as chunks
import doc_nhe as light


def project(parents, keep):
    assert len(parents)==len(keep)
    indexes={old:new for new,old in enumerate(i for i,k in enumerate(keep) if k)}
    result=[]
    for i in indexes:
        p=parents[i]
        while p!=-1 and not keep[p]: p=parents[p]
        result.append(-1 if p==-1 else indexes[p])
    return result


def capture(tree, key, counter, settings):
    heads=[n for n in sorted(tree.nodes,key=lambda n:n.reading_order) if n.node_type in chunking.HEADING_TYPES]
    assert all(normalize_text(n.text) for n in heads)
    keep=[]
    original=chunking._false_heading_reason
    def record(*args,**kwargs):
        reason=original(*args,**kwargs)
        assert args[0]==normalize_text(heads[len(keep)].text)
        keep.append(reason is None)
        return reason
    with patch.object(chunking,'_false_heading_reason',record):
        output=chunking.chunk_document(tree,key,counter,UnicodeSentenceSplitter(),**settings)
    assert len(keep)==len(heads) and sum(keep)==len(output.sections)-1
    mapping={s.section_id:i-1 for i,s in enumerate(output.sections)}
    parents=[mapping[s.parent_section_id] for s in output.sections[1:]]
    return output,keep,parents


def declared(tree, keep, parents):
    candidate=DocumentTree.from_dict(tree.to_dict())
    heads=[n for n in sorted(candidate.nodes,key=lambda n:n.reading_order) if n.node_type in chunking.HEADING_TYPES]
    assert len(heads)==len(keep) and sum(keep)==len(parents)
    depths=[]
    for node,accepted in zip(heads,keep):
        if not accepted:
            node.node_type='text'
        else:
            p=parents[len(depths)]
            depths.append(1 if p==-1 else depths[p]+1)
            node.level=depths[-1]
    return candidate


def path_score(reference, candidate):
    sets=[chunks.words(c.text) for c in candidate]
    hits=eligible=0
    for c in reference:
        words=chunks.words(c.text)
        options=[(len(words & sets[j])/max(len(words | sets[j]),1),-j)
                 for j,n in enumerate(candidate) if abs((c.page or 0)-(n.page or 0))<=2]
        if not options: continue
        similarity,neg=max(options)
        if similarity<.5: continue
        eligible+=1
        a=[light.words(s) for s in c.section_path]
        b=[light.words(s) for s in candidate[-neg].section_path]
        hits+=bool(a and all(a) and a==b)
    return dict(hits=hits,eligible=eligible,total=len(reference),share=hits/max(len(reference),1))
