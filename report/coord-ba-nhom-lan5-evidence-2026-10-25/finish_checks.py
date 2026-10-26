import json,socket,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap')
HERE=Path(__file__).parent
WT=ROOT/'tmp/coord-r5-acceptance-20261025'

def counts(path):
    cases=list(ET.parse(path).getroot().iter('testcase'))
    bad=sum(c.find('failure') is not None for c in cases)
    errors=sum(c.find('error') is not None for c in cases)
    skip=sum(c.find('skipped') is not None for c in cases)
    xfail=sum(c.find('skipped') is not None and c.find('skipped').get('type')=='pytest.xfail' for c in cases)
    return {'tests':len(cases),'passed':len(cases)-bad-errors-skip,'failures':bad,'errors':errors,'skip':skip-xfail,'xfail':xfail}

def save(name,data):
    (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if '--summary' in sys.argv:
    result={name:counts(HERE/'runs'/name) for name in ['full.xml','react.xml','safe-full.xml','safe-react.xml']}
    audit=json.loads((WT/'report/w09-evidence/browser-coord-r5/audit.json').read_text(encoding='utf-8'))
    result['browser']={key:len(audit[key]) for key in ['screens','accessibility','http','pageErrors','configurations']}
    save('acceptance-summary.json',result);print(json.dumps(result))
else:
    sys.path.insert(0,str(WT/'src/web/backend'))
    from dotenv import dotenv_values
    from sqlalchemy import text
    from sqlalchemy.engine import make_url
    from wayfinder.infrastructure.database import create_database_engine
    url=make_url(dotenv_values(ROOT/'src/web/.env')['WAYFINDER_TEST_DATABASE_URL'])
    runtime=json.loads((WT/'report/w09-evidence/browser-coord-r5/runtime.json').read_text(encoding='utf-8'))
    assert runtime['temporaryDatabaseRemoved'] and runtime['serverThreadStopped']
    engine=create_database_engine(url)
    try:
        with engine.connect() as connection:
            exists=connection.scalar(text('SELECT count(*) FROM pg_database WHERE datname=:name'),{'name':runtime['databaseName']})
    finally:engine.dispose()
    with socket.socket() as connection:
        listening=connection.connect_ex(('127.0.0.1',8019))==0
    assert exists==0 and not listening
    result={'database':runtime['databaseName'],'database_exists':False,'port_8019_listening':False,
            'producer_stopped':True,'new_provider_cost_usd':0}
    save('runtime-cleanup.json',result);print(json.dumps(result))
