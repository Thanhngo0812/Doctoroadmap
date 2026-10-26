import json,hashlib,socket,xml.etree.ElementTree as ET
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import make_url
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
TOOLS=ROOT/'tmp/coord-r8-tools-20261026'
WT=ROOT/'tmp/coord-r8-acceptance-20261026'
result={}
for label in ['full-ready','react']:
    receipt=json.loads((TOOLS/'runs'/f'{label}-exit.json').read_text(encoding='utf-8'))
    assert receipt['native_exit_code']==0,receipt
    cases=list(ET.parse(TOOLS/'runs'/f'{label}.xml').getroot().iter('testcase'))
    count=lambda tag:sum(c.find(tag) is not None for c in cases)
    result[label]={'tests':len(cases),'passed':sum(not any(c.find(t) is not None for t in ['failure','error','skipped']) for c in cases),'failures':count('failure'),'errors':count('error'),'skipped_or_xfailed':count('skipped'),'native':0,'seconds':receipt['elapsed_seconds']}
    assert result[label]['failures']==result[label]['errors']==0
    if label=='full-ready':
        result['named_groups']={key:sum(key in c.get('classname','') for c in cases) for key in ['test_w04_accounts','test_content_admission_w10','test_content_w10','test_tokens_and_wcag','test_usage_w16']}
        result['retained_skips']=[{'name':c.get('name'),'reason':c.find('skipped').get('message'),'type':c.find('skipped').get('type')} for c in cases if c.find('skipped') is not None]
for label in ['build','browser-ready']:
    receipt=json.loads((TOOLS/'runs'/f'{label}-exit.json').read_text(encoding='utf-8'))
    assert receipt['native_exit_code']==0
    result[label]={'native':0,'seconds':receipt['elapsed_seconds']}
runtime=json.loads((WT/'report/w10-r7-evidence/browser-coord-r8-ready/runtime.json').read_text(encoding='utf-8'))
assert runtime['temporaryDatabaseRemoved'] and runtime['serverThreadStopped']
url=make_url(dotenv_values(ROOT/'src/web/.env')['WAYFINDER_TEST_DATABASE_URL'])
import sys
sys.path[:0]=[str(WT/'src/web/backend'),str(WT/'src')]
from wayfinder.infrastructure.database import create_database_engine
engine=create_database_engine(url)
with engine.connect() as c:
    remains=c.scalar(text('SELECT count(*) FROM pg_database WHERE datname=:name'),{'name':runtime['databaseName']})
assert remains==0
engine.dispose()
s=socket.socket();s.settimeout(1);result['browser_port8020_closed']=s.connect_ex(('127.0.0.1',8020))!=0;s.close();assert result['browser_port8020_closed']
result['browser_database_absent_independent_read']=True
for p,sha in json.loads((TOOLS/'protected.json').read_text()).items():
    assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha,p
result['protected_six_files_unchanged']=True
(TOOLS/'gate-summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
