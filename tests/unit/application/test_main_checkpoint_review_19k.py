import json
from collections import Counter
from threading import Lock
from time import sleep
from types import SimpleNamespace

import pytest

from doc2roadmap.application.ports.extraction import ModelTransportError
from tests.unit.application.test_main_parallel_19k import chapter_store, response, run


@pytest.mark.parametrize('parallel,expected_writes', [(True, 1), (False, 2)])
def test_checkpoint_is_written_once_per_wave_with_its_final_state(parallel, expected_writes):
    store = chapter_store()
    store.chunks.result.sections.append(SimpleNamespace(section_id='ch2', parent_section_id=None, level=1, order_index=5))
    for section in store.chunks.result.sections:
        if section.section_id in ('s2', 's3'):
            section.parent_section_id = 'ch2'
    artifact = run(store, FailingModel(), concurrency=4, parallel_sessions=parallel)
    assert len(store.snapshots) == expected_writes
    last = store.snapshots[-1]
    for key in ('completed_main_sessions', 'main_edges', 'main_flags', 'decision_log', 'executor_log', 'model_metrics'):
        assert last[key] == artifact.payload[key]
    assert not store.checkpoints


class FailingModel:
    model_id = 'fixture-model'

    def __init__(self, fail_phase=None):
        self.fail_phase = fail_phase
        self.calls, self.returned, self.lock = Counter(), set(), Lock()
        self.active = self.peak = 0

    def start_session(self, prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split('\nCorrect this validation error:')[0])
        phase = 'repair' if data.get('repair_only') else 'main'
        key = phase, data['session_id']
        with self.lock:
            self.calls[key] += 1
            self.active += 1
            self.peak = max(self.peak, self.active)
        sleep(.015 * (1 + int(data['session_id'][-1])))
        with self.lock:
            self.active -= 1
            if self.fail_phase == phase and data['session_id'].endswith('1'):
                raise ModelTransportError('fixture transport failure')
            self.returned.add(key)
        return SimpleNamespace(payload=response(data, repair=True))


@pytest.mark.parametrize('phase', ['main', 'repair'])
def test_transport_failure_preserves_every_finished_call_and_reuses_it(phase):
    expected = run(chapter_store(), FailingModel(), concurrency=4)
    store, model = chapter_store(), FailingModel(phase)
    with pytest.raises(ModelTransportError, match='fixture transport failure'):
        run(store, model, concurrency=4)
    finished, counts_before = set(model.returned), model.calls.copy()
    assert len(finished) == (3 if phase == 'main' else 7)
    assert store.checkpoints and model.peak == 4
    model.fail_phase = None
    actual = run(store, model, concurrency=4)
    assert all(model.calls[key] == counts_before[key] for key in finished)
    assert sum(model.calls.values()) == 9
    for field in ('main_edges', 'main_flags', 'executor_log'):
        assert actual.payload[field] == expected.payload[field]
    clean = lambda rows: [{k: v for k, v in row.items() if k != 'reused'} for row in rows]
    assert clean(actual.payload['decision_log']) == clean(expected.payload['decision_log'])
    assert sum(row['reused'] for row in actual.payload['decision_log']) == len(finished)
    assert actual.manifest['config_hash'] == expected.manifest['config_hash']
    assert actual.payload['model_metrics']['main_calls'] == 4
    assert actual.payload['model_metrics']['main_repair_calls'] == 4
    assert not store.checkpoints


def many_store(count=24):
    store = chapter_store()
    for i in range(4, count):
        store.chunks.result.sections.append(SimpleNamespace(section_id=f's{i}', parent_section_id='ch', level=2, order_index=i+1))
        store.chunks.result.chunks.append(SimpleNamespace(chunk_id=f'c{i}', text='Alpha is required before Beta',
                                                        parent_section_id=f's{i}', order_index=i))
        node_id = f'n{i}'
        store.mentions.payload['nodes'].append(dict(node_id=node_id, name=node_id, learnable=True,
                                                   cluster_id='g', defining_chunk_ids=[f'c{i}']))
        store.mentions.payload['mention_map'][f'c{i}'] = {
            key: {'level': 'definition', 'channels': ['provenance']} for key in ('a', 'b', node_id)}
    return store


def test_progress_cache_is_throttled_and_separate_from_final_decision_log():
    store = many_store()
    artifact = run(store, FailingModel(), concurrency=4)
    partial = [s for s in store.snapshots if s.get('pending_model_results')]
    assert [len(s['pending_model_results']) for s in partial] == [16, 32, 48]
    assert all(s['completed_main_sessions'] == [] and s['decision_log'] == [] for s in partial)
    assert len(store.snapshots[-1]['completed_main_sessions']) == 24
    assert 'pending_model_results' not in store.snapshots[-1]
    assert len(artifact.payload['decision_log']) == 48


def test_transport_resume_also_reuses_completed_terminal_schema_failures():
    class Invalid(FailingModel):
        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split('\nCorrect this validation error:')[0])
            if data['session_id'].endswith('0') and not data.get('repair_only'):
                with self.lock:
                    self.calls['main', data['session_id']] += 1
                sleep(.005)
                return SimpleNamespace(payload={})
            return super().ask_json(prompt, response_schema=response_schema)
    expected = run(chapter_store(), Invalid(), concurrency=4)
    store, model = chapter_store(), Invalid('main')
    with pytest.raises(ModelTransportError):
        run(store, model, concurrency=4)
    assert model.calls['main', 'main_section_s0'] == 2
    model.fail_phase = None
    actual = run(store, model, concurrency=4)
    assert model.calls['main', 'main_section_s0'] == 2
    assert actual.payload['main_flags'] == expected.payload['main_flags']
    assert actual.payload['executor_log'] == expected.payload['executor_log']
    clean = lambda rows: [{k: v for k, v in row.items() if k != 'reused'} for row in rows]
    assert clean(actual.payload['decision_log']) == clean(expected.payload['decision_log'])


@pytest.mark.parametrize('phase', ['main', 'repair'])
@pytest.mark.parametrize('concurrency', [1, 4])
def test_persistent_transport_failure_cancels_queued_calls_and_resumes(phase, concurrency):
    class PersistentFailure(FailingModel):
        def __init__(self, fail_phase=None):
            super().__init__(fail_phase)
            self.transport_error = ModelTransportError('persistent transport failure')
            self.phase_calls = Counter()

        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split('\nCorrect this validation error:')[0])
            call_phase = 'repair' if data.get('repair_only') else 'main'
            key = call_phase, data['session_id']
            with self.lock:
                self.calls[key] += 1
                self.phase_calls[call_phase] += 1
                fail = call_phase == self.fail_phase and self.phase_calls[call_phase] >= 6
            sleep(.01)
            if fail:
                raise self.transport_error
            with self.lock:
                self.returned.add(key)
            return SimpleNamespace(payload=response(data, repair=True))

    expected = run(many_store(), PersistentFailure(), concurrency=concurrency)
    store, model = many_store(), PersistentFailure(phase)
    with pytest.raises(ModelTransportError) as caught:
        run(store, model, concurrency=concurrency)
    assert caught.value is model.transport_error
    assert 6 <= model.phase_calls[phase] <= 6 + 2 * concurrency
    assert model.phase_calls[phase] < 24  # Queued work actually remained unstarted.
    finished, before = set(model.returned), model.calls.copy()
    cached = list(store.checkpoints.values())[0]['pending_model_results']
    assert {(('repair' if row['input'].get('repair_only') else 'main'), row['input']['session_id'])
            for row in cached} == finished
    model.fail_phase = None
    actual = run(store, model, concurrency=concurrency)
    assert all(model.calls[key] == before[key] for key in finished)
    assert len(model.returned) == 48  # Cancelled sessions and repairs were eventually called.
    for field in ('main_edges', 'main_flags', 'executor_log'):
        assert actual.payload[field] == expected.payload[field]
    clean = lambda rows: [{k: v for k, v in row.items() if k != 'reused'} for row in rows]
    assert clean(actual.payload['decision_log']) == clean(expected.payload['decision_log'])
    assert actual.manifest['config_hash'] == expected.manifest['config_hash']
    assert not store.checkpoints
