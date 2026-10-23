import json
from pathlib import Path
import re
import socket
import sys
from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import make_url

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap')
sys.path.insert(0, str(root / 'src/web/backend'))
from wayfinder.infrastructure.database import create_database_engine

out = Path(__file__).parent
runtime = json.loads((root / 'tmp/coord-r2-acceptance-20261023/report/w11-evidence/auth-return-2026-10-23/browser-coord-r2/runtime.json').read_bytes())
name = runtime['databaseName']
assert re.fullmatch(r'wayfinder_w11_[a-f0-9]{32}', name)
engine = create_database_engine(make_url(dotenv_values(root / 'src/web/.env')['WAYFINDER_TEST_DATABASE_URL']))
try:
    with engine.connect() as connection:
        exists = connection.scalar(text('SELECT count(*) FROM pg_database WHERE datname=:name'), {'name': name})
finally:
    engine.dispose()
with socket.socket() as sock:
    sock.settimeout(2)
    port_open = sock.connect_ex(('127.0.0.1', 8011)) == 0
assert exists == 0 and not port_open
result = {'database_name': name, 'independent_database_count': exists, 'port_8011_open': port_open,
          'read_only_check': True, 'runtime_cleanup_flag': runtime['temporaryDatabaseRemoved']}
(out / 'browser-cleanup.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
print(json.dumps(result))
