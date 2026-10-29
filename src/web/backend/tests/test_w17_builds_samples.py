"""W17.2: admin build metadata list and dev sample flag. Real cookies/PostgreSQL, fake externals, synthetic data."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from test_builds_w14 import pdf
from test_w17_admin import (  # noqa: F401  (admin_case is a fixture)
    ORIGIN, admin_case, admin_routes, assert_admin_routes_protected, headers, record, sql)
from wayfinder.application.accounts import AuthError

BUILDS = '/api/v1/admin/builds'
ITEM_KEYS = {'build_id', 'doc_id', 'status', 'step', 'pipeline_version', 'requested_by', 'upload', 'course_count',
    'counts_quota', 'cancel_requested', 'claim_count', 'created_at', 'queued_at', 'started_at', 'finished_at',
    'error', 'usage', 'graph_version', 'module_count'}
T0 = datetime(2026, 3, 10, 5, 0, tzinfo=timezone.utc)


def new_build(rt, actor, *, name='fixture.pdf', created=T0, **columns):
    item = rt.services.builds.create_upload(actor, name, pdf() + b'\n%' + uuid4().hex.encode(), rights_confirmed=True)
    bid = item['build']['build_id']
    columns = {'status': 'failed', **columns, 'created_at': created}
    sets = ','.join(f'{key}=:{key}' for key in columns)
    with rt.engine.begin() as connection:
        connection.execute(text(f'UPDATE build SET {sets} WHERE id=:id'), {**columns, 'id': bid})
    return bid


def get_builds(rt, **params):
    return rt.owner.client.get(BUILDS, params=params)


def sample_course(rt, doc_id='doc-1', *, owner=None, is_sample=False, title='Khoá mẫu'):
    return rt.services.courses.create_course((owner or rt.owner).actor, doc_id=doc_id, title=title,
        graph_version=1, module_count=2, is_sample=is_sample)


def flag(rt, course, value, *, actor=None, body=None, hdrs=None):
    who = actor or rt.owner
    return who.client.patch('/api/v1/admin/courses/' + course.id, headers=hdrs or headers(who),
        json={'is_sample': value} if body is None else body)


def course_row(rt, cid):
    return sql(rt, 'SELECT is_sample,updated_at FROM course WHERE id=:id', id=cid)


def sample_audit(rt):
    rows = sql(rt, "SELECT action,actor_id,target_kind,target_id FROM audit_event WHERE action LIKE 'admin_course_sample_%' ORDER BY id")
    return [{**row, 'actor_id': str(row['actor_id'])} for row in rows]


# ---------------------------------------------------------------- route inventory and authorization

def test_new_routes_join_the_admin_inventory_and_stay_protected(admin_case):
    rt = admin_case
    seen = {(method, route.path) for route, method in admin_routes(rt.app)}
    assert {('GET', BUILDS), ('PATCH', '/api/v1/admin/courses/{cid}')} <= seen
    assert_admin_routes_protected(rt)


def test_ordinary_user_and_demoted_admin_cannot_read_or_flag(admin_case):
    rt = admin_case
    stale = rt.user(True)
    course = sample_course(rt)
    new_build(rt, rt.learner.actor)
    assert rt.services.admin.store.get_account(stale.id).role == 'admin'
    with rt.engine.begin() as connection:
        connection.execute(text("UPDATE account SET role='user' WHERE id=:id"), {'id': stale.id})
    for who in (rt.learner, stale):
        response = who.client.get(BUILDS)
        assert response.status_code == 403 and response.json()['error']['code'] == 'forbidden', response.text
        assert response.headers['cache-control'] == 'no-store'
        response = flag(rt, course, True, actor=who)
        assert response.status_code == 403 and response.json()['error']['code'] == 'forbidden', response.text
    assert course_row(rt, course.id)[0]['is_sample'] is False and sample_audit(rt) == []


def test_disabled_admin_cookie_cannot_read_or_flag(admin_case):
    rt = admin_case
    reader, writer = rt.user(True), rt.user(True)
    course = sample_course(rt)
    writer_headers = headers(writer)
    with rt.engine.begin() as connection:  # SQL keeps the session rows: only the live status check can refuse.
        connection.execute(text("UPDATE account SET status='disabled' WHERE id IN (:a,:b)"), {'a': reader.id, 'b': writer.id})
    assert len(sql(rt, 'SELECT id FROM auth_session WHERE account_id IN (:a,:b)', a=reader.id, b=writer.id)) == 2
    read = reader.client.get(BUILDS)
    assert read.status_code in {401, 403} and 'items' not in read.text, read.text
    write = flag(rt, course, True, actor=writer, hdrs=writer_headers)
    assert write.status_code in {401, 403} and 'course_id' not in write.text, write.text
    assert course_row(rt, course.id)[0]['is_sample'] is False and sample_audit(rt) == []


def test_service_layer_refuses_non_admin_and_stale_actors_without_the_route(admin_case):
    rt = admin_case
    service = rt.services.admin
    stale = rt.user(True)
    course = sample_course(rt)
    with rt.engine.begin() as connection:
        connection.execute(text("UPDATE account SET role='user' WHERE id=:id"), {'id': stale.id})
    for actor in (rt.learner.actor, stale.actor):
        with pytest.raises(AuthError) as error:
            service.list_builds(actor)
        assert error.value.code == 'forbidden'
        with pytest.raises(AuthError) as error:
            service.set_sample_course(actor, course.id, True)
        assert error.value.code == 'forbidden'
    assert course_row(rt, course.id)[0]['is_sample'] is False


def test_admin_demoted_after_entering_the_lock_cannot_flag(admin_case, monkeypatch):
    rt = admin_case
    second = rt.user(True)
    course = sample_course(rt)
    store = rt.services.admin.store
    original = store.atomic

    @contextmanager
    def demote_inside(keys):
        with original(keys):
            with rt.engine.begin() as connection:
                connection.execute(text("UPDATE account SET role='user' WHERE id=:id"), {'id': second.id})
            yield
    monkeypatch.setattr(store, 'atomic', demote_inside)
    with pytest.raises(AuthError) as error:
        rt.services.admin.set_sample_course(second.actor, course.id, True)
    assert error.value.code == 'forbidden'
    assert course_row(rt, course.id)[0]['is_sample'] is False and sample_audit(rt) == []


# ---------------------------------------------------------------- GET /admin/builds

def test_builds_page_filters_totals_and_order_match_independent_sql(admin_case):
    rt = admin_case
    ids = {}
    ids['failed_old'] = new_build(rt, rt.learner.actor, created=T0, status='failed', usage_complete=False)
    ids['ok'] = new_build(rt, rt.owner.actor, created=T0 + timedelta(days=1), status='succeeded')
    ids['failed_new'] = new_build(rt, rt.learner.actor, created=T0 + timedelta(days=2), status='failed')
    ids['running'] = new_build(rt, rt.owner.actor, created=T0 + timedelta(days=3), status='running', step='graph')
    ids['queued'] = new_build(rt, rt.learner.actor, created=T0 + timedelta(days=4), status='queued')
    everything = get_builds(rt)
    assert everything.status_code == 200, everything.text
    view = everything.json()
    assert view['total'] == 5 and (view['limit'], view['offset']) == (50, 0)
    expected = [str(row['id']) for row in sql(rt, 'SELECT id FROM build ORDER BY created_at DESC,id')]
    assert [item['build_id'] for item in view['items']] == expected
    # pages are disjoint, cover the whole set, and report the same total
    seen = []
    for offset in (0, 2, 4):
        page = get_builds(rt, limit=2, offset=offset).json()
        assert page['total'] == 5 and page['limit'] == 2 and page['offset'] == offset
        seen += [item['build_id'] for item in page['items']]
    assert seen == expected and get_builds(rt, limit=2, offset=6).json()['items'] == []
    # status / usage filters agree with SQL
    failed = get_builds(rt, status='failed').json()
    assert failed['total'] == 2 == sql(rt, "SELECT count(*) AS n FROM build WHERE status='failed'")[0]['n']
    assert {item['build_id'] for item in failed['items']} == {ids['failed_old'], ids['failed_new']}
    missing = get_builds(rt, usage_complete='false').json()
    assert [item['build_id'] for item in missing['items']] == [ids['failed_old']] and missing['total'] == 1
    assert get_builds(rt, usage_complete='true').json()['total'] == 4
    # text search: doc id, requester e-mail (case-insensitive), exact build id; SQL wildcards are literal
    doc = sql(rt, 'SELECT doc_id FROM build WHERE id=:id', id=ids['ok'])[0]['doc_id']
    assert [i['build_id'] for i in get_builds(rt, q=doc[3:12].upper()).json()['items']] == [ids['ok']]
    assert get_builds(rt, q=rt.learner.email.upper()).json()['total'] == 3
    assert get_builds(rt, q=ids['running']).json()['total'] == 1
    assert get_builds(rt, q='%').json()['total'] == 0 and get_builds(rt, q="' OR 1=1 --").json()['total'] == 0
    assert get_builds(rt, q=rt.learner.email, status='queued').json()['total'] == 1
    record('builds-list', view)


def test_builds_date_range_is_half_open_on_created_at(admin_case):
    rt = admin_case
    early = new_build(rt, rt.learner.actor, created=T0 - timedelta(seconds=1))
    edge = new_build(rt, rt.learner.actor, created=T0)
    inside = new_build(rt, rt.learner.actor, created=T0 + timedelta(seconds=59))
    late = new_build(rt, rt.learner.actor, created=T0 + timedelta(seconds=60))
    params = {'since': T0.isoformat(), 'until': (T0 + timedelta(minutes=1)).isoformat()}
    page = get_builds(rt, **params).json()
    assert page['total'] == 2 and {i['build_id'] for i in page['items']} == {edge, inside}
    assert {i['build_id'] for i in get_builds(rt, since=T0.isoformat()).json()['items']} == {edge, inside, late}
    assert {i['build_id'] for i in get_builds(rt, until=T0.isoformat()).json()['items']} == {early}
    # an offset instant and the same instant in UTC select identical rows
    vn = T0.astimezone(timezone(timedelta(hours=7))).isoformat()
    assert get_builds(rt, since=vn, until=params['until']).json()['total'] == 2


@pytest.mark.parametrize('params', [{'limit': 0}, {'limit': 101}, {'offset': -1}, {'offset': 100001},
    {'status': 'done'}, {'usage_complete': 'maybe'}, {'q': 'x' * 255}, {'since': '2026-01-01T00:00:00'},
    {'since': '2026-01-02T00:00:00Z', 'until': '2026-01-01T00:00:00Z'},
    {'since': '2026-01-01T00:00:00Z', 'until': '2026-01-01T00:00:00Z'}])
def test_builds_invalid_filters_fail_with_fields_and_no_store(admin_case, params):
    response = get_builds(admin_case, **params)
    assert response.status_code == 422, response.text
    assert response.json()['error']['code'] == 'validation' and response.json()['error']['fields']
    assert response.headers['cache-control'] == 'no-store'


def test_builds_item_contract_example_and_error_message_is_fixed_text(admin_case):
    rt = admin_case
    ok = new_build(rt, rt.learner.actor, created=T0, status='succeeded', step='learning_prep', graph_version=3, module_count=7,
        spent_usd='0.123456', model_calls=9, input_tokens=1200, output_tokens=340, elapsed_seconds=61.5,
        counts_quota=True, queued_at=T0, started_at=T0 + timedelta(seconds=2), finished_at=T0 + timedelta(seconds=63))
    bad = new_build(rt, rt.owner.actor, created=T0 + timedelta(hours=1), status='failed', error_code='loi_mang',
        error_message='Traceback (most recent call last): leaked', retryable=True, claim_count=2)
    unknown = new_build(rt, rt.owner.actor, created=T0 + timedelta(hours=2), status='failed', error_code='LEAK <b>raw</b>',
        error_message='RuntimeError: secret', retryable=False)
    items = {item['build_id']: item for item in get_builds(rt).json()['items']}
    assert all(set(item) == ITEM_KEYS for item in items.values())
    done = items[ok]
    assert done['status'] == 'succeeded' and done['step'] == 'learning_prep' and done['error'] is None
    assert done['usage'] == {'spent_usd': 0.123456, 'model_calls': 9, 'input_tokens': 1200, 'output_tokens': 340,
        'usage_complete': True, 'elapsed_seconds': 61.5}
    assert done['graph_version'] == 3 and done['module_count'] == 7 and done['counts_quota'] is True
    assert done['requested_by'] == {'user_id': rt.learner.id, 'email': rt.learner.email}
    assert done['upload']['kind'] == 'pdf' and done['upload']['page_count'] == 1 and done['upload']['size_bytes'] > 0
    assert done['course_count'] == 1 and done['pipeline_version'] and done['doc_id'].startswith('u-')
    assert items[bad]['error'] == {'code': 'loi_mang', 'message': 'Kết nối bị gián đoạn; bạn có thể thử lại', 'retryable': True}
    assert items[unknown]['error']['code'] == 'khong_ro' and items[unknown]['error']['retryable'] is False
    assert 'Traceback' not in json.dumps(items) and 'secret' not in json.dumps(items) and 'LEAK' not in json.dumps(items)
    # requester deleted: the build row survives with requested_by NULL
    with rt.engine.begin() as connection:
        connection.execute(text('UPDATE build SET requested_by=NULL WHERE id=:id'), {'id': bad})
    assert next(i for i in get_builds(rt).json()['items'] if i['build_id'] == bad)['requested_by'] is None
    record('builds-item', done)


def test_builds_response_never_carries_private_or_raw_fields(admin_case):
    rt = admin_case
    markers = ['W172_CHAT_Q', 'W172_CHAT_A', 'W172_DOCUMENT', 'W172_QUIZ_ANSWER']
    bid = new_build(rt, rt.learner.actor, name='W172_FILE_NAME.pdf', status='failed', error_code='loi_noi_bo',
        error_message='RuntimeError: W172_BUILD_ERROR_TRACE', retryable=False, claimed_by='W172_WORKER_HOST')
    course = rt.services.courses.create_course(rt.learner.actor, doc_id='w172-private-' + uuid4().hex,
        title='W172_COURSE_TITLE', graph_version=1, module_count=1)
    for kind, marker in zip(('session', 'turn', 'document', 'quiz_attempt'), markers):
        rt.services.phase_b_store.put_record(kind, uuid4().hex, {'owner': rt.learner.id, 'doc_id': course.doc_id, 'content': marker})
    with rt.engine.begin() as connection:
        connection.execute(text("INSERT INTO build_attempt(build_id,lease_id,claim_count,result) VALUES(:id,:lease,1,CAST(:r AS jsonb))"),
            {'r': json.dumps({'trace': 'W172_ATTEMPT_RESULT'}), 'id': bid, 'lease': str(uuid4())})
        connection.execute(text("UPDATE upload SET public_id='W172_PUBLIC_ID' WHERE id=(SELECT upload_id FROM build WHERE id=:id)"), {'id': bid})
    response = get_builds(rt)
    assert response.status_code == 200 and any(i['build_id'] == bid for i in response.json()['items'])
    leaks = markers + ['W172_FILE_NAME', 'W172_BUILD_ERROR_TRACE', 'W172_WORKER_HOST', 'W172_COURSE_TITLE',
        'W172_ATTEMPT_RESULT', 'W172_PUBLIC_ID', 'password_hash', 'token_hash', 'Traceback']
    assert not any(marker in response.text for marker in leaks)
    direct = rt.services.admin.list_builds(rt.owner.actor)
    assert not any(marker in json.dumps(direct, default=str) for marker in leaks)


def test_builds_dto_strips_repository_extras(admin_case, monkeypatch):
    rt = admin_case
    new_build(rt, rt.learner.actor)
    page = rt.services.admin.list_builds(rt.owner.actor)
    page['private_extra'] = 'W172_DTO_SECRET'
    page['items'][0]['error_message'] = 'W172_DTO_SECRET'
    page['items'][0]['usage']['extra'] = 'W172_DTO_SECRET'
    page['items'][0]['requested_by']['password_hash'] = 'W172_DTO_SECRET'
    monkeypatch.setattr(rt.services.admin, 'list_builds', lambda *a, **k: page)
    response = get_builds(rt)
    assert response.status_code == 200 and 'W172_DTO_SECRET' not in response.text


# ---------------------------------------------------------------- PATCH /admin/courses/{cid}

def test_flag_on_off_changes_the_learner_sample_list_and_audits_once_per_change(admin_case):
    rt = admin_case
    course = sample_course(rt)
    assert rt.learner.client.get('/api/v1/courses').json()['samples'] == []
    response = flag(rt, course, True)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['course_id'] == course.id and body['is_sample'] is True and body['doc_id'] == 'doc-1'
    assert set(body) == {'course_id', 'doc_id', 'title', 'status', 'is_sample', 'published_graph_version', 'module_count', 'updated_at'}
    assert course_row(rt, course.id)[0]['is_sample'] is True
    assert [c['course_id'] for c in rt.learner.client.get('/api/v1/courses').json()['samples']] == [course.id]
    assert sample_audit(rt) == [{'action': 'admin_course_sample_set', 'actor_id': rt.owner.id,
        'target_kind': 'course', 'target_id': course.id}]
    assert flag(rt, course, True).status_code == 200            # repeat: no second audit
    assert len(sample_audit(rt)) == 1
    response = flag(rt, course, False)
    assert response.status_code == 200 and response.json()['is_sample'] is False
    assert rt.learner.client.get('/api/v1/courses').json()['samples'] == []
    assert [row['action'] for row in sample_audit(rt)] == ['admin_course_sample_set', 'admin_course_sample_unset']
    assert flag(rt, course, False).status_code == 200 and len(sample_audit(rt)) == 2
    record('flag-on', body)


@pytest.mark.parametrize('doc_id', ['u-' + 'a' * 20, 'w172-private', 'doc-1 ', 'DOC-1', 'doc-1/../x'])
def test_flag_outside_the_six_allowlisted_documents_is_refused(admin_case, doc_id):
    rt = admin_case
    private = sample_course(rt, doc_id, owner=rt.learner, title='W172_PRIVATE_TITLE')
    before = course_row(rt, private.id)
    response = flag(rt, private, True)
    assert response.status_code == 409 and response.json()['error']['code'] == 'conflict', response.text
    assert response.json()['error']['fields'][0]['loc'] == 'doc_id'
    assert 'W172_PRIVATE_TITLE' not in response.text
    assert course_row(rt, private.id) == before and sample_audit(rt) == []
    assert rt.services.courses.list_sample_courses(rt.learner.actor) == []


def test_flag_refused_when_the_environment_is_not_dev(admin_case):
    rt = admin_case
    course = sample_course(rt, is_sample=True)
    other = sample_course(rt, 'doc-6')
    rt.services.admin.settings = rt.settings.model_copy(update={'env': 'prod'})
    for target, value in ((other, True), (course, False)):
        response = flag(rt, target, value)
        assert response.status_code == 409 and response.json()['error']['code'] == 'conflict', response.text
        assert response.json()['error']['fields'][0]['loc'] == 'env'
    assert course_row(rt, course.id)[0]['is_sample'] is True and course_row(rt, other.id)[0]['is_sample'] is False
    assert sample_audit(rt) == []


def test_flag_missing_course_and_invalid_bodies_never_change_anything(admin_case):
    rt = admin_case
    course = sample_course(rt)
    before = course_row(rt, course.id)
    missing = rt.owner.client.patch('/api/v1/admin/courses/' + str(uuid4()), headers=headers(rt.owner), json={'is_sample': True})
    assert missing.status_code == 404 and missing.json()['error']['code'] == 'not_found'
    malformed = rt.owner.client.patch('/api/v1/admin/courses/not-a-uuid', headers=headers(rt.owner), json={'is_sample': True})
    assert malformed.status_code == 422 and malformed.json()['error']['fields']
    for body in ({}, {'is_sample': None}, {'is_sample': 'true'}, {'is_sample': 1}, {'is_sample': True, 'title': 'x'},
            {'is_sample': True, 'owner_id': rt.learner.id}, {'doc_id': 'doc-6'}):
        response = flag(rt, course, None, body=body)
        assert response.status_code == 422 and response.json()['error']['code'] == 'validation', (body, response.text)
        assert response.json()['error']['fields']
    assert course_row(rt, course.id) == before and sample_audit(rt) == []


def test_csrf_and_origin_required_for_flag(admin_case):
    rt = admin_case
    course = sample_course(rt)
    path = '/api/v1/admin/courses/' + course.id
    for bad in ({'Origin': ORIGIN}, {**headers(rt.owner), 'Origin': 'https://evil.invalid'}):
        response = rt.owner.client.patch(path, headers=bad, json={'is_sample': True})
        assert response.status_code == 403 and response.json()['error']['code'] == 'csrf_failed'
    assert course_row(rt, course.id)[0]['is_sample'] is False


def test_flag_and_audit_commit_or_roll_back_together(admin_case, monkeypatch):
    rt = admin_case
    course = sample_course(rt)
    before = course_row(rt, course.id)

    def fail(event):
        raise RuntimeError('synthetic audit write failure')
    monkeypatch.setattr(rt.services.admin.store, 'append_audit', fail)
    response = flag(rt, course, True)
    assert response.status_code == 500
    assert course_row(rt, course.id) == before and sample_audit(rt) == []
    assert rt.services.courses.list_sample_courses(rt.learner.actor) == []


def test_second_course_of_the_same_document_cannot_become_a_duplicate_sample(admin_case):
    rt = admin_case
    kept = sample_course(rt, is_sample=True)
    duplicate = sample_course(rt)
    response = flag(rt, duplicate, True)
    assert response.status_code == 409 and response.json()['error']['fields'][0]['loc'] == 'is_sample'
    assert course_row(rt, duplicate.id)[0]['is_sample'] is False and sample_audit(rt) == []
    assert flag(rt, kept, True).status_code == 200      # the existing sample may be re-asserted
    assert flag(rt, kept, False).status_code == 200 and flag(rt, duplicate, True).status_code == 200


def _second_runtime(rt):
    from wayfinder.application.admin import AdminService
    from wayfinder.infrastructure.admin_store import PostgresAdminStore
    from wayfinder.infrastructure.database import create_database_engine
    engine = create_database_engine(rt.engine.url)
    return engine, AdminService(PostgresAdminStore(engine), settings=rt.settings, clock=rt.clock)


def test_concurrent_flags_on_two_courses_of_one_document_leave_exactly_one_sample(admin_case):
    rt = admin_case
    first, second = sample_course(rt), sample_course(rt)
    engine, other = _second_runtime(rt)
    barrier = Barrier(2)

    def run(pair):
        service, course = pair
        barrier.wait(5)
        try:
            service.set_sample_course(rt.owner.actor, course.id, True)
            return 'changed'
        except AuthError as error:
            return error.code
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, [(rt.services.admin, first), (other, second)]))
    finally:
        engine.dispose()
    assert sorted(results) == ['changed', 'conflict']
    assert sql(rt, "SELECT count(*) AS n FROM course WHERE is_sample AND doc_id='doc-1'")[0]['n'] == 1
    assert len(sample_audit(rt)) == 1


def test_concurrent_identical_flags_audit_one_change(admin_case):
    rt = admin_case
    course = sample_course(rt)
    engine, other = _second_runtime(rt)
    barrier = Barrier(2)

    def run(service):
        barrier.wait(5)
        return service.set_sample_course(rt.owner.actor, course.id, True)['is_sample']
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert list(pool.map(run, [rt.services.admin, other])) == [True, True]
    finally:
        engine.dispose()
    assert course_row(rt, course.id)[0]['is_sample'] is True and len(sample_audit(rt)) == 1


def test_flag_response_and_service_never_expose_private_learning_markers(admin_case):
    rt = admin_case
    course = sample_course(rt, title='Khoá mẫu công khai')
    marker = 'W172_FLAG_PRIVATE'
    rt.services.phase_b_store.put_record('turn', uuid4().hex, {'owner': rt.learner.id, 'doc_id': course.doc_id, 'content': marker})
    response = flag(rt, course, True)
    assert response.status_code == 200 and marker not in response.text
    assert marker not in json.dumps(rt.services.admin.set_sample_course(rt.owner.actor, course.id, False), default=str)
