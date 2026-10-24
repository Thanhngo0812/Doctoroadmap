from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from doc2roadmap.application.phase_b.budget import DailySpendGuard, DailyLimitExceeded
from doc2roadmap.application.phase_b.common import call_json
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.scope import module_scope, resolve_scope
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore


class FakeClock:
    def __init__(self, now=None):
        self.value = now or datetime(2026, 10, 18, 16, 59, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def today(self, timezone):
        return self.now().astimezone(ZoneInfo(timezone)).date()

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


def graphs():
    # Stable, split, and dispersed modules all retain their concepts in v2.
    old = {'stable': ['a'], 'split': ['b', 'c', 'd'], 'gone': ['e', 'f', 'g'], 'extra': ['x', 'y', 'z', 'u', 'v']}
    new = {'stable': ['a'], 'split': ['e', 'x', 'y'], 'part': ['b', 'c'],
           'tail': ['d', 'f', 'z'], 'last': ['g', 'u', 'v']}
    def graph(version, modules):
        return SimpleNamespace(doc_id='synthetic', graph_version=version,
                               modules={m: {'index': i, 'node_ids': ids} for i, (m, ids) in enumerate(modules.items())},
                               learnable_nodes={n: {'node_id': n} for ids in modules.values() for n in ids})
    return graph(1, old), graph(2, new)


def assert_split_contract(resolver):
    v1, v2 = graphs()
    saved = module_scope(v1, 'split')
    before = deepcopy(saved)
    assert resolver(saved, v2) == {'module_id': 'part', 'stale': False, 'jaccard': 2 / 3}
    assert saved == before


def test_scope_anchor_survives_split_and_stale_and_ties():
    v1, v2 = graphs()
    assert resolve_scope({'kind': 'roadmap'}, v2)['stale'] is False
    assert resolve_scope(module_scope(v1, 'stable'), v2)['module_id'] == 'stable'
    assert_split_contract(resolve_scope)
    assert resolve_scope(module_scope(v1, 'gone'), v2) == {'module_id': None, 'stale': True, 'jaccard': .2}
    tied = SimpleNamespace(modules={'later': {'index': 2, 'node_ids': ['b']},
                                   'earlier': {'index': 1, 'node_ids': ['c']}})
    assert resolve_scope({'kind': 'module', 'node_ids': ['b', 'c']}, tied)['module_id'] == 'earlier'
    assert resolve_scope(module_scope(v1, 'split'), v2, .8)['stale'] is True


def test_split_guard_rejects_mutant_using_saved_module_id():
    def wrong(saved, graph):
        return {'module_id': saved['module_id_at_creation'], 'stale': False, 'jaccard': 1.0}
    with pytest.raises(AssertionError):
        assert_split_contract(wrong)


@pytest.fixture(params=['memory', 'json'])
def store(request, tmp_path):
    return InMemoryPhaseBStore() if request.param == 'memory' else JsonPhaseBStore(tmp_path / 'b.json')


def test_store_delete_and_document_filter_contract(store):
    for id, owner, doc in [('one', 'alice', 'a'), ('two', 'alice', 'b'), ('three', 'bob', 'a')]:
        store.put_record('session', id, {'id': id, 'owner': owner, 'doc_id': doc})
    assert [r['id'] for r in store.list_records('session', 'alice', 'a')] == ['one']
    store.delete_record('session', 'one')
    store.delete_record('session', 'one')
    assert store.get_record('session', 'one') is None
    assert {r['id'] for r in store.list_records('session')} == {'two', 'three'}
    if hasattr(store, 'path'):
        assert JsonPhaseBStore(store.path).list_records('session', doc_id='b')[0]['id'] == 'two'


def test_progress_manual_choice_wins_and_remaps_modules(store):
    v1, v2 = graphs()
    progress = ProgressUseCase(store, v1, clock=FakeClock())
    progress.set_progress('alice', 'synthetic', 'b', True)
    progress.set_progress('alice', 'synthetic', 'b', False)
    progress.mark_quiz_correct('alice', 'synthetic', ['b', 'c'])
    values = progress.get_progress('alice', 'synthetic')
    assert values['nodes']['b']['state'] == 'not_learned'
    assert values['nodes']['b']['source'] == 'learner'
    assert values['nodes']['c']['state'] == 'learned'
    assert values['nodes']['c']['source'] == 'quiz'
    assert progress.get_progress('bob', 'synthetic')['nodes']['c']['state'] == 'not_learned'
    progress.mark_quiz_correct('alice', 'synthetic', [])
    v2_result = ProgressUseCase(store, v2).get_progress('alice', 'synthetic')
    assert next(m for m in v2_result['modules'] if m['module_id'] == 'part') == {'module_id': 'part', 'learned': 1, 'total': 2}
    with pytest.raises(PermissionError):
        progress.get_progress('', 'synthetic')
    with pytest.raises(ValueError):
        progress.set_progress('alice', 'other-doc', 'b', True)


def usage(store, clock, purpose, cost, learner=None):
    store.append_usage({'purpose': purpose, 'cost_usd': cost, 'learner_id': learner,
                        'created_at': clock.now().isoformat()})


def test_daily_cap_owner_timezone_and_settings(store):
    clock = FakeClock()
    guard = DailySpendGuard(store, clock=clock, settings=replace(BSettings(), learner_daily_max_usd=.20))
    usage(store, clock, 'assistant', .19, 'alice')
    usage(store, clock, 'document', .10, 'bob')
    assert not guard.check('document', .02, owner='alice')
    assert guard.check('assistant', .02, owner='bob')
    assert DailySpendGuard(store, clock=clock, settings=replace(BSettings(), learner_daily_max_usd=.3)).check('document', .02, 'alice')
    usage(store, clock, 'quiz_verify', 4.99)
    assert not guard.check('lecture', .02)
    assert guard.check('module_title', 20)
    clock.advance(120)  # Midnight in Ho Chi Minh, still the same UTC date.
    assert guard.check('document', .02, owner='alice')
    assert guard.check('quiz_gen', .02)


def test_ledger_rejects_unowned_rows_before_persist(store):
    for purpose in ['assistant', 'document']:
        with pytest.raises(ValueError, match='learner_id'):
            store.append_usage({'purpose': purpose, 'cost_usd': .01})
    assert store.usage_rows() == []


def test_common_blocks_before_model_and_uses_injected_clock(store):
    clock = FakeClock()
    class Model:
        model_id = BSettings().model_id
        calls = 0
        def ask_json(self, prompt, **kwargs):
            self.calls += 1
            return {'answer': 'ok'}
    model = Model()
    settings = replace(BSettings(), learner_daily_max_usd=.19)
    usage(store, clock, 'assistant', .19, 'alice')
    kwargs = dict(response_schema={}, store=store, purpose='document', doc_id='a', context_hash='test',
                  allow_spend=True, learner_id='alice', settings=settings, clock=clock,
                  spend_guard=DailySpendGuard(store, settings=settings, clock=clock))
    with pytest.raises(DailyLimitExceeded):
        call_json(model, 'explain', **kwargs)
    assert model.calls == 0
    clock.advance(120)
    call_json(model, 'explain', **kwargs)
    assert model.calls == 1
    assert store.usage_rows()[-1]['created_at'] == clock.now().isoformat()
