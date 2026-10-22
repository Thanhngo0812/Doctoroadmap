"""Serial W11 counterexamples; restore source before any full gate/browser."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'report/w11-evidence/final-2026-10-22/mutations'
CASES = (
    ('token-disclosure', 'application/sharing.py', 'test_share_link_token_is_one_time_and_never_returned_by_list',
     'token[-6:]', 'token'),
    ('revocation', 'application/sharing.py', 'test_revoked_or_expired_link_is_invalid_even_for_an_existing_member',
     'link and link.revoked_at is None and', 'link and'),
    ('expiry', 'application/sharing.py', 'test_revoked_or_expired_link_is_invalid_even_for_an_existing_member',
     '(link.expires_at is None or link.expires_at > now)', 'True'),
    ('use-limit', 'application/sharing.py', 'test_all_invalid_preview_reasons_have_the_same_error_envelope_fields',
     '(not check_uses or link.max_uses is None or link.use_count < link.max_uses)', 'True'),
    ('count', 'application/sharing.py', 'test_postgres_one_use_join_race_counts_exactly_one_member_and_use',
     'if not self.store.increment_use_count(link.id, link.max_uses):', 'if False:'),
    ('atomic-join', 'infrastructure/sharing_store.py', 'test_postgres_create_and_join_rollback_when_audit_write_fails',
     'self._connection.set(connection)', 'self._connection.set(None)'),
    ('immediate-access', 'application/sharing.py', 'test_postgres_remove_and_rejoin_preserve_phase_b_progress_and_revoke_keeps_members',
     'self.store.remove_membership(cid, user_id)', 'pass  # mutation: removal omitted'),
)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,relative,test,old,new in CASES:
        p=ROOT/'src/web/backend/wayfinder'/relative
        original=p.read_bytes(); content=original.decode('utf-8'); assert content.count(old)==1
        xml=OUT/f'{name}.xml'
        cmd=[sys.executable,'scripts/w05_run_tests.py','-o','addopts=','-q',
             f'src/web/backend/tests/test_w11_sharing.py::{test}',
             f'--basetemp=tmp/w11-mut-{name}-{uuid4().hex}',f'--junitxml={xml}']
        try:
            p.write_bytes(content.replace(old,new).encode('utf-8'))
            run=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=180)
            (OUT/f'{name}.log').write_bytes(run.stdout+run.stderr)
            suite=ET.parse(xml).getroot()
            failures=suite.findall('.//testcase/failure'); errors=suite.findall('.//testcase/error')
            assert run.returncode==1 and failures and not errors,name
            rows.append(dict(name=name,command=cmd,native_exit_code=run.returncode,
                             failures=len(failures),errors=len(errors),original_sha256=sha256(original).hexdigest()))
        finally:
            p.write_bytes(original); assert p.read_bytes()==original
        rows[-1]['restored_sha256']=sha256(p.read_bytes()).hexdigest()
    (OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} mutations caught; exact bytes restored')


if __name__=='__main__': main()
