"""Shared frozen candidate preparation for the next role/grouping ablations."""
from collections import Counter
import joblib
import doi_chung_r9 as r9
import loc_bien_r13 as margin
import caption_hinh_r18 as captions
import hinh_r6 as images
import tach_nhan_cay_r16 as replay

base=r9.base


def prepare(key,d):
    rows,body=margin.prepare_rows(d['rows'])
    name=key if d['book']['split']=='train' else 'full'
    current=base.read(base.ROOT/'tmp/a1-v414-r8c-model/models'/(name+'.json'))
    model,row_record=r9.frozen(base.ROOT/'tmp/doc-nhe-v414',name+'-lightgbm',key,current['train_books'])
    flags=model.predict_proba(base.feature_matrix(rows,body))[:,1]>=.5
    flags[captions.candidates(rows,d['figures'])]=False
    model,pair_record=r9.frozen(base.ROOT/'tmp/a1-v414-r5',name,key,current['train_books'])
    joins=model.predict_proba(r9.pairs.matrix(rows))[:,1]>=.5
    nodes,_=r9.structure.group_rows(rows,d['figures'],d['pages'],flags,prepare_rows=margin.prepare_rows)
    nodes=r9.pairs.regroup(rows,nodes,joins); r9.verify_nodes(rows,d['figures'],nodes)
    assets=base.read(base.ROOT/'tmp/a1-v414-r6-native-resolution/books'/(key+'.json'))['assets']
    for asset in assets:
        if asset['image_id']:
            assert base.digest(base.ROOT/'tmp/a1-v414-r6-native-resolution/images'/(asset['image_id']+'.png'))==asset['image_id']
    settings={k:v for k,v in d['book']['chunk_config'].items() if k in (
        'max_tokens','max_table_tokens','hard_cap_tokens','target_tokens','sentence_overlap',
        'result_min_count','result_max_body_chars','heading_scheme')}
    return rows,nodes,assets,settings,dict(M2f=row_record['model_sha256'],B2=pair_record['model_sha256'])


def evaluate(key,nodes,assets,settings,reference_tree,counter):
    placed,warnings=images.place_figures(nodes,assets)
    assert [n for n in nodes if n['node_type']!='figure']==[n for n in placed if n['node_type']!='figure']
    tree=images.document_tree(placed,warnings)
    output=replay.chunking.chunk_document(tree,key,counter,replay.UnicodeSentenceSplitter(),**settings)
    refs=[r.image_id for c in output.chunks for r in c.image_refs]
    assert Counter(refs)==Counter(a['image_id'] for a in assets if a['image_id'])
    reference=r9.chunks.chunks_of(r9.DocumentTree.from_dict(reference_tree),key,counter,settings)
    return tree,output,dict(leaf_strict=r9.leaf_score(reference,output.chunks),
        heading_strict=r9.heading_score(reference_tree['nodes'],nodes),chunks=len(output.chunks),
        sections=len(output.sections),image_refs=len(refs),formula_refs=sum(len(c.formula_refs) for c in output.chunks))
