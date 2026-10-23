import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-w15-acceptance-20261023')
out = Path(__file__).parent
source = root / 'src/web/backend/wayfinder/infrastructure/real_build.py'
original = source.read_bytes()
old = b"if 'phase_b_store' not in signature(factory).parameters:"
assert original.count(old) == 1
command = [sys.executable, 'scripts/w05_run_tests.py',
           'src/web/backend/tests/test_real_build_w15.py', '-k', 'default_requires_core_port',
           '-o', 'addopts=', '-q', '--basetemp=tmp/coord-w15-port-mutation-v2-20261023',
           '--junitxml=' + str(out / 'port-mutation-v2.xml')]
try:
    source.write_bytes(original.replace(old, b'if False:'))
    with (out / 'port-mutation-v2.log').open('w', encoding='utf-8') as stream:
        result = subprocess.run(command, cwd=root, stdout=stream, stderr=stream)
    tree = ET.parse(out / 'port-mutation-v2.xml')
    failures, errors = tree.findall('.//testcase/failure'), tree.findall('.//testcase/error')
    record = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
              'command': command, 'native_exit_code': result.returncode,
              'failures': len(failures), 'errors': len(errors),
              'original_sha256': hashlib.sha256(original).hexdigest()}
    assert result.returncode == 1 and len(failures) == 1 and not errors, record
    assert 'DID NOT RAISE' in (failures[0].text or ''), failures[0].text
finally:
    source.write_bytes(original)
    assert source.read_bytes() == original
record['restored_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
(out / 'port-mutation-result.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
