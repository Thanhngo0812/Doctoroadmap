"""Ordered heading tree prototype: score parents only on the open right frontier."""
from collections import Counter
import math
import re
import numpy as np
import cau_truc_r2 as r2


def signature(text):
    text=text.strip()
    if re.match(r'^(phần|part)\b',text,re.I): return 1,()
    if re.match(r'^(chương|chapter)\b',text,re.I): return 2,()
    m=re.match(r'^(\d+(?:\.\d+)*)(?:[.)]?\s+|$)',text)
    if m: return 4,tuple(map(int,m[1].split('.')))
    if re.match(r'^[IVXLCDM]+(?:[.\-–]\s*|\s+)',text): return 3,()
    if re.match(r'^[A-ZĐ][.)]\s+',text): return 5,()
    if re.match(r'^[a-zđ][.)]\s+',text): return 6,()
    return 0,()


def project_outline(marks,rows):
    counts=Counter(m['matching_rows'][0] for m in marks if len(m['matching_rows'])==1)
    stack=[]
    native=[]
    groups=[]
    for i,m in enumerate(marks):
        while stack and marks[stack[-1]]['level']>=m['level']: stack.pop()
        native.append(stack[-1] if stack else -1)
        groups.append(groups[stack[0]] if stack else i)
        stack.append(i)
    selected=[i for i,m in enumerate(marks) if len(m['matching_rows'])==1 and counts[m['matching_rows'][0]]==1]
    lookup={old:new for new,old in enumerate(selected)}
    indexes=[marks[i]['matching_rows'][0] for i in selected]
    if any(a>=b for a,b in zip(indexes,indexes[1:])):
        raise ValueError('Outline does not follow PDF row order')
    result=[]
    for i in selected:
        parent=native[i]
        while parent!=-1 and parent not in lookup: parent=native[parent]
        result.append(dict(row=dict(rows[marks[i]['matching_rows'][0]]),row_index=marks[i]['matching_rows'][0],
                           bookmark=i,group=groups[i],native_parent=native[i],parent=lookup.get(parent,-1)))
    return result


def subset(entries,groups):
    indexes=[i for i,e in enumerate(entries) if e['group'] in groups]
    mapping={i:j for j,i in enumerate(indexes)}
    return [dict(entries[i],parent=mapping.get(entries[i]['parent'],-1)) for i in indexes]


def baseline(rows):
    parents=[]
    stack=[]
    levels=[r2.baseline.heading_level(r['text']) for r in rows]
    for i,level in enumerate(levels):
        while stack and levels[stack[-1]]>=level: stack.pop()
        parents.append(stack[-1] if stack else -1)
        stack.append(i)
    return parents


def pair_features(rows,i,parent,parents):
    child=rows[i]
    p=rows[parent] if parent>=0 else None
    ckind,cnum=signature(child['text'])
    pkind,pnum=signature(p['text']) if p else (-1,())
    depth=0
    cursor=parent
    while cursor>=0:
        depth+=1
        cursor=parents[cursor]
    siblings=[j for j,q in enumerate(parents) if q==parent]
    sibling=rows[siblings[-1]] if siblings else None
    skind,snum=signature(sibling['text']) if sibling else (-1,())
    same_style=lambda a,b: bool(a and b and a.get('font')==b.get('font') and a['bold']==b['bold']
                               and abs(a['size']-b['size'])<=.5)
    return [parent<0,depth,math.log1p(i-parent),0 if p is None else min(child['page']-p['page'],100),
            child['size'],child['bold'],child.get('italic',0),ckind,len(cnum),
            0 if p is None else p['size'],0 if p is None else child['size']-p['size'],
            0 if p is None else p['bold'],pkind,len(pnum),same_style(child,p),
            bool(p and child.get('font')==p.get('font')),0 if p is None else (child['x0']-p['x0'])/max(child['width'],1),
            bool(cnum and pnum and cnum[:-1]==pnum),ckind==pkind,
            sibling is not None,same_style(child,sibling),ckind==skind,len(cnum)==len(snum),
            bool(cnum and snum and len(cnum)==len(snum) and cnum[:-1]==snum[:-1] and cnum[-1]==snum[-1]+1)]


def decode(rows,score):
    parents=[]
    frontier=[-1]
    for i in range(len(rows)):
        candidates=list(frontier)
        values=np.asarray(score(rows,i,candidates,parents),dtype=float)
        if values.shape!=(len(candidates),) or not np.isfinite(values).all():
            raise ValueError('Need one finite score per candidate parent')
        parent=candidates[int(np.argmax(values))]
        parents.append(parent)
        frontier=frontier[:frontier.index(parent)+1]+[i]
    return parents


def training_pairs(entries):
    rows=[e['row'] for e in entries]
    parents=[]
    frontier=[-1]
    x,y,ids=[],[],[]
    for i,entry in enumerate(entries):
        target=entry['parent']
        if target not in frontier: raise ValueError('Training tree is not ordered')
        for parent in frontier:
            x.append(pair_features(rows,i,parent,parents)); y.append(int(parent==target)); ids.append(entry['bookmark'])
        parents.append(target)
        frontier=frontier[:frontier.index(target)+1]+[i]
    return np.asarray(x,dtype=np.float32),np.asarray(y,dtype=np.int8),ids


def metrics(target,predicted):
    if len(target)!=len(predicted): raise ValueError('Tree sizes differ')
    def ancestors(parents):
        result=[]
        frontier=[-1]
        for i,parent in enumerate(parents):
            if parent not in frontier: raise ValueError('Tree must follow preorder')
            result.append(set() if parent<0 else result[parent]|{parent})
            frontier=frontier[:frontier.index(parent)+1]+[i]
        return result
    gold,actual=ancestors(target),ancestors(predicted)
    tp=sum(len(a&b) for a,b in zip(gold,actual))
    ref=sum(map(len,gold)); pred=sum(map(len,actual))
    return dict(headings=len(target),parent_hits=sum(a==b for a,b in zip(target,predicted)),
                parent_accuracy=sum(a==b for a,b in zip(target,predicted))/max(len(target),1),
                ancestor_tp=tp,ancestor_reference=ref,ancestor_predicted=pred,
                ancestor_precision=tp/pred if pred else float(not ref),
                ancestor_recall=tp/ref if ref else float(not pred),
                ancestor_f1=2*tp/(pred+ref) if pred+ref else 1.)
