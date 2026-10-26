from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from fastapi.testclient import TestClient
import pytest

from wayfinder.api.app import create_app
from wayfinder.application.accounts import AuthError
from wayfinder.settings import WebSettings
from wayfinder.testing import build_test_application

P='Coordinator synthetic original passphrase!'

def test_two_authenticated_sessions_cannot_both_change_the_old_password(monkeypatch):
    bundle=build_test_application()
    service=bundle.services.accounts
    a=service.register('coord-w04@example.vn',P,'An',ip=None,user_agent=None).session
    b=service.login('coord-w04@example.vn',P,ip=None,user_agent=None)
    original=service.me
    barrier=Barrier(2)
    def simultaneous_identity(raw):
        identity=original(raw)
        barrier.wait(timeout=10)
        return identity
    monkeypatch.setattr(service,'me',simultaneous_identity)
    def update(grant,new_password):
        try:
            service.change_password(grant.token,P,new_password,ip=None)
            return ('ok',grant,new_password)
        except AuthError as error:
            return (error.code,grant,new_password)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(update,a,'Coordinator first replacement!'),pool.submit(update,b,'Coordinator second replacement!')]
        results=[future.result(timeout=20) for future in futures]
    assert sorted(row[0] for row in results)==['ok','unauthenticated']
    monkeypatch.setattr(service,'me',original)
    winner=next(row for row in results if row[0]=='ok')
    loser=next(row for row in results if row[0]!='ok')
    assert service.me(winner[1].token).session.id==winner[1].session.id
    with pytest.raises(AuthError) as revoked:
        service.me(loser[1].token)
    assert revoked.value.code=='unauthenticated'
    credentials=service.store.get_credentials('coord-w04@example.vn')
    assert service.hasher.verify(credentials.password_hash,winner[2])
    assert not service.hasher.verify(credentials.password_hash,loser[2])
    assert not service.hasher.verify(credentials.password_hash,P)
    assert len([event for event in service.store.audit_events if event.action=='password_changed'])==1
    assert bundle.phase_b.model.json_calls==bundle.phase_b.model.tool_calls==[]
    assert bundle.phase_b.embedding.requests==[]

@pytest.mark.parametrize('missing',[{}, {'new_password':'Coordinator replacement passphrase!'}, {'current_password':None,'new_password':'Coordinator replacement passphrase!'}])
def test_current_password_is_required_without_mutating_account(missing):
    bundle=build_test_application()
    settings=WebSettings(_env_file=None,frontend_dist=Path('missing'),allowed_origins=['https://testserver'])
    with TestClient(create_app(settings,bundle.services),base_url='https://testserver') as client:
        client.post('/api/v1/auth/register',headers={'Origin':'https://testserver'},json={'email':'coord-required@example.vn','password':P,'display_name':'An'})
        identity=client.get('/api/v1/me').json()
        before=bundle.services.accounts.store.get_credentials('coord-required@example.vn')
        response=client.post('/api/v1/me/password',headers={'Origin':'https://testserver','X-CSRF-Token':identity['csrf_token']},json=missing)
        assert response.status_code==422
        assert response.json()['error']['code']=='validation'
        assert bundle.services.accounts.store.get_credentials('coord-required@example.vn')==before
        assert client.get('/api/v1/me').json()==identity
        assert not [event for event in bundle.services.accounts.store.audit_events if event.action=='password_changed']


def test_openapi_snapshot_is_generated_and_preserves_main_operations():
    import json
    from wayfinder.api.openapi import write_openapi
    from wayfinder.composition import WebServices
    root=Path(__file__).resolve().parents[4]
    app=create_app(WebSettings(_env_file=None,frontend_dist=Path('missing')),WebServices(health_check=lambda:'ok'))
    current=app.openapi()
    snapshot=json.loads((root/'src/web/openapi.json').read_text(encoding='utf8'))
    assert current==snapshot
    old=json.loads((root/'main-openapi.json').read_text(encoding='utf8'))
    operations=lambda schema:{(p,m) for p,methods in schema['paths'].items() for m in methods}
    assert operations(old)<=operations(current)
    assert operations(current)-operations(old)=={('/api/v1/me','patch'),('/api/v1/me/password','post'),('/api/v1/auth/logout-all','post')}
