import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

base=Path('src/web/backend/wayfinder')
service=base/'application/admin.py'
accounts=base/'application/accounts.py'
store=base/'infrastructure/admin_store.py'
migration=base/'migrations/versions/w17_0009_first_admin.py'
api=base/'api/admin.py'
cases=[
 ('first-identity-service',service,'if blocked and (protected is None or uid == protected):','if False:',
    'test_first_identity_protected_even_with_two_admins_and_atomic_patch'),
 ('bootstrap-write',accounts,'self.store.establish_first_admin(account.id, now)','pass # mutated registry write',
    'test_bootstrap_creation_race_persists_exactly_one_identity_and_audit'),
 ('bootstrap-transaction',accounts,"with self.store.atomic(['admin:users', f\"account:{normalized}\"]):",
    "with __import__('contextlib').nullcontext():",'test_bootstrap_insert_and_audit_failure_roll_back_together'),
 ('bootstrap-global-lock',accounts,"['admin:users', f\"account:{normalized}\"]","[f\"account:{normalized}\"]",
    'test_bootstrap_creation_race_persists_exactly_one_identity_and_audit'),
 ('legacy-no-guess',accounts,'if first_admin is None and self.store.has_admins():','if False:',
    'test_legacy_upgrade_requires_explicit_uuid_without_guessing_and_atomic_assignment'),
 ('legacy-assignment-transaction',accounts,"with self.store.atomic(['admin:users', f'account:{account_id}']):",
    "with __import__('contextlib').nullcontext():",'test_legacy_upgrade_requires_explicit_uuid_without_guessing_and_atomic_assignment'),
 ('account-db-guard',migration,'IF OLD.id=protected_id THEN','IF FALSE THEN',
    'test_database_rejects_delete_and_bypass_of_protected_identity'),
 ('registry-immutable',migration,"IF TG_OP <> 'INSERT' THEN",'IF FALSE THEN',
    'test_database_rejects_delete_and_bypass_of_protected_identity'),
 ('active-admin-count',store,"table.c.role=='admin',table.c.status=='active'","table.c.role=='admin'",
    'test_disabled_actor_and_disabled_admin_not_counted_as_active'),
 ('session-revocation',service,'self.store.delete_account_sessions(uid)','pass # mutated revoke',
    'test_disable_revokes_two_cookies_enable_never_resurrects'),
 ('update-transaction',service,"with self.store.atomic(['admin:users', f'account:{uid}', f'account:{target.email_normalized}']):",
    "with __import__('contextlib').nullcontext():",'test_update_and_audit_rollback_on_audit_failure'),
 ('stale-actor',service,"if account is None or account.status != 'active' or account.role != 'admin':",'if False:',
    'test_stale_admin_actor_and_unauthorized_patch_cannot_write'),
 ('dto-projection',api,"@router.get('/users',response_model=AdminUsersResponse)","@router.get('/users',response_model=None)",
    'test_real_response_dtos_strip_repository_extras_at_every_level'),
 ('login-lock',service,"['admin:users', f'account:{uid}', f'account:{target.email_normalized}']","['admin:users', f'account:{uid}']",
    'test_inflight_login_cannot_leave_a_session_after_disable'),
]
out=Path('report/w17-first-admin-evidence')
summary_path=out/'mutations.json'
summary=json.loads(summary_path.read_text(encoding='utf-8')) if len(sys.argv)>1 and summary_path.exists() else []
for name,path,old,new,test in cases:
    if len(sys.argv)>1 and name not in sys.argv[1:]: continue
    original=path.read_bytes()
    source=original.decode('utf-8')
    assert source.count(old)==1,(name,source.count(old))
    try:
        path.write_bytes(source.replace(old,new).encode('utf-8'))
        run=subprocess.run([sys.executable,'-X','utf8','tmp/w17_policy_capture.py','policy-mutation-'+name,
            'src/web/backend/tests/test_w17_first_admin.py','src/web/backend/tests/test_w17_admin.py','-k',test],capture_output=True)
        xml=ET.parse(out/'runs'/('policy-mutation-'+name+'.xml'))
        failures=xml.findall('.//failure'); errors=xml.findall('.//error')
        caught=run.returncode==1 and bool(failures) and not errors
        row=dict(name=name,test=test,native_exit=run.returncode,failures=len(failures),errors=len(errors),caught=caught,
            source_original_sha256=hashlib.sha256(original).hexdigest())
    finally:
        path.write_bytes(original)
        assert path.read_bytes()==original
    row['restored_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    summary=[entry for entry in summary if entry['name']!=name]+[row]
    summary_path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(row),flush=True)
assert all(row['caught'] for row in summary)
