"""Commit ordering on separate PostgreSQL services, with synthetic nonzero usage."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from decimal import Decimal
import json
import os
from pathlib import Path
from threading import Event
from time import monotonic, sleep

import pytest

from test_builds_w14 import builds, sql, upload, worker
from wayfinder.api.errors import WebError
from wayfinder.application.builds import BuildService
from wayfinder.infrastructure.build_store import PostgresBuildStore
from wayfinder.infrastructure.database import create_database_engine

pytestmark = pytest.mark.postgres


@pytest.fixture(autouse=True)
def clear_registration_mail(builds):
    builds.mailer.messages.clear()


@contextmanager
def independent_service(b):
    engine = create_database_engine(b.postgres_database_url)
    try:
        service = BuildService(PostgresBuildStore(engine), settings=b.settings, media=b.media, clock=b.clock)
        assert sql(b, 'SELECT pg_backend_pid() AS pid')[0]['pid'] != service.store.one('SELECT pg_backend_pid() AS pid')['pid']
        yield service
    finally:
        engine.dispose()


def snapshot(b, bid, name, **observations):
    payload = {
        'kind': 'independent PostgreSQL SQL; synthetic usage; zero provider calls',
        'build': sql(b, 'SELECT * FROM build WHERE id=:id', {'id': bid})[0],
        'courses': sql(b, 'SELECT status,title,published_graph_version,module_count FROM course WHERE build_id=:id', {'id': bid}),
        'uploads': sql(b, 'SELECT confirmed_at FROM upload WHERE course_id IN (SELECT id FROM course WHERE build_id=:id)', {'id': bid}),
        'attempts': sql(b, 'SELECT * FROM build_attempt WHERE build_id=:id', {'id': bid}),
        'ledger': sql(b, "SELECT * FROM usage_ledger WHERE extra->>'build_id'=:id ORDER BY id", {'id': bid}),
        'assets': sql(b, 'SELECT * FROM media_asset WHERE doc_id=(SELECT doc_id FROM build WHERE id=:id)', {'id': bid}),
        'quota': b.service.usage(b.actor),
        'mail': b.mailer.messages,
        'observations': observations,
    }
    output = Path(__file__).parents[4] / 'report/w25-evidence/sql' / os.environ.get('W25_EVIDENCE_RUN', 'latest')
    output.mkdir(parents=True, exist_ok=True)
    (output / (name + '.json')).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    return payload


def test_cancel_commit_before_confirmation_queue_write_wins(builds, monkeypatch):
    # Coordinator repro, synchronized at the queue write instead of get_job call counts.
    b = builds
    item = upload(b)
    bid = item['build']['build_id']
    entered, resume = Event(), Event()
    original = b.store.execute

    def before_queue_write(statement, params=None):
        if statement.startswith("UPDATE build SET status='queued',queued_at="):
            entered.set()
            assert resume.wait(15), 'queue write was not released'
        return original(statement, params)

    monkeypatch.setattr(b.store, 'execute', before_queue_write)
    with independent_service(b) as cancel, ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(b.service.confirm_build, b.actor, item['upload_id'], title='Must roll back')
        try:
            assert entered.wait(15), 'confirmation did not reach its queue write'
            assert cancel.cancel_build(b.actor, bid)['status'] == 'cancelled'
            assert sql(b, 'SELECT status FROM build WHERE id=:id', {'id': bid})[0]['status'] == 'cancelled'
        finally:
            resume.set()
        try:
            pending.result(timeout=15)
        except WebError as error:
            assert error.code == 'conflict'
        else:
            # Save the erroneous committed SQL before the business assertion on old code.
            snapshot(b, bid, 'cancel-before-confirm')
            pytest.fail('confirmation must reject cancellation committed before its queue write')
    proof = snapshot(b, bid, 'cancel-before-confirm')
    assert proof['build']['status'] == 'cancelled' and proof['build']['cancel_requested']
    assert not proof['build']['counts_quota'] and proof['quota']['builds_used'] == 0
    assert proof['courses'][0]['status'] == 'failed' and proof['courses'][0]['title'] == 'book'
    assert proof['uploads'][0]['confirmed_at'] is None
    assert not proof['attempts'] and not proof['ledger']
    assert worker(b).run_next_job() is None


def test_confirmation_commit_before_cancel_keeps_used_quota(builds, monkeypatch):
    b = builds
    item = upload(b)
    bid = item['build']['build_id']
    entered, resume = Event(), Event()
    with independent_service(b) as cancel:
        original = cancel.store.execute

        def before_cancel_lock(statement, params=None):
            if statement == 'SELECT * FROM build WHERE id=:id FOR UPDATE':
                entered.set()
                assert resume.wait(15), 'cancel lock was not released'
            return original(statement, params)

        monkeypatch.setattr(cancel.store, 'execute', before_cancel_lock)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(cancel.cancel_build, b.actor, bid)
            try:
                assert entered.wait(15), 'cancel did not reach its state transition'
                assert b.service.confirm_build(b.actor, item['upload_id'])['status'] == 'queued'
                assert sql(b, 'SELECT status FROM build WHERE id=:id', {'id': bid})[0]['status'] == 'queued'
            finally:
                resume.set()
            assert pending.result(timeout=15)['status'] == 'cancelled'
    proof = snapshot(b, bid, 'confirm-before-cancel')
    assert proof['build']['status'] == 'cancelled' and proof['build']['counts_quota']
    assert proof['quota']['builds_used'] == 1
    assert proof['courses'][0]['status'] == 'failed'
    assert worker(b).run_next_job() is None


@pytest.mark.parametrize('boundary', ['graph', 'formula', 'media', 'terminal'])
@pytest.mark.parametrize('complete', [True, False], ids=['complete', 'incomplete'])
def test_cancel_commit_before_terminal_prevents_success_and_preserves_receipt(builds, monkeypatch, boundary, complete):
    b = builds
    item = upload(b)
    bid = item['build']['build_id']
    b.service.confirm_build(b.actor, item['upload_id'])
    doc = b.store.get_job(bid)['doc_id']
    initial_media = dict(b.media.files)
    paths = []
    for index in range(2):
        relative = (f'phase_b/formula_images/{doc}/{index}.png' if boundary == 'formula' else f'media/{doc}/{index}.png')
        path = b.settings.artifact_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'synthetic image')
        paths.append(path)

    def media_result(step, result):
        if step == 'learning_prep' and boundary == 'media':
            result.step_details['learning_prep'] = {'confirmed_media': [
                {'confirmed': True, 'path': path.name, 'asset_key': path.name} for path in paths]}

    consumer = worker(b, complete=complete, hook=media_result)
    entered, resume = Event(), Event()
    uploads = []

    def wait_for_cancel():
        entered.set()
        assert resume.wait(15), 'publication was not released'

    if boundary == 'graph':
        original = consumer.graph_loader

        def graph(doc, version):
            wait_for_cancel()
            return original(doc, version)

        consumer.graph_loader = graph
    elif boundary in {'formula', 'media'}:
        original = b.media.upload

        def media(path, folder, resource_type):
            public_id = original(path, folder, resource_type)
            uploads.append(public_id)
            if len(uploads) == 1:
                wait_for_cancel()
            return public_id

        monkeypatch.setattr(b.media, 'upload', media)
    else:
        # All worker-side checks have already passed. Only the locked terminal read can win.
        original = b.store.record_usage

        def terminal(*args, **kwargs):
            if kwargs.get('result') is not None:
                wait_for_cancel()
            return original(*args, **kwargs)

        monkeypatch.setattr(b.store, 'record_usage', terminal)

    with independent_service(b) as cancel, ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(consumer.run_next_job)
        try:
            assert entered.wait(15), 'worker did not reach publication boundary'
            assert cancel.cancel_build(b.actor, bid)['cancel_requested']
            assert sql(b, 'SELECT cancel_requested FROM build WHERE id=:id', {'id': bid})[0]['cancel_requested']
        finally:
            resume.set()
        pending.result(timeout=15)
    proof = snapshot(b, bid, f'cancel-{boundary}-{complete}')
    assert proof['build']['status'] == 'cancelled', proof
    assert proof['courses'][0]['status'] == 'failed'
    assert proof['courses'][0]['published_graph_version'] is None
    assert proof['courses'][0]['module_count'] == 0
    assert not proof['mail']
    assert proof['build']['spent_usd'] == Decimal('.003')
    assert proof['build']['model_calls'] == 3
    assert proof['build']['input_tokens'] == 300 and proof['build']['output_tokens'] == 60
    assert proof['build']['usage_complete'] == complete
    assert proof['quota']['builds_used'] == 1
    assert sum(row['cost_usd'] for row in proof['ledger']) == Decimal('.003')
    assert len(proof['attempts']) == 1 and proof['attempts'][0]['result']['status'] == 'cancelled'
    assert proof['attempts'][0]['usage_complete'] == complete
    assert proof['ledger'][-1]['failed']
    assert len([row for row in proof['ledger'] if row['extra']['step'] is None]) == 1
    if boundary in {'formula', 'media'}:
        assert len(uploads) == 1, 'stop before uploading another asset after cancellation'
        assert b.media.files == initial_media, 'delete only the newly uploaded, uncommitted asset'
        assert not proof['assets']
    assert all(not path.exists() for path in consumer.runners[0].sources)
    attempt = proof['attempts'][0]
    from doc2roadmap.application.ports.build import BuildResult
    duplicate = BuildResult(doc, 'succeeded', 'web-fake-v1', graph_version=8, spent_usd=.003)
    assert not b.store.record_usage(bid, str(attempt['lease_id']), duplicate.to_dict(), b.clock.now(), result=duplicate)
    after = snapshot(b, bid, f'duplicate-{boundary}-{complete}')
    assert len(after['ledger']) == len(proof['ledger'])
    assert after['build']['spent_usd'] == Decimal('.003') and after['build']['status'] == 'cancelled'


def test_terminal_commit_before_cancel_keeps_success_and_sends_one_mail(builds, monkeypatch):
    b = builds
    item = upload(b)
    bid = item['build']['build_id']
    b.service.confirm_build(b.actor, item['upload_id'])
    original = b.store.record_usage
    committed, resume = Event(), Event()

    def after_terminal(*args, **kwargs):
        accepted = original(*args, **kwargs)
        if kwargs.get('result') is not None:
            committed.set()
            assert resume.wait(15), 'terminal callback was not released'
        return accepted

    monkeypatch.setattr(b.store, 'record_usage', after_terminal)
    with independent_service(b) as cancel, ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(worker(b).run_next_job)
        try:
            assert committed.wait(15), 'worker did not commit its terminal transaction'
            assert sql(b, 'SELECT status FROM build WHERE id=:id', {'id': bid})[0]['status'] == 'succeeded'
            assert cancel.cancel_build(b.actor, bid)['status'] == 'succeeded'
        finally:
            resume.set()
        assert pending.result(timeout=15)['status'] == 'succeeded'
    proof = snapshot(b, bid, 'terminal-before-cancel')
    assert not proof['build']['cancel_requested']
    assert proof['courses'][0]['status'] == 'ready' and proof['courses'][0]['published_graph_version'] == 8
    assert proof['build']['spent_usd'] == sum(row['cost_usd'] for row in proof['ledger']) == Decimal('.003')
    assert len(proof['mail']) == 1 and proof['mail'][0]['subject'] == 'Bản dựng xong'


def test_cancelled_new_lease_cannot_be_published_by_late_old_receipt(builds):
    from doc2roadmap.application.ports.build import BuildResult
    b = builds
    item = upload(b)
    bid = item['build']['build_id']
    b.service.confirm_build(b.actor, item['upload_id'])
    first = b.store.claim('old', b.clock.now(), b.settings)
    b.clock.advance(601)
    assert b.store.reclaim(b.clock.now(), b.settings) == 1
    second = b.store.claim('new', b.clock.now(), b.settings)
    with independent_service(b) as cancel:
        assert cancel.cancel_build(b.actor, bid)['cancel_requested']
    old = BuildResult(first['doc_id'], 'succeeded', first['pipeline_version'], graph_version=8,
                      spent_usd=.009, usage_complete=False)
    assert not b.store.record_usage(bid, first['lease_id'], old.to_dict(), b.clock.now(), result=old)
    assert not b.store.record_usage(bid, first['lease_id'], old.to_dict(), b.clock.now(), result=old)
    running = sql(b, 'SELECT status,lease_id FROM build WHERE id=:id', {'id': bid})[0]
    assert running['status'] == 'reading' and str(running['lease_id']) == second['lease_id']
    current = BuildResult(first['doc_id'], 'succeeded', first['pipeline_version'], graph_version=8, spent_usd=.003)
    assert b.store.record_usage(bid, second['lease_id'], current.to_dict(), b.clock.now(), result=current)
    proof = snapshot(b, bid, 'stale-lease-after-cancel')
    assert proof['build']['status'] == 'cancelled' and not proof['build']['usage_complete']
    assert proof['build']['spent_usd'] == sum(row['cost_usd'] for row in proof['ledger']) == Decimal('.012')
    assert len(proof['attempts']) == 2 and len(proof['ledger']) == 2
    assert proof['courses'][0]['status'] == 'failed' and proof['courses'][0]['published_graph_version'] is None
    assert not proof['mail']


def test_terminal_row_read_and_cancel_follow_observed_commit_order(builds, monkeypatch):
    """If the terminal read loses its lock, cancel commits first and success must lose."""
    b = builds
    item = upload(b)
    bid = item['build']['build_id']
    b.service.confirm_build(b.actor, item['upload_id'])
    read, resume, cancel_committed, cancel_entered = Event(), Event(), Event(), Event()
    in_terminal = False
    original_record, original_execute = b.store.record_usage, b.store.execute

    def record(*args, **kwargs):
        nonlocal in_terminal
        in_terminal = kwargs.get('result') is not None
        try:
            return original_record(*args, **kwargs)
        finally:
            in_terminal = False

    def after_row_read(statement, params=None):
        rows = original_execute(statement, params)
        if in_terminal and statement.startswith('SELECT * FROM build WHERE id=:id'):
            read.set()
            assert resume.wait(15), 'terminal row read was not released'
        return rows

    monkeypatch.setattr(b.store, 'record_usage', record)
    monkeypatch.setattr(b.store, 'execute', after_row_read)
    blocked = False
    with independent_service(b) as cancel, ThreadPoolExecutor(max_workers=2) as pool:
        pid = []
        original_cancel = cancel.store.execute

        def cancel_lock(statement, params=None):
            if statement.startswith('SELECT * FROM build WHERE id=:id'):
                pid.append(original_cancel('SELECT pg_backend_pid() AS pid')[0]['pid'])
                cancel_entered.set()
            return original_cancel(statement, params)

        monkeypatch.setattr(cancel.store, 'execute', cancel_lock)

        def cancellation():
            response = cancel.cancel_build(b.actor, bid)
            cancel_committed.set()
            return response

        pending = pool.submit(worker(b).run_next_job)
        try:
            assert read.wait(15), 'worker never read its terminal row'
            cancelling = pool.submit(cancellation)
            assert cancel_entered.wait(15), 'cancel never attempted its state transition'
            deadline = monotonic() + 10
            while not cancel_committed.is_set() and monotonic() < deadline:
                blocked = bool(sql(b, 'SELECT pg_blocking_pids(:pid) AS blockers', {'pid': pid[0]})[0]['blockers'])
                if blocked:
                    break
                sleep(.01)
            assert blocked or cancel_committed.is_set(), 'neither a lock wait nor a committed cancellation was observed'
        finally:
            resume.set()
        response = cancelling.result(timeout=15)
        pending.result(timeout=15)
    proof = snapshot(b, bid, 'terminal-row-lock-order', blocking_observed=blocked,
                     cancellation_accepted=response['cancel_requested'])
    if response['cancel_requested']:
        assert proof['build']['status'] == 'cancelled'
        assert proof['courses'][0]['status'] == 'failed' and not proof['mail']
    else:
        assert blocked, 'success is valid only when cancellation waited for terminal commit'
        assert proof['build']['status'] == 'succeeded'
        assert proof['courses'][0]['status'] == 'ready' and len(proof['mail']) == 1
    assert proof['build']['spent_usd'] == sum(row['cost_usd'] for row in proof['ledger']) == Decimal('.003')
