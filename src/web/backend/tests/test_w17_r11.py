"""CORE-R11-01: disabled-admin transitions do not remove an active administrator."""
import pytest

from test_w17_admin import admin_case, patch, record, sql
from test_w17_first_admin import snapshot
from wayfinder.application.accounts import AuthError


@pytest.mark.parametrize('enable',[False,True])
@pytest.mark.parametrize('quota',[False,True])
def test_disabled_later_admin_demotion_and_enable_demotion_are_atomic(admin_case,enable,quota):
    rt=admin_case
    later=rt.user(True)
    assert patch(rt,{'status':'disabled'},target=later).status_code==200
    registry=sql(rt,'SELECT account_id,established_at FROM bootstrap_admin')
    owner=snapshot(rt,rt.owner.id)['account']
    assert rt.services.admin.store.admin_count()==1
    changes={'role':'user'}
    if enable: changes['status']='active'
    if quota: changes['build_monthly_max']=7
    response=patch(rt,changes,target=later)
    record(f'disabled-demote-enable-{enable}-quota-{quota}',{
        'response_status':response.status_code,'response':response.json(),
        'accounts':sql(rt,'SELECT id,role,status,build_monthly_max FROM account WHERE id IN (:a,:b)',a=rt.owner.id,b=later.id),
        'registry':sql(rt,'SELECT account_id,established_at FROM bootstrap_admin')})
    assert response.status_code==200,response.text
    assert response.json()['role']=='user' and response.json()['is_first_admin'] is False
    assert sql(rt,'SELECT role,status,build_monthly_max FROM account WHERE id=:id',id=later.id)==[{
        'role':'user','status':'active' if enable else 'disabled','build_monthly_max':7 if quota else None}]
    assert sql(rt,'SELECT account_id,established_at FROM bootstrap_admin')==registry
    assert snapshot(rt,rt.owner.id)['account']==owner
    assert rt.services.admin.store.admin_count()==1
    assert sql(rt,'SELECT id FROM auth_session WHERE account_id=:id',id=later.id)==[]
    assert later.client.get('/api/v1/me').status_code==401
    assert rt.owner.client.get('/api/v1/me').status_code==200
    audits=sql(rt,"SELECT id,action,actor_id,target_id,meta FROM audit_event WHERE action LIKE 'admin_user_%' ORDER BY id")
    expected=['admin_user_disabled','admin_user_role_changed']
    if enable: expected.append('admin_user_enabled')
    if quota: expected.append('admin_user_quota_changed')
    assert audits[0]['action']=='admin_user_disabled'
    assert sorted(row['action'] for row in audits)==sorted(expected)
    assert all(str(row['actor_id'])==rt.owner.id and row['target_id']==later.id and row['meta']=={} for row in audits)
    assert patch(rt,changes,target=later).status_code==200
    assert sql(rt,"SELECT id,action,actor_id,target_id,meta FROM audit_event WHERE action LIKE 'admin_user_%' ORDER BY id")==audits
    record(f'demotion-audit-enable-{enable}-quota-{quota}',audits)


def test_bootstrap_protection_remains_a_separate_control(admin_case):
    rt=admin_case
    other=rt.user(True)
    before=snapshot(rt,rt.owner.id)
    for actor in (rt.owner,other):
        response=patch(rt,{'role':'user','status':'disabled','build_monthly_max':7},target=rt.owner,actor=actor)
        assert response.status_code==409 and response.json()['error']['code']=='protected_admin'
        assert snapshot(rt,rt.owner.id)==before


def test_disabled_transition_does_not_query_last_active_admin_count(admin_case,monkeypatch):
    rt=admin_case
    later=rt.user(True)
    assert patch(rt,{'status':'disabled'},target=later).status_code==200
    def forbidden_count():
        raise AssertionError('A disabled target cannot remove an active admin')
    monkeypatch.setattr(rt.services.admin.store,'admin_count',forbidden_count)
    response=patch(rt,{'role':'user','status':'active','build_monthly_max':7},target=later)
    assert response.status_code==200,response.text


def test_active_admin_removal_retains_count_guard_and_atomic_refusal(admin_case,monkeypatch):
    rt=admin_case
    later=rt.user(True)
    before=snapshot(rt,later.id)
    queried=[]
    def last_active_count():
        queried.append(True)
        return 1  # Application port boundary: prove the fallback guard still refuses a last-active result.
    monkeypatch.setattr(rt.services.admin.store,'admin_count',last_active_count)
    with pytest.raises(AuthError) as error:
        rt.services.admin.update_user(rt.owner.actor,later.id,{'role':'user','build_monthly_max':7})
    assert error.value.code=='conflict' and queried==[True]
    assert snapshot(rt,later.id)==before


def test_disabled_demotion_audit_failure_rolls_back_all_fields_and_preserves_registry(admin_case,monkeypatch):
    rt=admin_case
    later=rt.user(True)
    assert patch(rt,{'status':'disabled'},target=later).status_code==200
    before=snapshot(rt,later.id)
    def fail(event): raise RuntimeError('synthetic R11 audit failure')
    monkeypatch.setattr(rt.services.admin.store,'append_audit',fail)
    response=patch(rt,{'role':'user','status':'active','build_monthly_max':7},target=later)
    assert response.status_code==500
    assert snapshot(rt,later.id)==before
    assert rt.owner.client.get('/api/v1/me').status_code==200
