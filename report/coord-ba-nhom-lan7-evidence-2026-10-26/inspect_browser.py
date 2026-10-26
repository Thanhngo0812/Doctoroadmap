import collections,json,re
from pathlib import Path
HERE=Path(__file__).parent
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
a=json.loads((ROOT/'tmp/coord-r7-acceptance-20261026/report/w10-evidence/browser-coord-r7/audit.json').read_text(encoding='utf8'))
assert len(a['configurations'])==12 and len(a['screens'])==89 and len(a['accessibility'])==58
assert not a['pageErrors']
assert all(not row['layout']['overflow'] and not row['layout']['targets'] for row in a['screens'])
assert all(not row['violations'] for row in a['accessibility'])
measurements=[]
for row in a['accessibility']:
    assert all(x['id']=='color-contrast' for x in row['incomplete'])
    if row['incomplete']:assert row['manualContrast']
    for sample in row['manualContrast']:
        assert sample['eligible'] and sample['unobscured'] and sample['contrast']>=4.5
        measurements.append(sample['contrast'])
counts=collections.Counter()
for row in a['console']:
    m=row['message']
    if 'Applying inline style violates' in m:counts['axe_csp_style']+=1
    elif 'fonts.googleapis.com' in m and 'Content Security Policy' in m:counts['axe_csp_font']+=1
    elif '401 (Unauthorized)' in m:counts['expected_unauthenticated_401']+=1
    elif '404 (Not Found)' in m:counts['expected_outsider_or_revoked_404']+=1
    elif 'ERR_FAILED' in m:counts['deliberately_lost_submit_response']+=1
    else:raise AssertionError(m)
def walk(value,public_quiz=False):
    if isinstance(value,dict):
        for key,child in value.items():
            assert key.lower() not in {'validation','public_id','_private','usage','owner','cost_usd'},key
            if public_quiz:assert not any(word in key.lower() for word in ['correct','answer','explanation','why_wrong']),key
            walk(child,public_quiz)
    elif isinstance(value,list):
        for child in value:walk(child,public_quiz)
checked=0;unavailable=[]
for r in a['http']:
    if not re.search(r'/(quizzes|documents)(/|$)',r['path']):continue
    if r.get('unavailableBody'):unavailable.append({'path':r['path'],'status':r['status']});continue
    body=r.get('body')
    if body is None:continue
    assert 'PRIVATE_SOLVER_REASON' not in body and 'res.cloudinary.com' not in body
    if r['status']>=400 or 'markdown' in r.get('type',''):continue
    public_quiz=bool(re.search(r'/quizzes(?:/[^/]+)?$',r['path']))
    if 'json' in r.get('type',''):
        walk(json.loads(body),public_quiz);checked+=1
    elif 'event-stream' in r.get('type',''):
        for line in body.splitlines():
            if line.startswith('data: '):walk(json.loads(line[6:]),public_quiz);checked+=1
assert a['contrastGuard']=={'lowContrastRejected':True,'obscuredRejected':True}
assert a['disconnect']['completedAfterDialogClosed'] and a['hourLimit']['status']==429 and a['hourLimit']['providerCallsUnchanged']
result={'configurations':12,'screens':89,'axe':58,'http_records':len(a['http']),'page_errors':0,'overflow_or_bad_targets':0,
 'contrast_measurements':len(measurements),'minimum_contrast':min(measurements),'console_classification':dict(counts),'console_total':len(a['console']),
 'captured_content_payloads_checked':checked,'unavailable_response_bodies':unavailable,'unavailable_count':len(unavailable),
 'privacy_limits':'Only captured bodies checked here; Promise.allSettled in harness can ignore a rejected assertion. Native0 is not proof for unavailable bodies. HTTP/PG and DTO tests provide separate evidence.',
 'limits':'Scripted content/media/mail; happy path does not cover cross-origin frequency cap or late submit after quiz history navigation.'}
(HERE/'browser-independent.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='unavailable_response_bodies'}))
