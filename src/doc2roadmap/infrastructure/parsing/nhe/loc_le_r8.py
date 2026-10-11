"""Conservative running-margin detection, separate from heading recognition."""
from collections import Counter, defaultdict
import re
import unicodedata


def zone(row):
    return row['top']>.92*row['height'] or row['bottom']<.08*row['height']


def style(row):
    width=max(row.get('width') or 600,1)
    return (row.get('font'),round(row['size']),bool(row['bold']),
            round((row['x0']+row['x1'])/(2*width),1),round(row['top']/row['height'],2))


def decisions(rows):
    repeated=defaultdict(set)
    numbers=defaultdict(set)
    for r in rows:
        if not zone(r): continue
        text=' '.join(unicodedata.normalize('NFC',r['text']).casefold().split())
        if len(text)>3 and any(c.isalpha() for c in text):
            repeated[(text,style(r))].add(r['page'])
        if re.fullmatch(r'\d{1,4}',text):
            numbers[(r['page']-int(text),style(r))].add(r['page'])
    running={k for k,p in repeated.items() if len(p)>=3 and len(p)/(max(p)-min(p)+1)>=.4}
    pagination={k for k,p in numbers.items() if len(p)>=3}
    result=[]
    for r in rows:
        text=' '.join(unicodedata.normalize('NFC',r['text']).casefold().split())
        reason=None
        if zone(r):
            if (text,style(r)) in running:
                reason='repeated_exact_text_style_dense_pages'
            elif re.fullmatch(r'\d{1,4}',text) and (r['page']-int(text),style(r)) in pagination:
                reason='page_number_consistent_offset_style'
        result.append(reason)
    return result


def prepare_rows(rows):
    kept=[r for r,reason in zip(rows,decisions(rows),strict=True) if reason is None]
    sizes=Counter()
    for r in kept:
        sizes[r['size']]+=r['chars']
    body=sizes.most_common(1)[0][0] if sizes else 10.
    return kept,body
