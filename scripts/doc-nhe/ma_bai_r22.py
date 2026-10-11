"""Separate explicit lesson-code metadata accidentally merged into a chapter."""
from copy import deepcopy
import re
from cau_truc_r2 import normalize_row


def separate(rows,nodes):
    result=[]; audit=[]
    for node in nodes:
        indexes=node['source_rows']
        if (node['node_type']!='section_header' or len(indexes)<2
                or not re.match(r'^(?:chương|chapter|phần|part)\s+(?:\d+|[IVXLCDM]+)\b',node['text'],re.I)):
            result.append(deepcopy(node)); continue
        tail=normalize_row(rows[indexes[-1]]['text'])
        if not re.fullmatch(r'Mã bài\s+(?=[A-Za-z0-9 .:/_\-]*\d)[A-Za-z0-9][A-Za-z0-9 .:/_\-]*',tail,re.I):
            result.append(deepcopy(node)); continue
        for source,kind in [(indexes[:-1],'section_header'),(indexes[-1:],'text')]:
            part=deepcopy(node); selected=[rows[i] for i in source]
            part.update(node_type=kind,text=' '.join(normalize_row(r['text']) for r in selected),
                        source_rows=source,level=node['level'] if kind=='section_header' else None,
                        x0=selected[0]['x0'],bbox=[min(r['x0'] for r in selected),max(r['top'] for r in selected),
                                                 max(r['x1'] for r in selected),min(r['bottom'] for r in selected)])
            result.append(part)
        audit.append(dict(page=node['page'],text=tail,source_rows=indexes[-1:]))
    return result,audit
