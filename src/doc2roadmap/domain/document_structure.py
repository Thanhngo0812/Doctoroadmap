"""Infer numbering families from the document itself, without heading vocabularies."""
import re
import unicodedata
from collections import defaultdict
from statistics import median

RESULT_MIN_COUNT = 8
RESULT_MAX_BODY_CHARS = 2000
STRUCTURE_RULE = 'numbering-families-v1'
_NUMBER = re.compile(r'\d+(?:\.\d+)*')
_CODE = re.compile(r'(?<!\w)(\d+)([^\W\d_])(?=\W|$)')


def section_code(title):
    match = _CODE.search(title)
    return match if match and unicodedata.category(match[2]) == 'Lu' else None


def code_sequences(titles):
    groups = defaultdict(list)
    for title in titles:
        match = section_code(title)
        if match:
            number, letter = int(match[1]), match[2]
            if letter not in groups[number]:
                groups[number].append(letter)
    return {f'{number}{letter}' for number, letters in groups.items()
            if len(letters) >= 3 and all(ord(b)==ord(a)+1 for a,b in zip(letters,letters[1:]))
            for letter in letters}


def chapter_members(headings):
    """(index,title,declared-level) → outermost increasing numbered families."""
    groups = defaultdict(list)
    for row in headings:
        index,title,level = row[:3]
        order = row[3] if len(row)>3 else index
        match = _NUMBER.search(title)
        if not match or '.' in match[0] or section_code(title):
            continue
        prefix = title[:match.start()].strip().casefold()
        if not any(c.isalpha() for c in prefix):
            continue
        groups[prefix].append((index,int(match[0]),level or 1,order))
    families = [rows for rows in groups.values() if len(rows)>=2
                and any(b[3]>a[3]+1 for a,b in zip(rows,rows[1:]))
                and all(b[1]>a[1] for a,b in zip(rows,rows[1:]))]
    if not families:
        return set()
    shallowest = min(min(r[2] for r in rows) for rows in families)
    families = [rows for rows in families if min(r[2] for r in rows)==shallowest]
    # A recurring end-of-chapter family interleaves the real chapter family;
    # the earlier outer family owns that interval even when the last exercise follows it.
    outer = []
    for rows in sorted(families, key=lambda rows: rows[0][0]):
        if not outer or rows[0][0] > outer[-1][-1][0]:
            outer.append(rows)
    return {r[0] for rows in outer for r in rows}


def back_matter(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines)<3:
        return False
    return sum((len(line)<=120 and bool(re.search(r'\s\d+(?:\s*[,–-]\s*\d+)*$',line)))
               or bool(re.search(r'\b(?:1[5-9]|20)\d{2}\b',line) and re.search(r'[^\W\d_]\.',line))
               for line in lines)/len(lines) > .5


def structure_profile(nodes, *, result_min_count=RESULT_MIN_COUNT, result_max_body_chars=RESULT_MAX_BODY_CHARS):
    headings = [(i,n.text,n.level) for i,n in enumerate(nodes) if n.node_type in {'title','section_header'}]
    chapters = chapter_members(headings)
    codes = code_sequences(title for _,title,_ in headings)
    levels = {i:1 for i in chapters}
    primary = {}
    for i,title,_ in headings:
        match = section_code(title)
        if match and match[0] in codes:
            is_primary = match.start()==0 or bool(title[match.end():].strip())
            levels[i] = 2 if is_primary else 3
            if is_primary:
                primary[i] = match[0]
    bodies = {i:'\n'.join(n.text for n in nodes[i+1:headings[k+1][0] if k+1<len(headings) else len(nodes)])
              for k,(i,_,_) in enumerate(headings)}
    chapter, peer = None,None
    families = defaultdict(list)
    for i,title,_ in headings:
        if i in chapters:
            chapter,peer = i,None
        if i in primary:
            peer = primary[i]
        if i in levels:
            continue
        match = _NUMBER.search(title)
        if not match:
            continue
        numbers = tuple(int(n) for n in match[0].split('.'))
        prefix = title[:match.start()].strip().casefold()
        # Bare decimal labels need a demonstrated peer-section system, not a lone '2D'.
        if not prefix and not codes:
            continue
        families[chapter,prefix].append((i,numbers[-1],peer,len(bodies[i])))
    results, measurements = set(),[]
    proven_prefixes = {prefix for (_,prefix),rows in families.items()
                       if len(rows)>=result_min_count
                       and all(b[1]>a[1] for a,b in zip(rows,rows[1:]))
                       and median(r[3] for r in rows)<=result_max_body_chars
                       and len({r[2] for r in rows if r[2] is not None})>=2}
    for (chapter,prefix),rows in families.items():
        spans_peers = len({r[2] for r in rows if r[2] is not None})>=2
        dense = len(rows)>=result_min_count and all(b[1]>a[1] for a,b in zip(rows,rows[1:]))
        short = median(r[3] for r in rows)<=result_max_body_chars
        measurements.append({'chapter_index':chapter,'prefix':prefix,'count':len(rows),
                             'median_body_chars':median(r[3] for r in rows),'spans_peers':spans_peers})
        if dense and short and prefix in proven_prefixes:
            results.update(r[0] for r in rows)
    last_chapter = max(chapters,default=len(nodes))
    endings = {i for i,_,_ in headings if i>last_chapter and back_matter(bodies[i])}
    levels.update({i:1 for i in endings})
    return {'chapters':chapters,'codes':codes,'levels':levels,'results':results,'back_matter':endings,
            'measurements':measurements}
