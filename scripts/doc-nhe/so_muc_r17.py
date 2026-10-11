"""Versioned H3 baseline: mixed Roman/decimal prefixes, alphabet ambiguity."""
import re
from collections import Counter,defaultdict
from doi_chung_cay_r14b import style
from cay_tieu_de_r14 import signature


def rule(rows):
    letters=defaultdict(set)
    for row in rows:
        match=re.match(r'^([A-Z])[.)]\s+',row['text'].strip())
        if match: letters[style(row)].add(match[1])
    levels=[]; anchors=defaultdict(Counter)
    for row in rows:
        text=row['text'].strip()
        kind,number=signature(text)
        level={1:1,2:2,5:3,3:4,4:5+max(len(number)-1,0),6:9}.get(kind)
        roman=re.match(r'^([IVXLCDM]+)((?:\.\d+)*)(?:[.)\-–]?\s+)',text)
        if roman and re.fullmatch(r'M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})',roman[1]):
            level=4+roman[2].count('.')
        letter=re.match(r'^([A-Z])[.)]\s+',text)
        if letter and {'A','B'}<=letters[style(row)]: level=3
        levels.append(level)
        if level is not None: anchors[style(row)][level]+=1
    for i,row in enumerate(rows):
        if levels[i] is None:
            counts=anchors[style(row)]
            levels[i]=counts.most_common(1)[0][0] if counts else 2
    parents=[]; stack=[]
    for i,level in enumerate(levels):
        while stack and levels[stack[-1]]>=level: stack.pop()
        parents.append(stack[-1] if stack else -1)
        stack.append(i)
    return parents
