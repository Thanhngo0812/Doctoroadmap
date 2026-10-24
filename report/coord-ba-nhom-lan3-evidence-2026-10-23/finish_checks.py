import hashlib,json,socket,subprocess,sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap');OUT=Path(__file__).parent
WT=ROOT/'tmp/coord-r3-acceptance-20261023'
def run(*args,cwd=ROOT):return subprocess.check_output(args,cwd=cwd,text=True,encoding='utf-8').strip()
def counts(p):
    cases=list(ET.parse(p).getroot().iter('testcase'))
    failures=sum(x.find('failure') is not None for x in cases)
    errors=sum(x.find('error') is not None for x in cases)
    skipped=sum(x.find('skipped') is not None for x in cases)
    return dict(tests=len(cases),passed=len(cases)-failures-errors-skipped,failures=failures,errors=errors,skipped=skipped)
def write(name,obj):(OUT/name).write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())

if sys.argv[-1]=='summary':
    result={'coordinatorHead':run('git','rev-parse','HEAD',cwd=WT),'main':run('git','rev-parse','main'),
        'workers':{name:run('git','rev-parse',branch) for name,branch in [('web','work/w08-lecture'),('core','work/w15-real-build'),('design','work/w24-figma-evidence')]},
        'python':counts(OUT/'runs/full.xml'),'react':counts(OUT/'runs/react.xml'),'reviewRepro':counts(OUT/'runs/repro.xml'),
        'newProviderCostUsd':0,'wholeW15Accepted':False,'productMerged':False}
    write('acceptance-summary.json',result);print(json.dumps(result))
else:
    sys.path.insert(0,str(WT/'src/web/backend'))
    from dotenv import dotenv_values
    from sqlalchemy.engine import make_url
    from sqlalchemy import text
    from wayfinder.infrastructure.database import create_database_engine
    values=dotenv_values(ROOT/'src/web/.env')
    from sqlalchemy.engine import URL
    configured=values.get('WAYFINDER_TEST_DATABASE_URL')
    url=make_url(configured) if configured else URL.create('postgresql+psycopg',username='wayfinder',password=values['POSTGRES_TEST_PASSWORD'],host='127.0.0.1',port=5433,database='wayfinder_test')
    runtime=json.loads((WT/'report/w08-evidence/browser-coord-r3/runtime.json').read_text())
    assert runtime['temporaryDatabaseRemoved'] and runtime['serverThreadStopped']
    engine=create_database_engine(url)
    try:
        with engine.connect() as c: exists=c.scalar(text('SELECT count(*) FROM pg_database WHERE datname=:name'),{'name':runtime['databaseName']})
    finally:engine.dispose()
    with socket.socket() as s: listening=s.connect_ex(('127.0.0.1',8018))==0
    assert exists==0 and not listening
    source_diff=run('git','diff','--name-only','e6b336e','HEAD','--','src','tests','scripts','design',cwd=WT)
    assert not source_diff
    write('runtime-cleanup.json',{'database':runtime['databaseName'],'databaseExists':False,'port8018Listening':False,
        'producerStopped':True,'workingCodeSameAsWorkerE6b336e':True,'paidCalls':0,'usd':0})
    print('Independent browser database/port cleanup and source identity verified')
