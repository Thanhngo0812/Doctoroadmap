"""D-02 line-ID metrics; missing predictions stay in metric denominators."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics

from kiem_nhan_d02 import read_jsonl, validate,load_labels

BODY={'than_bai','danh_sach'}
SKIP={'dau_trang','chan_trang','so_trang'}
ROLE_GROUPS={'bo_dau_chan_so_trang':SKIP,'cong_thuc':{'cong_thuc'},'bang':{'bang'},
             'chu_thich_hinh':{'chu_thich_hinh'},'tieu_de':{'tieu_de'}}


def prf(tp,fp,fn):
    p=tp/(tp+fp) if tp+fp else (1. if not fn else 0.)
    r=tp/(tp+fn) if tp+fn else (1. if not fp else 0.)
    return dict(tp=tp,fp=fp,fn=fn,precision=p,recall=r,f1=2*p*r/(p+r) if p+r else 0.)


def heading_matches(gold,pred,lines):
    """Maximum-cardinality one-to-one matches, >=half gold lines on a common page."""
    edges={}
    for i,g in enumerate(gold):
        options=[];gs=set(g['dong'])
        for j,p in enumerate(pred):
            shared=gs.intersection(p['dong'])
            pages=Counter(lines[x]['trang'] for x in shared if x in lines)
            if pages and max(pages.values())*2>=len(gs):options.append((len(shared),j))
        edges[i]=[j for _,j in sorted(options,key=lambda t:(-t[0],t[1]))]
    owners={}
    def augment(i,seen):
        for j in edges[i]:
            if j in seen:continue
            seen.add(j)
            if j not in owners or augment(owners[j],seen):owners[j]=i;return True
        return False
    for i in edges:augment(i,set())
    return {pred[j]['id']:gold[i]['id'] for j,i in owners.items()}


def gold_leaves(headings,lines):
    starts={x:h['id'] for h in headings for x in h['dong']};leaf=None;result={}
    for line in lines:
        if line['id'] in starts:leaf=starts[line['id']]
        result[line['id']]=leaf
    return result


def kendall(gold,pred):
    ranks={x:i for i,x in enumerate(gold)}
    actual=[x for x in pred if x in ranks]; n=len(actual)
    if len(actual)!=len(set(actual)):raise ValueError('Duplicate predicted reading-order line')
    if n<2:return dict(tau=None,coverage=n/len(gold) if gold else None,penalized=None,common=n,total=len(gold))
    inverted=sum(ranks[a]>ranks[b] for i,a in enumerate(actual) for b in actual[i+1:])
    pairs=n*(n-1)//2;tau=1-2*inverted/pairs
    coverage=n/len(gold)
    return dict(tau=tau,coverage=coverage,penalized=tau*coverage,common=n,total=len(gold))


def score(lines,headings,sample_pages,pred,*,reviewed_lines=None):
    source={r['id']:r for r in lines}
    mapping=heading_matches(headings,pred['headings'],source);gold_by_id={h['id']:h for h in headings}
    pred_lines=pred.get('lines',{})
    if set(pred_lines)-source.keys():raise ValueError('Prediction references unknown source lines')
    match_count=len(mapping)
    m1=prf(match_count,len(pred['headings'])-match_count,len(headings)-match_count)
    correct_parent=0
    for p in pred['headings']:
        if p['id'] not in mapping:continue
        parent=p.get('cha'); actual=None if parent is None else mapping.get(parent,'<unmatched>')
        correct_parent+=actual==gold_by_id[mapping[p['id']]].get('cha')
    m2=dict(correct=correct_parent,matched=match_count,accuracy=correct_parent/match_count if match_count else None)
    gold_role={x:r for p in sample_pages for x,r in p['dong'].items()}
    # L1-only fallback uses the frozen margin detector's explicitly exported exclusions.
    body={x for x,r in gold_role.items() if r in BODY} if sample_pages else source.keys()-set(pred.get('evaluation_excluded',[]))
    if reviewed_lines is not None:body=body.intersection(reviewed_lines)
    leaves=gold_leaves(headings,lines)
    weight=lambda x:sum(not c.isspace() for c in source[x]['text'])
    total=sum(weight(x) for x in body)
    aligned=sum(weight(x) for x in body if x in pred_lines)
    def leaf_matches(x):
        if x not in pred_lines:return False
        value=pred_lines[x].get('leaf')
        actual=None if value is None else mapping.get(value,'<unmatched>')
        return actual==leaves[x]
    correct=sum(weight(x) for x in body if leaf_matches(x))
    m3=dict(correct_chars=correct,total_chars=total,accuracy=correct/total if total else None,
            aligned_chars=aligned,alignment_coverage=aligned/total if total else None,
            body_policy='L2 than_bai+danh_sach' if sample_pages else 'all lines minus frozen raw margin exclusions')
    roles={}
    for name,group in ROLE_GROUPS.items():
        eligible=set(gold_role) if reviewed_lines is None else set(gold_role).intersection(reviewed_lines)
        expected={x for x in eligible if gold_role[x] in group}
        actual={x for x in eligible if pred_lines.get(x,{}).get('role') in group}
        roles[name]=prf(len(expected&actual),len(actual-expected),len(expected-actual))
    orders=[dict(trang=p['trang'],**kendall(p['thu_tu'],pred.get('reading_order',{}).get(str(p['trang']),[]))) for p in sample_pages]
    # L1 covers the whole book; L2 body sampling must not discard all other chunks.
    chunk_lines=source.keys()-{x for x,r in gold_role.items() if r not in BODY}
    chunks=pred.get('chunks',[]);eligible_chunks=[];correct_chunks=0;unmapped=0
    for c in chunks:
        ids=set(c.get('dong',[])).intersection(chunk_lines)
        if not ids:
            unmapped+=1;continue
        eligible_chunks.append(c)
        leaf=c.get('heading');actual=None if leaf is None else mapping.get(leaf,'<unmatched>')
        correct_chunks+=all(leaves[x]==actual for x in ids)
    # Report both conditional and all-chunk denominator; the latter is acceptance M6.
    m6=dict(correct=correct_chunks,total=len(chunks),eligible=len(eligible_chunks),unmapped_or_nonbody=unmapped,
            share=correct_chunks/len(chunks) if chunks else None,
            conditional_share=correct_chunks/len(eligible_chunks) if eligible_chunks else None)
    return dict(M1=m1,M2=m2,M3=m3,M4=dict(roles=roles,reading_order=orders),M6=m6,
                headings_gold=len(headings),source_lines=len(lines),predicted_lines=len(pred_lines))


def aggregate(books):
    groups={}
    for kind in sorted({b['pdf_type'] for b in books}):
        entries=[b for b in books if b['pdf_type']==kind];groups[kind]={}
        for system in sorted({s for b in entries for s in b['systems']}):
            records=[(b['sach'],b['systems'][system]) for b in entries if system in b['systems']]
            summary={}
            for metric,field in [('M1','f1'),('M2','accuracy'),('M3','accuracy'),('M6','share')]:
                values=[(key,r[metric][field]) for key,r in records if r[metric][field] is not None]
                summary[metric]=dict(books=len(values),median=statistics.median(v for _,v in values) if values else None,
                    worst=min(values,key=lambda p:p[1]) if values else None)
            def measure(values,higher=True):
                values=[(key,v) for key,v in values if v is not None]
                return dict(books=len(values),median=statistics.median(v for _,v in values) if values else None,
                    worst=(min if higher else max)(values,key=lambda p:p[1]) if values else None)
            summary['M4']={role:{field:measure([(key,r['M4']['roles'][role][field]) for key,r in records])
                for field in ('precision','recall','f1')} for role in ROLE_GROUPS}
            for field in ('tau','coverage','penalized'):
                values=[]
                for key,r in records:
                    pages=[p[field] for p in r['M4']['reading_order'] if p[field] is not None]
                    values.append((key,statistics.mean(pages) if pages else None))
                summary['M4']['reading_'+field]=measure(values)
            summary['M5']={field:measure([(key,r.get('M5',{}).get(field)) for key,r in records],False)
                           for field in ('seconds_per_page','peak_rss_mb')}
            groups[kind][system]=summary
    return groups


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sach',required=True);parser.add_argument('--thu-muc',type=Path,required=True)
    parser.add_argument('--prediction',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--ban-duyet',action='store_true')
    args=parser.parse_args();folder=args.thu_muc
    errors=validate(args.sach,folder,l2_required=False,review=args.ban_duyet)
    if errors:raise SystemExit('\n'.join(errors))
    lines=read_jsonl(folder/'dong'/f'{args.sach}.jsonl');heads,pages=load_labels(args.sach,folder,review=args.ban_duyet)
    result=score(lines,heads,pages,json.loads(args.prediction.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
