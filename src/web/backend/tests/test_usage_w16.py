"""W-16 backend: synthetic ledger/build fixtures, real PostgreSQL/HTTP, zero provider spend."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from test_builds_w14 import builds, pdf
from wayfinder.application.courses import CourseService
from wayfinder.infrastructure.course_store import PostgresCourseStore
from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
from wayfinder.infrastructure.learning_usage import my_learning_usage
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore

pytestmark = pytest.mark.postgres


@pytest.fixture
def usage_case(builds, monkeypatch):
    b = builds
    attempted = []
    def forbidden(*args, **kwargs):
        attempted.append(1)
        raise AssertionError('W-16 usage reads must not invoke provider, ADC, SMTP or media')
    for target in ('doc2roadmap.infrastructure.llm.gemini.urlopen',
                   'doc2roadmap.infrastructure.embedding.gemini.urlopen',
                   'doc2roadmap.infrastructure.llm.phase_b.urlopen',
                   'doc2roadmap.infrastructure.google_auth.VertexCredentials.headers',
                   'google.auth.default', 'smtplib.SMTP'):
        monkeypatch.setattr(target, forbidden)
    b.ledger = PostgresPhaseBStore(b.engine)
    b.runtime = WebLearningRuntime(b.ledger, clock=b.clock)
    b.courses = CourseService(PostgresCourseStore(b.engine), settings=b.settings, clock=b.clock)
    b.course_a = b.courses.create_course(b.actor, doc_id='w16-book-a', title='Fixture A', graph_version=8, module_count=1)
    b.course_b = b.courses.create_course(b.actor, doc_id='w16-book-b', title='Fixture B', graph_version=8, module_count=1)
    b.other, b.other_client, _ = b.user()
    b.services.learning = SimpleNamespace(courses=b.courses, runtime=b.runtime)
    try:
        yield b
        assert attempted == []
    finally:
        b.ledger.close()


def ledger_row(b, purpose, cost, *, owner=None, doc=None, at=None, **extra):
    b.ledger.append_usage(dict(purpose=purpose, cost_usd=cost, doc_id=doc or b.course_a.doc_id,
        learner_id=owner or b.actor.user_id, created_at=(at or b.clock.now()).isoformat(),
        fixture='W16 synthetic ledger, not provider spend', **extra))


def usage(b, client=None):
    response = (client or b.client).get('/api/v1/me/usage')
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'no-store'
    return response.json()


def assert_no_money_keys(value):
    if isinstance(value, dict):
        assert all('usd' not in key.lower() and 'cost' not in key.lower() for key in value)
        for item in value.values():
            assert_no_money_keys(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_money_keys(item)


def test_usage_combines_courses_isolates_people_and_separates_shared_and_build(usage_case):
    b = usage_case
    ledger_row(b, 'assistant', .25, doc=b.course_a.doc_id)
    ledger_row(b, 'document', .35, doc=b.course_b.doc_id)
    ledger_row(b, 'assistant', .8, owner=b.other.user_id)
    for purpose, amount in [('lecture', 2), ('quiz_gen', 1), ('quiz_verify', 1.5)]:
        ledger_row(b, purpose, amount, owner=b.other.user_id, doc=b.course_b.doc_id)
    for purpose in ('assistant', 'document', 'lecture', 'quiz_gen', 'quiz_verify'):
        ledger_row(b, purpose, 99, counted_in='build')
    ledger_row(b, 'build', 99)
    view = usage(b)
    assert view['learner_today']['used_ratio'] == pytest.approx(.6)
    assert not view['learner_today']['limited'] and not view['shared_content_today']['limited']
    assert usage(b, b.other_client)['learner_today']['used_ratio'] == pytest.approx(.8)
    assert view['builds_this_month'] == {'used': 0, 'max': None, 'resets_at': '2026-02-01T00:00:00+07:00'}
    ledger_row(b, 'quiz_verify', .5, owner=b.other.user_id)
    ledger_row(b, 'document', .4)
    assert usage(b)['learner_today'] == {'used_ratio': 1., 'limited': True, 'resets_at': '2026-01-02T00:00:00+07:00'}
    assert usage(b)['shared_content_today'] == {'limited': True}
    assert usage(b, b.other_client)['shared_content_today'] == {'limited': True}
    assert_no_money_keys(view)


@pytest.mark.parametrize('date,next_reset', [
    ('2026-10-31', '2026-11-02T00:00:00+07:00'),
    ('2026-12-31', '2027-01-02T00:00:00+07:00'),
    ('2028-02-29', '2028-03-02T00:00:00+07:00'),
])
def test_usage_resets_at_1700_utc_and_excludes_next_day_rows(usage_case, date, next_reset):
    b = usage_case
    before = datetime.fromisoformat(date + 'T16:59:00+00:00')
    after = before + timedelta(minutes=1)
    b.clock.instant = before
    ledger_row(b, 'assistant', .75, at=before)
    ledger_row(b, 'document', .35, at=after)
    ledger_row(b, 'lecture', 5, at=after)
    ledger_row(b, 'document', 99, at=before - timedelta(days=1))
    view = usage(b)
    assert view['learner_today']['used_ratio'] == pytest.approx(.75)
    assert view['shared_content_today'] == {'limited': False}
    assert datetime.fromisoformat(view['learner_today']['resets_at']).astimezone(timezone.utc) == after
    b.clock.instant = after
    view = usage(b)
    assert view['learner_today'] == {'used_ratio': .35, 'limited': False, 'resets_at': next_reset}
    assert view['shared_content_today'] == {'limited': True}


def test_usage_projection_uses_the_scoped_ledger_port(usage_case, monkeypatch):
    b = usage_case
    ledger_row(b, 'assistant', .4)
    ledger_row(b, 'lecture', .1)
    ledger_row(b, 'document', 99, owner=b.other.user_id)
    ledger_row(b, 'assistant', 99, at=b.clock.now() - timedelta(days=1))
    ledger_row(b, 'build', 99)
    original = b.ledger.usage_rows
    observed = []
    def scoped_rows(doc_id=None, *, learner_id=None, since=None, purposes=None):
        assert doc_id is None and since is not None and since.utcoffset() is not None
        assert purposes in ({'assistant', 'document'}, {'lecture', 'quiz_gen', 'quiz_verify'})
        rows = original(doc_id, learner_id=learner_id, since=since, purposes=purposes)
        observed.append((learner_id, set(purposes), len(rows)))
        return rows
    monkeypatch.setattr(b.ledger, 'usage_rows', scoped_rows)
    view = my_learning_usage(b.actor, b.engine, b.runtime)
    assert view['learner_today']['used_ratio'] == pytest.approx(.4)
    assert observed == [(b.actor.user_id, {'assistant', 'document'}, 1),
                        (None, {'lecture', 'quiz_gen', 'quiz_verify'}, 1)]


def build_row(b, stamp, *, actor=None, counted=True):
    item = b.service.create_upload(actor or b.actor, 'fixture.pdf', pdf() + b'\n%' + uuid4().hex.encode(), rights_confirmed=True)
    with b.engine.begin() as c:
        c.execute(text("UPDATE build SET status='failed',counts_quota=:counted,queued_at=:stamp,finished_at=:stamp,spent_usd=:cost WHERE id=:id"),
            {'id': item['build']['build_id'], 'stamp': stamp, 'counted': counted, 'cost': .01 if counted else 0})


@pytest.mark.parametrize('date,reset', [('2026-01-31', '2026-02-01T00:00:00+07:00'),
                                     ('2026-12-31', '2027-01-01T00:00:00+07:00'),
                                     ('2028-02-29', '2028-03-01T00:00:00+07:00')])
def test_monthly_quota_uses_counted_attempts_in_exact_vietnam_month(usage_case, date, reset):
    b = usage_case
    before = datetime.fromisoformat(date + 'T16:59:00+00:00')
    after = before + timedelta(minutes=1)
    b.clock.instant = before
    build_row(b, before)
    build_row(b, before, counted=False)
    build_row(b, after)
    build_row(b, before, actor=b.other)
    build_row(b, before.replace(day=1) - timedelta(days=2))
    assert b.store.quota(b.actor.user_id, before, None)['builds_used'] == 1
    view = usage(b)
    assert view['builds_this_month'] == {'used': 1, 'max': None, 'resets_at': reset}
    assert view['builds_used'] == 1 and view['build_monthly_max'] is None and view['builds_remaining'] is None
    b.clock.instant = after
    assert usage(b)['builds_this_month']['used'] == 1


@pytest.mark.parametrize('maximum', [None, 3])
def test_monthly_demo_default_and_account_override_use_existing_quota(usage_case, maximum):
    b = usage_case
    b.service.settings = b.settings.model_copy(update={'build_monthly_max': maximum})
    build_row(b, b.clock.now())
    assert usage(b)['builds_this_month']['max'] == maximum
    with b.engine.begin() as c:
        c.execute(text('UPDATE account SET build_monthly_max=1 WHERE id=:id'), {'id': b.actor.user_id})
    view = usage(b)
    assert view['builds_this_month']['used'] == view['builds_this_month']['max'] == 1
    assert view['builds_remaining'] == 0


def test_usage_http_enforces_authentication_and_cannot_select_another_owner(usage_case):
    b = usage_case
    with TestClient(b.app) as guest:
        assert guest.get('/api/v1/me/usage').status_code == 401
    ledger_row(b, 'assistant', .2)
    ledger_row(b, 'assistant', .9, owner=b.other.user_id)
    response = b.client.get('/api/v1/me/usage', params={'learner_id': b.other.user_id})
    assert response.status_code == 200 and response.json()['learner_today']['used_ratio'] == pytest.approx(.2)
    with b.engine.begin() as c:
        c.execute(text("UPDATE account SET status='disabled' WHERE id=:id"), {'id': b.actor.user_id})
    assert b.client.get('/api/v1/me/usage').status_code in (401, 403)


def test_usage_real_response_dto_recursively_removes_internal_money(usage_case, monkeypatch):
    from wayfinder.infrastructure import learning_usage
    b = usage_case
    original = learning_usage.my_learning_usage
    def with_private_fields(*args):
        value = original(*args)
        value['internal_cost_usd'] = 99
        value['learner_today']['cost_usd'] = 99
        value['shared_content_today']['debug'] = [{'provider_cost': 99}]
        return value
    monkeypatch.setattr(learning_usage, 'my_learning_usage', with_private_fields)
    view = usage(b)
    assert_no_money_keys(view)
    assert set(view['learner_today']) == {'used_ratio', 'limited', 'resets_at'}
    assert set(view['shared_content_today']) == {'limited'}
    assert set(view['builds_this_month']) == {'used', 'max', 'resets_at'}


def test_usage_http_without_learning_runtime_keeps_usage_1_and_exports_fixture_json(usage_case):
    b = usage_case
    b.services.learning = None
    ledger_row(b, 'document', .35, doc=b.course_b.doc_id)
    view = usage(b)
    assert view['contract_version'] == 'usage-1' and view['learner_today']['used_ratio'] == pytest.approx(.35)
    assert view['builds_this_month']['max'] is None
    assert_no_money_keys(view)
    label = os.environ.get('W16_EVIDENCE_RUN')
    if label:
        out = Path(__file__).resolve().parents[4] / 'report/w16-evidence' / label
        out.mkdir(parents=True, exist_ok=True)
        (out / 'usage-1.json').write_bytes((json.dumps(view, ensure_ascii=False, indent=2) + '\n').encode())
