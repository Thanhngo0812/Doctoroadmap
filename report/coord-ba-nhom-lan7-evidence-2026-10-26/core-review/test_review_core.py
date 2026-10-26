"""Independent R7 offline probes. No PostgreSQL or provider connection."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore
from wayfinder.api.auth import get_actor
from wayfinder.domain.auth import Actor

ROOT = Path(__file__).resolve().parents[2]
WT = ROOT / 'tmp/w16-usage-backend'
OUT = Path(__file__).resolve().parent
ACTOR = Actor('alice', 'user', True, 'active')


def load_source(relative, mutant):
    source = (WT / relative).read_text(encoding='utf8')
    changes = {
        'trace': ("row.get('counted_in') != 'build'", 'True'),
        'day-upper': ('< reset)', '<= reset)'),
        'day-lower': ('start <= datetime.fromisoformat', 'datetime.fromisoformat'),
        'personal-owner': ("total({'assistant', 'document'}, actor.user_id)", "total({'assistant', 'document'})"),
        'shared-owner': ("total({'lecture', 'quiz_gen', 'quiz_verify'})", "total({'lecture', 'quiz_gen', 'quiz_verify'}, actor.user_id)"),
        'month-upper': (' AND queued_at<:end', ''),
        'month-lower': (' AND queued_at>=:start', ''),
        'dto': ("@router.get('/me/usage',response_model=MyUsage)", "@router.get('/me/usage',response_model=None)"),
    }
    if mutant in changes:
        old, new = changes[mutant]
        if old in source:
            assert source.count(old) == 1
            source = source.replace(old, new)
    ns = {'__name__': 'r7_scratch_' + relative.replace('/', '_')}
    exec(compile(source, str(WT / relative) + '#in-memory', 'exec'), ns)
    return SimpleNamespace(**ns)


@pytest.fixture
def modules(request):
    mutant = request.config.getoption('--w16-review-mutant')
    return SimpleNamespace(
        usage=load_source('src/web/backend/wayfinder/infrastructure/learning_usage.py', mutant),
        build=load_source('src/web/backend/wayfinder/infrastructure/build_store.py', mutant),
        api=load_source('src/web/backend/wayfinder/api/builds.py', mutant))


def stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds')


class SqlLedger:
    """Execute the real PG query-builder predicates on isolated SQLite rows."""
    def __init__(self):
        self.db = sqlite3.connect(':memory:', check_same_thread=False)
        self.db.execute('CREATE TABLE usage_ledger(id INTEGER PRIMARY KEY, purpose TEXT, learner_id TEXT, doc_id TEXT, created_at TEXT, extra TEXT)')
        self.calls = []

    def add(self, purpose, cost, at, owner='alice', doc='course-a', **extra):
        row = dict(purpose=purpose, cost_usd=cost, created_at=at.isoformat(), learner_id=owner, doc_id=doc, **extra)
        self.db.execute('INSERT INTO usage_ledger(purpose,learner_id,doc_id,created_at,extra) VALUES(?,?,?,?,?)',
                        (purpose, owner, doc, stamp(at), json.dumps(row)))

    def usage_rows(self, doc_id=None, *, learner_id=None, since=None, purposes=None):
        query = PostgresPhaseBStore._usage_query(None, doc_id, learner_id=learner_id, since=since, purposes=purposes)
        compiled = query.compile(dialect=postgresql.dialect(paramstyle='named'), compile_kwargs={'render_postcompile': True})
        params = {k: stamp(v) if isinstance(v, datetime) else v for k, v in compiled.params.items()}
        # PostgreSQL timezone cast syntax is erased only for the SQLite execution adapter.
        sql = str(compiled).replace('::TIMESTAMP WITH TIME ZONE', '').replace('::VARCHAR', '')
        rows = [json.loads(row[0]) for row in self.db.execute(sql, params)]
        self.calls.append({'owner': learner_id, 'purposes': sorted(purposes), 'row_count': len(rows), 'sql': str(compiled)})
        return rows


def runtime(ledger, now):
    return SimpleNamespace(store=ledger, clock=SimpleNamespace(now=lambda: now),
        settings=SimpleNamespace(spend_day_timezone='Asia/Ho_Chi_Minh', learner_daily_max_usd=1., system_daily_max_usd=5.))


@pytest.mark.parametrize('date', ['2026-10-31', '2026-12-31', '2028-02-29'])
def test_exact_day_bounds_and_reset(modules, date):
    now = datetime.fromisoformat(date + 'T16:59:00+00:00')
    reset = now.replace(hour=17, minute=0)
    start = reset - timedelta(days=1)
    ledger = SqlLedger()
    ledger.add('assistant', 99, start - timedelta(microseconds=1))
    ledger.add('assistant', .2, start)
    ledger.add('document', .1, now)
    ledger.add('assistant', .4, reset)
    ledger.add('lecture', 5, reset)
    view = modules.usage.my_learning_usage(ACTOR, None, runtime(ledger, now))
    assert view['learner_today']['used_ratio'] == pytest.approx(.3)
    assert view['shared_content_today'] == {'limited': False}
    assert datetime.fromisoformat(view['learner_today']['resets_at']) == reset
    after = modules.usage.my_learning_usage(ACTOR, None, runtime(ledger, reset))
    assert after['learner_today']['used_ratio'] == pytest.approx(.4)
    assert after['shared_content_today'] == {'limited': True}
    assert datetime.fromisoformat(after['learner_today']['resets_at']) == reset + timedelta(days=1)
    # The real repository predicate removed the preceding-day row, with no projection flag involved.
    assert ledger.calls[0]['row_count'] == 3


def test_actor_purpose_course_trace_and_failure_aggregation(modules):
    now = datetime.fromisoformat('2026-10-26T05:00:00+00:00')
    ledger = SqlLedger()
    ledger.add('assistant', .2, now, doc='course-a')
    ledger.add('document', .3, now, doc='course-b', failed=True)
    ledger.add('assistant', .8, now, owner='bob')
    for purpose, amount in [('lecture', 2), ('quiz_gen', 1), ('quiz_verify', 2)]:
        ledger.add(purpose, amount, now, owner='bob', failed=True)
    for purpose in ['assistant', 'document', 'lecture', 'quiz_gen', 'quiz_verify']:
        ledger.add(purpose, 99, now, counted_in='build')
    ledger.add('build', 99, now)
    ledger.add('other', 99, now)
    ledger.add('assistant', 0, now, replayed=True)
    view = modules.usage.my_learning_usage(ACTOR, None, runtime(ledger, now))
    assert view['learner_today']['used_ratio'] == pytest.approx(.5)
    assert view['shared_content_today'] == {'limited': True}
    assert [(c['owner'], c['purposes']) for c in ledger.calls] == [
        ('alice', ['assistant', 'document']), (None, ['lecture', 'quiz_gen', 'quiz_verify'])]
    bob = Actor('bob', 'user', True, 'active')
    other_view = modules.usage.my_learning_usage(bob, None, runtime(ledger, now))
    assert other_view['learner_today']['used_ratio'] == pytest.approx(.8)
    assert other_view['shared_content_today'] == {'limited': True}
    (OUT / 'aggregation-observable.json').write_text(json.dumps({'alice': view, 'bob': other_view, 'queries': ledger.calls}, indent=2), encoding='utf8')


@pytest.mark.parametrize('date', ['2026-01-31', '2026-12-31', '2028-02-29'])
@pytest.mark.parametrize('maximum', [None, 3])
def test_real_quota_sql_counts_exact_month_not_dollars(modules, date, maximum):
    now = datetime.fromisoformat(date + 'T16:59:00+00:00')
    start = modules.build.month_start(now)
    end = (start + timedelta(days=32)).replace(day=1)
    db = sqlite3.connect(':memory:', check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE account(id TEXT, build_monthly_max INTEGER)')
    db.execute('CREATE TABLE build(requested_by TEXT,counts_quota INTEGER,queued_at TEXT,spent_usd REAL,status TEXT)')
    db.execute('INSERT INTO account VALUES(?,?)', ('alice', maximum))
    rows = [('alice', 1, start, .01, 'failed'), ('alice', 1, now, 81.33, 'succeeded'),
            ('alice', 0, now, 0., 'succeeded'), ('bob', 1, now, 2., 'failed'),
            ('alice', 1, start - timedelta(microseconds=1), 1., 'failed'),
            ('alice', 1, end, 1., 'failed')]
    db.executemany('INSERT INTO build VALUES(?,?,?,?,?)', [(u,c,stamp(t),cost,status) for u,c,t,cost,status in rows])
    store = modules.build.PostgresBuildStore.__new__(modules.build.PostgresBuildStore)
    queries = []
    def one(sql, params):
        queries.append(sql)
        converted = {k: stamp(v) if isinstance(v, datetime) else v for k,v in params.items()}
        row = db.execute(sql, converted).fetchone()
        return dict(row) if row else None
    store.one = one
    view = store.quota('alice', now, None)
    assert view == {'builds_used': 2, 'build_monthly_max': maximum,
                    'builds_remaining': None if maximum is None else 1}
    assert db.execute('SELECT sum(spent_usd) FROM build WHERE requested_by=? AND queued_at>=? AND queued_at<? AND counts_quota', ('alice', stamp(start), stamp(end))).fetchone()[0] == pytest.approx(81.34)
    assert store.quota('alice', end, None)['builds_used'] == 1
    db.execute('UPDATE account SET build_monthly_max=1 WHERE id=?', ('alice',))
    assert store.quota('alice', now, 5)['builds_remaining'] == 0
    (OUT / 'quota-observable.json').write_text(json.dumps({'view': view, 'queries': queries}, indent=2), encoding='utf8')


def assert_no_money(value):
    if isinstance(value, dict):
        assert not [key for key in value if any(s in key.lower() for s in ['usd','cost'])]
        for item in value.values(): assert_no_money(item)
    elif isinstance(value, list):
        for item in value: assert_no_money(item)


def test_actual_http_response_model_removes_private_nested_keys(modules, monkeypatch):
    from wayfinder.infrastructure import learning_usage
    now = datetime.fromisoformat('2026-10-26T05:00:00+00:00')
    ledger = SqlLedger()
    ledger.add('document', .35, now)
    rt = runtime(ledger, now)
    def private_projection(actor, engine, runtime):
        value = modules.usage.my_learning_usage(actor, engine, runtime)
        value['internal_cost_usd'] = 99
        value['learner_today']['cost_usd'] = 99
        value['shared_content_today']['debug'] = [{'provider_cost': 99}]
        return value
    monkeypatch.setattr(learning_usage, 'my_learning_usage', private_projection)
    app = FastAPI()
    app.state.services = SimpleNamespace(
        builds=SimpleNamespace(usage=lambda actor: {'builds_used': 2,'build_monthly_max': None,'builds_remaining': None}),
        learning=SimpleNamespace(courses=SimpleNamespace(store=SimpleNamespace(engine=None)), runtime=rt))
    app.dependency_overrides[get_actor] = lambda: ACTOR
    app.include_router(modules.api.build_router())
    with TestClient(app) as client:
        response = client.get('/api/v1/me/usage', params={'learner_id': 'bob'})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    view = response.json()
    assert_no_money(view)
    assert view['learner_today']['used_ratio'] == pytest.approx(.35)
    assert view['builds_this_month'] == {'used': 2, 'max': None, 'resets_at': '2026-11-01T00:00:00+07:00'}
    assert set(view['learner_today']) == {'used_ratio','limited','resets_at'}
    assert set(view['shared_content_today']) == {'limited'}
    (OUT / 'http-observable.json').write_text(json.dumps(view, indent=2), encoding='utf8')


def test_repository_rejects_naive_since():
    with pytest.raises(ValueError, match='timezone'):
        PostgresPhaseBStore._usage_query(None, since=datetime(2026,10,26))
