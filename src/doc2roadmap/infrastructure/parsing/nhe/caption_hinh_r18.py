"""Caption veto requires both a numbered caption and nearby raster geometry."""
import re


def candidates(rows,figures):
    result=[]
    for i,row in enumerate(rows):
        if len(row['text'].split())>40 or not re.match(
            r'^\s*(?:hình|figure|fig\.)\s+\d+(?:[.\-]\d+)*(?:[.:\-]?\s+)\S',row['text'],re.I):
            continue
        height=max(row['size'],1)
        for figure in figures:
            left,bottom,right,top=figure['bbox']
            overlap=max(0,min(right,row['x1'])-max(left,row['x0']))
            if figure['page']!=row['page'] or not -.2*height<=bottom-row['top']<=3*height:
                continue
            if overlap<.5*min(right-left,row['x1']-row['x0']): continue
            if any(j!=i and other['page']==row['page'] and row['top']<other['top']<bottom
                   and min(other['x1'],row['x1'])>max(other['x0'],row['x0']) for j,other in enumerate(rows)):
                continue
            result.append(i); break
    return result
