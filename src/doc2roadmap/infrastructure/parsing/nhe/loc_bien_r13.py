"""Research outer-row extension; R8c remains frozen."""
from collections import Counter, defaultdict
import re
import unicodedata
from . import loc_le_r8c as previous


def boundary_candidates(rows):
    pages=defaultdict(list)
    for i,row in enumerate(rows):
        pages[row['page']].append(i)
    result={}
    for indexes in pages.values():
        ordered=sorted(indexes,key=lambda i:-rows[i]['top'])
        if len(ordered)<2:
            continue
        for side,i,j in [('top',ordered[0],ordered[1]),('bottom',ordered[-1],ordered[-2])]:
            row,other=rows[i],rows[j]
            gap=row['bottom']-other['top'] if side=='top' else other['bottom']-row['top']
            half=row['top']>row['height']/2 if side=='top' else row['bottom']<row['height']/2
            if not half or gap<.5*max(row['size'],1):
                continue
            text=' '.join(unicodedata.normalize('NFC',row['text']).casefold().split())
            for position,pattern in [('first',r'^(\d{1,4})\s+(.+)$'),('last',r'^(.+)\s+(\d{1,4})$')]:
                match=re.fullmatch(pattern,text)
                if not match:
                    continue
                number,body=match.groups() if position=='first' else match.groups()[::-1]
                if sum(any(c.isalpha() for c in word) for word in body.split())>=3:
                    result.setdefault(i,[]).append((side,position,body,row['page']-int(number),previous.previous.style(row)))
    return result


def prepare_rows(rows):
    kept,_=previous.prepare_rows(rows)
    while True:
        keys=boundary_candidates(kept)
        series=defaultdict(set)
        for i,values in keys.items():
            for key in values:
                series[key].add(kept[i]['page'])
        running={k for k,pages in series.items() if len(pages)>=10 and len(pages)/(max(pages)-min(pages)+1)>=.8}
        remove={i for i,values in keys.items() if any(k in running for k in values)}
        if not remove:
            break
        kept=[r for i,r in enumerate(kept) if i not in remove]
    sizes=Counter()
    for r in kept:
        sizes[r['size']]+=r['chars']
    return kept,sizes.most_common(1)[0][0] if sizes else 10.
