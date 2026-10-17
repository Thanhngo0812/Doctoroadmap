import json
from copy import deepcopy
from io import BytesIO
from threading import Lock
from time import sleep
from types import SimpleNamespace

import pytest

from doc2roadmap.application.prerequisite_prompt import main_system_prompt
from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges
from doc2roadmap.config import Settings
from doc2roadmap.domain.canonical import digest
from doc2roadmap.infrastructure.llm.gemini import GeminiEntityExtractor
from doc2roadmap.infrastructure.llm.rate_limit import AdaptiveModelLimiter
from tests.unit.application.test_build_main_edges import Store


def chapter_store():
    store = Store()
    sections = [SimpleNamespace(section_id='ch', parent_section_id=None, level=1, order_index=0)]
    chunks, nodes = [], []
    for i, name in enumerate(['Alpha', 'Beta', 'Gamma', 'Delta']):
        sections.append(SimpleNamespace(section_id=f's{i}', parent_section_id='ch', level=2, order_index=i+1))
        chunks.append(SimpleNamespace(chunk_id=f'c{i}', text='Alpha is required before Beta',
                                      parent_section_id=f's{i}', order_index=i))
        nodes.append(dict(node_id='abcd'[i], name=name, learnable=True, cluster_id='g',
                          defining_chunk_ids=[f'c{i}']))
    store.chunks.result = SimpleNamespace(chunks=chunks, sections=sections)
    store.mentions.payload['nodes'] = nodes
    store.mentions.payload['mention_map'] = {c.chunk_id: {
        n['node_id']: {'level': 'definition', 'channels': ['provenance']} for n in nodes} for c in chunks}
    store.snapshots, store.history = [], []
    save_checkpoint, save_graph = store.save_checkpoint, store.save_graph
    def checkpoint(*args):
        save_checkpoint(*args)
        store.snapshots.append(deepcopy(args[-1]))
    def graph(*args, **kwargs):
        artifact = save_graph(*args, **kwargs)
        store.history.append(artifact)
        return artifact
    store.save_checkpoint, store.save_graph = checkpoint, graph
    store.find_graph = lambda doc, source, config: next((a for a in store.history
        if a.manifest['source_hash'] == source and a.manifest['config_hash'] == config), None)
    return store


def response(data, repair=False):
    return {'edges': [{'target': 'b', 'prerequisite': 'a' if not repair or data.get('repair_only') else 'outside',
                       'evidence_kind': 'noi_ro', 'chunk_ids': ['c0'], 'reason': 'fixture'}], 'flags': []}


class DelayedModel:
    model_id = 'fixture-model'

    def __init__(self, repair=False):
        self.lock, self.calls, self.prompts = Lock(), [], []
        self.active = self.peak = 0
        self.repair = repair

    def start_session(self, prompt):
        self.prompts.append(prompt)
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split('\nCorrect this validation error:')[0])
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.calls.append(data)
        sleep(.02 * (4 - int(data['session_id'][-1])))
        with self.lock:
            self.active -= 1
        return SimpleNamespace(payload=response(data, self.repair))


def run(store, model, **kwargs):
    return BuildMainEdges(store, model, single_session_limit=1, **kwargs).execute('doc', upstream=store.mentions)[0]


def test_default_parallel_sessions_keep_experiment_input_prompt_and_deterministic_results(monkeypatch):
    monkeypatch.delenv('DOC2ROADMAP_ROADMAP_MAIN_PARALLEL', raising=False)
    assert getattr(Settings(_env_file=None), 'roadmap_main_parallel', False) is True
    expected = run(chapter_store(), DelayedModel(repair=True), concurrency=1)
    store, model = chapter_store(), DelayedModel(repair=True)
    actual = run(store, model, concurrency=4)
    assert model.peak == 4
    assert len(model.calls) == 8 and sum(bool(c.get('repair_only')) for c in model.calls) == 4
    for call in model.calls:
        data = call.get('original_input', call)
        assert data['previous_edges_in_chapter'] == []
        assert data['previous_edges_omitted_count'] == 0
    assert set(model.prompts) == {main_system_prompt()}
    assert digest(actual.payload) == digest(expected.payload)
    assert [len(s['completed_main_sessions']) for s in store.snapshots] == [4]
    assert [r['input']['session_id'] for r in actual.payload['decision_log'] if r['stage'] == 'main'] == [f'main_section_s{i}' for i in range(4)]


def test_disabling_parallel_restores_previous_edges_and_sequential_chapter():
    model = DelayedModel()
    artifact = run(chapter_store(), model, concurrency=4, parallel_sessions=False)
    assert model.peak == 1 and len(model.calls) == 4
    assert model.calls[0]['previous_edges_in_chapter'] == []
    assert all([(e['source'], e['target']) for e in call['previous_edges_in_chapter']] == [('a', 'b')] for call in model.calls[1:])
    assert len(artifact.payload['main_edges']) == 1


def test_switch_changes_cache_and_checkpoint_identity_but_worker_count_does_not():
    store, model = chapter_store(), DelayedModel()
    legacy = run(store, model, parallel_sessions=False)
    parallel = run(store, model)
    assert legacy.manifest['config_hash'] != parallel.manifest['config_hash']
    assert legacy.manifest['config']['prompt_hash'] == parallel.manifest['config']['prompt_hash']
    assert len(model.calls) == 8
    assert run(store, model, concurrency=8) is parallel
    assert run(store, model, parallel_sessions=False) is legacy
    assert len(model.calls) == 8
    store.find_graph = lambda *args: None
    assert BuildMainEdges(store, model, single_session_limit=1).plan('doc', upstream=store.mentions).checkpoint_id != BuildMainEdges(
        store, model, single_session_limit=1, parallel_sessions=False).plan('doc', upstream=store.mentions).checkpoint_id


def test_parallel_resume_preserves_inputs_edges_and_executor_decisions():
    expected = run(chapter_store(), DelayedModel(), concurrency=4)
    store, model = chapter_store(), DelayedModel()
    save = store.save_checkpoint
    def interrupted(*args):
        save(*args)
        raise RuntimeError('interrupted after first checkpoint')
    store.save_checkpoint = interrupted
    with pytest.raises(RuntimeError, match='interrupted'):
        run(store, model, concurrency=4)
    assert len(store.snapshots[-1]['completed_main_sessions']) == 4
    store.save_checkpoint = save
    resumed = run(store, model, concurrency=4)
    assert len(model.calls) == 4
    for field in ('main_edges', 'main_flags', 'decision_log', 'executor_log', 'completed_main_sessions'):
        assert resumed.payload[field] == expected.payload[field]
    assert not store.checkpoints


def test_main_parallel_requests_still_obey_actual_extractor_limiter(monkeypatch):
    lock, active, peak = Lock(), 0, 0
    limiter = AdaptiveModelLimiter(2, 1_000_000)
    def fake_open(request, timeout):
        nonlocal active, peak
        data = json.loads(json.loads(request.data)['contents'][0]['parts'][0]['text'])
        with lock:
            active += 1
            peak = max(peak, active)
        sleep(.04)
        with lock:
            active -= 1
        return BytesIO(json.dumps({'candidates': [{'content': {'parts': [{'text': json.dumps(response(data))}]}}]}).encode())
    monkeypatch.setattr('doc2roadmap.infrastructure.llm.gemini.urlopen', fake_open)
    artifact = run(chapter_store(), GeminiEntityExtractor('fake-key', limiter=limiter), concurrency=4)
    assert peak == limiter.max_observed == 2
    assert len(artifact.payload['decision_log']) == 4 and len(artifact.payload['main_edges']) == 1


@pytest.mark.parametrize('enabled', [False, True])
def test_composition_passes_parallel_setting(tmp_path, monkeypatch, enabled):
    from doc2roadmap.composition import build_learning_graph
    settings = Settings(_env_file=None, artifact_dir=tmp_path, secondary_mode='llm', roadmap_main_parallel=enabled)
    monkeypatch.setattr('doc2roadmap.composition._a3_dependencies',
                        lambda: (settings, Store(), SimpleNamespace(limiter=None)))
    monkeypatch.setattr('doc2roadmap.composition.GeminiEntityExtractor', lambda *a, **k: DelayedModel())
    pipeline, _ = build_learning_graph()
    assert pipeline.main_edges.parallel_sessions is enabled
