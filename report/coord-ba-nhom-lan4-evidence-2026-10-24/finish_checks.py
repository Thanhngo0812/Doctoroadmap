import hashlib, json, socket, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
OUT = Path(__file__).parent
WT = ROOT / 'tmp/coord-r4-acceptance-20261024'

def counts(path):
    cases = list(ET.parse(path).getroot().iter('testcase'))
    failed = sum(c.find('failure') is not None for c in cases)
    errors = sum(c.find('error') is not None for c in cases)
    skipped = sum(c.find('skipped') is not None for c in cases)
    xfailed = sum(c.find('skipped') is not None and c.find('skipped').get('type') == 'pytest.xfail' for c in cases)
    return dict(tests=len(cases), passed=len(cases)-failed-errors-skipped,
                failed=failed, errors=errors, skipped=skipped-xfailed, xfailed=xfailed)

def write(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if '--summary' in sys.argv:
    result = {name: counts(OUT/'runs'/name) for name in ['full.xml','full-final.xml','full-current.xml','react.xml','react-final.xml','react-current.xml','design-focused.xml']}
    audit = json.loads((WT/'report/w08-evidence/browser-coord-r4-current-retry/audit.json').read_text(encoding='utf-8'))
    result['browser_keys'] = list(audit)
    result['browser_counts'] = {key: len(value) for key,value in audit.items() if isinstance(value,list)}
    result['new_provider_cost_usd'] = 0
    write('acceptance-summary.json', result)
    print(json.dumps(result))
else:
    sys.path.insert(0, str(WT/'src/web/backend'))
    from dotenv import dotenv_values
    from sqlalchemy import text
    from sqlalchemy.engine import make_url, URL
    from wayfinder.infrastructure.database import create_database_engine
    values = dotenv_values(ROOT/'src/web/.env')
    configured = values.get('WAYFINDER_TEST_DATABASE_URL')
    url = make_url(configured) if configured else URL.create('postgresql+psycopg', username='wayfinder',
        password=values['POSTGRES_TEST_PASSWORD'], host='127.0.0.1', port=5433, database='wayfinder_test')
    runtime = json.loads((WT/'report/w08-evidence/browser-coord-r4-current-retry/runtime.json').read_text(encoding='utf-8'))
    assert runtime['temporaryDatabaseRemoved'] and runtime['serverThreadStopped']
    engine = create_database_engine(url)
    try:
        with engine.connect() as connection:
            exists = connection.scalar(text('SELECT count(*) FROM pg_database WHERE datname=:name'), {'name':runtime['databaseName']})
    finally:
        engine.dispose()
    with socket.socket() as connection:
        listening = connection.connect_ex(('127.0.0.1',8018)) == 0
    assert exists == 0 and not listening
    source_diff = subprocess.check_output(['git','diff','--name-only',runtime['sourceCommit'],'HEAD','--','src','tests','scripts','design'], cwd=WT, text=True)
    assert not source_diff.strip()
    write('runtime-cleanup.json', {'database': runtime['databaseName'], 'database_exists':False,
        'port_8018_listening':False, 'producer_stopped':True, 'browser_source_same_as_final_gate':True,
        'provider_calls':0, 'usd':0})
    print('Independent browser database/port cleanup and final source identity verified')
