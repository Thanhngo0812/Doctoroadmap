import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r2-acceptance-20261023')
out = Path(__file__).parent
path = root / 'src/web/backend/wayfinder/infrastructure/phase_b_store.py'
raw = path.read_bytes()
old = b'if value.get("counted_in") == "build":'
assert raw.count(old) == 1
command = [sys.executable, 'scripts/w05_run_tests.py',
           'src/web/backend/tests/test_real_build_w15.py::test_build_trace_keeps_raw_usage_but_is_not_billed_twice[build]',
           '-o', 'addopts=', '-q', '--basetemp=tmp/coord-r2-trace-mut', '--junitxml=' + str(out / 'trace-mutation.xml')]
try:
    path.write_bytes(raw.replace(old, b'if False:'))
    with (out / 'trace-mutation.log').open('w', encoding='utf-8') as stream:
        process = subprocess.run(command, cwd=root, stdout=stream, stderr=stream)
    tree = ET.parse(out / 'trace-mutation.xml')
    failures, errors = tree.findall('.//testcase/failure'), tree.findall('.//testcase/error')
    result = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
              'command': command, 'native_exit': process.returncode, 'failures': len(failures), 'errors': len(errors),
              'original_sha256': hashlib.sha256(raw).hexdigest()}
    assert process.returncode == 1 and len(failures) == 1 and not errors, result
    assert 'AssertionError' in (failures[0].text or '')
finally:
    path.write_bytes(raw)
    assert path.read_bytes() == raw
result['restored_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
(out / 'trace-mutation.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
print(json.dumps(result))
