import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

base=Path('src/web/backend/wayfinder')
service=base/'application/admin.py'
store=base/'infrastructure/admin_store.py'
api=base/'api/admin.py'
cases=[
 ('session-revocation',service,'self.store.delete_account_sessions(uid)','pass # mutation', 'test_disable_revokes_two_cookies_enable_never_resurrects'),
 ('last-admin',service,'and self.store.admin_count() <= 1','and False', 'test_last_admin_demote_rejected'),
 ('concurrent-admin-lock',service,"['admin:users', f'account:{uid}',", "[f'account:{uid}',", 'test_two_postgres_runtimes_cannot_demote_both_last_admins'),
 ('audit-transaction',service,'with self.store.atomic([\'admin:users\', f\'account:{uid}\', f\'account:{target.email_normalized}\']):',
    'with __import__(\'contextlib\').nullcontext():','test_update_and_audit_rollback_on_audit_failure'),
 ('admin-authority',service,"decision = decide(actor, 'admin_users', None, None)","return\n        decision = decide(actor, 'admin_users', None, None)",'test_all_admin_routes_require_admin_and_no_store'),
 ('live-admin-authority',service,"if account is None or account.status != 'active' or account.role != 'admin':",'if False:', 'test_stale_admin_actor_and_unauthorized_patch_cannot_write'),
 ('audit-meta',store,"('id','at','actor_id','action','target_kind','target_id','ip')","('id','at','actor_id','action','target_kind','target_id','ip','meta')",'test_audit_filters_half_open_dates_and_never_exposes_arbitrary_meta'),
 ('dto-users',api,"@router.get('/users',response_model=AdminUsersResponse)","@router.get('/users',response_model=None)",'test_real_response_dtos_strip_repository_extras_at_every_level'),
 ('month-end',store,'b.queued_at<:end','b.queued_at<=:end','test_user_monthly_counts_match_existing_quota_at_vietnam_boundary'),
 ('audit-start',store,'predicates.append(table.c.at>=since)','predicates.append(table.c.at>since)','test_audit_filters_half_open_dates_and_never_exposes_arbitrary_meta'),
 ('login-account-lock',service,"['admin:users', f'account:{uid}', f'account:{target.email_normalized}']",
    "['admin:users', f'account:{uid}']",'test_inflight_login_cannot_leave_a_session_after_disable'),
]
summary_path=Path('report/w17-evidence/mutations.json')
summary=json.loads(summary_path.read_text(encoding='utf-8')) if len(sys.argv)>1 else []
for name,path,old,new,test in cases:
    if len(sys.argv)>1 and name not in sys.argv[1:]:
        continue
    original=path.read_bytes()
    source=original.decode('utf-8')
    assert source.count(old)==1,(name,source.count(old))
    try:
        path.write_bytes(source.replace(old,new).encode('utf-8'))
        result=subprocess.run([sys.executable,'tmp/w17_capture.py','mutation-'+name,
            'src/web/backend/tests/test_w17_admin.py','-k',test],capture_output=True,text=True)
        xml=ET.parse('report/w17-evidence/runs/mutation-'+name+'.xml')
        failures=xml.findall('.//failure')
        errors=xml.findall('.//error')
        caught=result.returncode==1 and bool(failures) and not errors
        entry=dict(name=name,test=test,native_exit=result.returncode,failures=len(failures),errors=len(errors),caught=caught,
            source_before_sha256=hashlib.sha256(original).hexdigest())
        summary.append(entry)
        print(json.dumps(entry),flush=True)
    finally:
        path.write_bytes(original)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==hashlib.sha256(original).hexdigest()
    Path('report/w17-evidence/mutations.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
assert all(row['caught'] for row in summary)
