"""R8c: pagination attached to running text, confirmed by page-offset series."""
from collections import Counter, defaultdict
import re
import unicodedata
import loc_le_r8 as previous


def candidates(row):
    if not previous.zone(row):
        return []
    text=' '.join(unicodedata.normalize('NFC',row['text']).casefold().split())
    result=[]
    for side,pattern in [('first',r'^(\d{1,4})\s+(.+)$'),('last',r'^(.+)\s+(\d{1,4})$')]:
        match=re.fullmatch(pattern,text)
        if not match:
            continue
        number,body=match.groups() if side=='first' else match.groups()[::-1]
        if any(c.isalpha() for c in body):
            result.append((side,body,row['page']-int(number),previous.style(row)))
    return result


def decisions(rows):
    series=defaultdict(set)
    keys=[candidates(r) for r in rows]
    for row,items in zip(rows,keys,strict=True):
        for key in items:
            series[key].add(row['page'])
    running={k for k,pages in series.items() if len(pages)>=5 and len(pages)/(max(pages)-min(pages)+1)>=.4}
    return [reason or ('running_text_with_consistent_page_number' if any(k in running for k in items) else None)
            for reason,items in zip(previous.decisions(rows),keys,strict=True)]


def prepare_rows(rows):
    kept=[r for r,reason in zip(rows,decisions(rows),strict=True) if reason is None]
    sizes=Counter()
    for r in kept:
        sizes[r['size']]+=r['chars']
    return kept,sizes.most_common(1)[0][0] if sizes else 10.
