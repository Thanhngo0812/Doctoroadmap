import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

source_path=Path('src/web/backend/wayfinder/application/admin.py')
cases=[('disabled-target-count',"was_active_admin = target.role == 'admin' and target.status == 'active'",
    "was_active_admin = target.role == 'admin'",'disabled_later_admin_demotion'),
    ('drop-active-guard','if was_active_admin and not will_be_active_admin and self.store.admin_count() <= 1:',
     'if False:','active_admin_removal_retains_count_guard')]
summary=[]
for name,old,new,test in cases:
    raw=source_path.read_bytes()
    text=raw.decode('utf-8')
    assert text.count(old)==1
    try:
        source_path.write_bytes(text.replace(old,new).encode('utf-8'))
        result=subprocess.run([sys.executable,'-X','utf8','tmp/w17_r11_capture.py','r11-mutation-'+name,
            'src/web/backend/tests/test_w17_r11.py','-k',test],capture_output=True)
        xml=ET.parse('report/w17-r11-evidence/runs/r11-mutation-'+name+'.xml')
        failures=xml.findall('.//failure'); errors=xml.findall('.//error')
        row=dict(name=name,test=test,native_exit=result.returncode,assertion_failures=len(failures),setup_errors=len(errors),
            caught=result.returncode==1 and bool(failures) and not errors,original_sha256=hashlib.sha256(raw).hexdigest())
    finally:
        source_path.write_bytes(raw)
        assert source_path.read_bytes()==raw
    row['restored_sha256']=hashlib.sha256(source_path.read_bytes()).hexdigest()
    summary.append(row)
    Path('report/w17-r11-evidence/mutations.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(row),flush=True)
assert all(row['caught'] for row in summary)
