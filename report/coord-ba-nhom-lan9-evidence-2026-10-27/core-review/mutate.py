import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).parent
PY=Path('C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe')
CASES=[
('verified-guard','src/web/backend/wayfinder/application/sharing.py',b"if not actor.email_verified or account['email_verified_at'] is None:",b'if False:', 'test_unverified_actor_and_db_account_cannot_accept'),
('expiry-equality','src/web/backend/wayfinder/application/sharing.py',b'self.clock.now() >= invitation.expires_at',b'self.clock.now() > invitation.expires_at','test_expiry_exact_boundary_denies_without_membership'),
('binding-verified-predicate','src/web/backend/wayfinder/infrastructure/sharing_store.py',b"AND a.email_verified_at IS NOT NULL ",b'', 'test_actual_repository_binding_sql_requires_active_verified_matching_pending_unexpired'),
]
receipts=[]
for name,rel,old,new,test in CASES:
    source=ROOT/rel;before=source.read_bytes();assert before.count(old)==1,(name,before.count(old))
    altered=before.replace(old,new)
    try:
        source.write_bytes(altered)
        cmd=[str(PY),'scripts/w05_run_tests.py','-o','addopts=','-q','tests/test_independent_w12.py::'+test,'--basetemp=tmp/'+name,'--junitxml=runs/'+name+'.xml']
        started=time.monotonic()
        with (ROOT/'runs'/f'{name}.log').open('w',encoding='utf8') as log:
            result=subprocess.run(cmd,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=log,stderr=log)
        cases=list(ET.parse(ROOT/'runs'/f'{name}.xml').getroot().iter('testcase'))
        failures=sum(c.find('failure') is not None for c in cases);errors=sum(c.find('error') is not None for c in cases)
        receipt=dict(name=name,source=rel,before_sha256=hashlib.sha256(before).hexdigest(),mutated_sha256=hashlib.sha256(altered).hexdigest(),native=result.returncode,assertion_failures=failures,setup_errors=errors,seconds=round(time.monotonic()-started,2),command=cmd)
        assert result.returncode==1 and failures==1 and errors==0,receipt
    finally:
        source.write_bytes(before)
    receipt['restored_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();assert receipt['restored_sha256']==receipt['before_sha256'];receipts.append(receipt)
    (ROOT/'mutation-summary.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipts))
