"""Run sequentially: every deliberate regression must fail an assertion; always restore."""
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).absolute().parents[4]
PACKAGE=ROOT/'src/web/backend/wayfinder'
TEST='src/web/backend/tests/test_builds_w14.py'
CASES=[
 ('confirmation','application/builds.py',"'ready' if ready else 'building'","'ready' if ready else 'building'",None),
 ('title','application/builds.py',"{'title':title.strip(),'now':now,'cid':upload['course_id']}",
  "{'title':'book','now':now,'cid':upload['course_id']}",'name_is_saved'),
 ('owner','infrastructure/build_store.py','WHERE u.id=:id AND u.account_id=:uid','WHERE u.id=:id','expiration_rights'),
 ('usage','infrastructure/build_store.py',"cost_usd=delta['spent_usd']","cost_usd=0",'result_and_nonzero'),
 ('complete','infrastructure/build_store.py',"complete=counters.get('usage_complete',True) and attempt['usage_complete']","complete=True",'result_and_nonzero'),
 ('cancel','application/build_worker.py',"current['cancel_requested']","False",'result_and_nonzero'),
 ('capacity','infrastructure/build_store.py','return total>=Decimal(str(maximum))','return False','system_cap'),
 ('lease','infrastructure/build_store.py','if result and active:','if result:','heartbeat_reclaim'),
 ('publication-usage','application/build_worker.py',"state['result'] or BuildResult",'BuildResult','publication_error'),
 ('confirmed-media','application/build_worker.py',"if asset.get('confirmed') is not True: continue",'if False: continue','confirmed_media_only'),
 ('late-usage','infrastructure/build_store.py','if not active and result is None: return False','if not active: return False','heartbeat_reclaim'),
 ('boundary-cancel','application/build_worker.py',"if self.store.get_job(bid)['cancel_requested']:",'if False:','cancel_requested_between'),
 ('skip-locked','infrastructure/build_store.py','FOR UPDATE SKIP LOCKED LIMIT 1','FOR UPDATE LIMIT 1','queue_skips_a_locked_job'),
 ('course-context','application/builds.py',"return self._view(actor,upload,self.store.get_job(job['id']))","return self.get_build(actor,job['id'])",'same_actor_separate'),
]
# Change the initial state, so a worker can claim before the explicit confirmation.
CASES[0]=('confirmation','application/builds.py',"VALUES(:id,:doc,:upload,:uid,'awaiting_confirmation',:pipeline,:expires,:now)",
          "VALUES(:id,:doc,:upload,:uid,'queued',:pipeline,:expires,:now)",'upload_requires_explicit')


def main():
    output=ROOT/'report/w14-evidence'
    output.mkdir(parents=True,exist_ok=True)
    records=[]
    run_id=uuid4().hex[:8]
    for label,relative,old,new,selection in CASES:
        path=PACKAGE/relative
        original=path.read_bytes()
        source=original.decode('utf-8')
        assert old in source,(label,'mutation target missing')
        xml=output/(label+'-red.xml')
        command=[sys.executable,str(ROOT/'scripts/w05_run_tests.py'),TEST,'-k',selection,
                 '-o','addopts=','-q','--tb=short','--basetemp=tmp/w14-mut-'+run_id+'-'+label,'--junitxml='+str(xml)]
        try:
            path.write_bytes(source.replace(old,new).encode('utf-8'))
            process=subprocess.run(command,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},
                capture_output=True,encoding='utf-8',errors='replace')
            (output/(label+'-red.log')).write_text(process.stdout+process.stderr,encoding='utf-8')
            tree=ET.parse(xml)
            failures=tree.findall('.//testcase/failure')
            errors=tree.findall('.//testcase/error')
            record={'label':label,'exit_code':process.returncode,'failures':len(failures),'setup_errors':len(errors),
                    'assertion_failures':sum('AssertionError' in (f.text or '') or 'assert ' in (f.text or '') for f in failures),
                    'command':command[2:]}
            assert record['exit_code']==1 and record['assertion_failures']>=1 and not errors,record
        finally:
            path.write_bytes(original)
            assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(original).digest()
        record['source_restored']=True
        records.append(record)
        (output/'mutations.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
        print(label+': caught and restored',flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
