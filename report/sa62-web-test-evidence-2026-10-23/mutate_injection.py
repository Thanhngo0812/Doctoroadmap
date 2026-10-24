import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/sa62-port-kho-pha-b')
out = Path(__file__).parent
path = root / 'src/web/backend/wayfinder/infrastructure/real_build.py'
raw = path.read_bytes()
old = b'phase_b_store=runtime.phase_b_store)'
assert raw.count(old) == 1
command = [sys.executable, 'scripts/w05_run_tests.py',
           'src/web/backend/tests/test_real_build_w15.py', '-k', 'default_factory_injects_web_postgres',
           '-o', 'addopts=', '-q', '--basetemp=tmp/sa62-web-injection-red',
           '--junitxml=' + str(out / 'injection-red.xml')]
try:
    path.write_bytes(raw.replace(old, b'phase_b_store=None)'))
    with (out / 'injection-red.log').open('w', encoding='utf-8') as stream:
        process = subprocess.run(command, cwd=root, stdout=stream, stderr=stream)
    tree = ET.parse(out / 'injection-red.xml')
    failures, errors = tree.findall('.//testcase/failure'), tree.findall('.//testcase/error')
    result = {'command': command, 'native_exit_code': process.returncode, 'failures': len(failures), 'errors': len(errors),
              'original_sha256': hashlib.sha256(raw).hexdigest()}
    assert process.returncode == 1 and len(failures) == 1 and not errors, result
    assert 'AssertionError' in (failures[0].text or '')
finally:
    path.write_bytes(raw)
    assert path.read_bytes() == raw
result['restored_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
(out / 'injection-red-result.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
print(json.dumps(result))
