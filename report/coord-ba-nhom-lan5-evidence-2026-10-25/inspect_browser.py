import collections,json
from pathlib import Path
HERE=Path(__file__).parent
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
path=ROOT/'tmp/coord-r5-acceptance-20261025/report/w09-evidence/browser-coord-r5/audit.json'
audit=json.loads(path.read_text(encoding='utf-8'))
assert len(audit['configurations'])==12 and len(audit['screens'])==99 and len(audit['accessibility'])==43
assert not audit['pageErrors']
assert all(not r['layout']['overflow'] and not r['layout']['targets'] for r in audit['screens'])
assert all(not r['violations'] for r in audit['accessibility'])
incomplete=[]
for row in audit['accessibility']:
    assert all(item.get('id')=='color-contrast' for item in row['incomplete']),row['file']
    if row['incomplete']:
        assert row['manualMath'],row['file']
    assert all(sample.get('eligible') and sample.get('unobscured') and sample.get('contrast',0)>=4.5 for sample in row.get('manualMath',[]))
    if row['incomplete']:incomplete.append(row['file'])
classified=collections.Counter()
for row in audit['console']:
    message=row['message']
    if 'Applying inline style violates' in message and 'Content Security Policy' in message:classified['axe_csp_inline_probe']+=1
    elif 'fonts.googleapis.com' in message and 'Content Security Policy' in message:classified['axe_csp_font_probe']+=1
    elif '401 (Unauthorized)' in message:classified['pre_login_401']+=1
    elif '404 (Not Found)' in message:classified['revoked_access_404']+=1
    else:raise AssertionError(row)
result={'configurations':12,'screens':99,'axe':43,'http_records_including_sse_tee':len(audit['http']),
        'page_errors':0,'overflow_or_bad_targets':0,'axe_violations':0,'reviewed_contrast_incomplete':len(incomplete),
        'console_classification':dict(classified),'console_total':len(audit['console']),
        'limits':'The browser happy paths do not cover the two independent W09 Required counterexamples.'}
(HERE/'browser-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
