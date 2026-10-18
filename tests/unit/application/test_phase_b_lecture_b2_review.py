"""Cross-cutting B2 regressions found during integration review."""
import json
from dataclasses import replace
from threading import Event
from types import SimpleNamespace

from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_lecture_b2 import _graph, _Model, _payload


def test_timeout_after_open_gate_keeps_emitted_items_and_ready_status():
    release = Event()
    class Session:
        last_usage = {}
        last_finish_reason = 'STOP'
        def stream_json(self, prompt, *, response_schema):
            yield json.dumps(_payload()[0], ensure_ascii=False)
            release.wait(2)
    class Model:
        model_id = 'scripted'
        def start_session(self, _prompt):
            return Session()
    store, events = InMemoryPhaseBStore(), []
    try:
        result = LectureUseCase(Model(), store, settings=replace(BSettings(), lecture_click_timeout_seconds=.15)).make(
            'd1', 'g1', _graph(), 'a', allow_spend=True, on_event=events.append)
        emitted = [e['item'] for e in events if e['event'] == 'item' and e['section_kind'] == 'giai_thich']
        assert len(emitted) == 2
        assert result['status'] == 'ready'
        assert 'cat_ngan' in result['warnings']
        assert next(s['items'] for s in result['sections'] if s['kind'] == 'giai_thich') == emitted
        assert events[-1]['event'] == 'final'
    finally:
        release.set()


def test_failure_read_page_is_citation_target_and_failure_memo_has_no_learner_labels():
    graph, store = _graph(with_later=True), InMemoryPhaseBStore()
    progress = ProgressUseCase(store, graph)
    progress.set_progress('alice', 'd1', 'a', True)
    result = LectureUseCase(None, store, progress=progress).make('d1', 'g1', graph, 'b', owner='alice')
    page = result['failure']['read_page']
    assert isinstance(page, dict)
    assert page['page'] >= 1 and page['chunk_id'] in graph.chunks
    assert result['prerequisites'][0]['learner_status'] == 'learned'
    saved = store.get_record('lecture_failure', result['lecture_key'])['result']
    assert 'learner_status' not in json.dumps(saved)


def test_skeleton_event_retains_read_time_labels_after_ready_cache_write():
    graph, store = _graph(with_later=True), InMemoryPhaseBStore()
    progress = ProgressUseCase(store, graph)
    progress.set_progress('alice', 'd1', 'a', True)
    events = []
    result = LectureUseCase(_Model([_payload()[0]]), store, progress=progress).make(
        'd1', 'g1', graph, 'b', owner='alice', allow_spend=True, on_event=events.append)
    assert result['status'] == 'ready'
    assert events[0]['lecture']['prerequisites'][0]['learner_status'] == 'learned'
    assert 'learner_status' not in json.dumps(store.get_cache(result['lecture_key']))


def test_all_click_timings_share_the_click_start_including_skeleton_work(monkeypatch):
    from doc2roadmap.application.phase_b import lectures
    now = [0.0]
    assemble = lectures._assemble
    def slow_assemble(*args, **kwargs):
        result = assemble(*args, **kwargs)
        now[0] += .05
        return result
    monkeypatch.setattr(lectures, 'perf_counter', lambda: now[0])
    monkeypatch.setattr(lectures, '_assemble', slow_assemble)
    store = InMemoryPhaseBStore()
    LectureUseCase(_Model([_payload()[0]]), store).make('d1', 'g1', _graph(), 'a', allow_spend=True)
    timing = next(row for row in store.usage_rows() if row['purpose'] == 'lecture_timing')
    assert timing['skeleton_ms'] == 50
    assert timing['skeleton_ms'] <= timing['gate_ms'] <= timing['final_ms']


def test_repair_stream_network_error_after_gate_preserves_ready_items():
    class Model:
        model_id = 'scripted'
        calls = 0
        def start_session(self, _):
            self.calls += 1
            repair = self.calls > 1
            class Session:
                last_usage = {}
                last_finish_reason = 'STOP'
                def stream_json(self, prompt, *, response_schema):
                    yield json.dumps(_payload(explanation=[])[0] if not repair else _payload()[0])
                    if repair:
                        raise OSError('connection lost after repaired gate')
            return Session()
    events = []
    result = LectureUseCase(Model(), InMemoryPhaseBStore()).make(
        'd1', 'g1', _graph(), 'a', allow_spend=True, on_event=events.append)
    assert sum(e['event'] == 'item' for e in events) == 2
    assert result['status'] == 'ready'
    assert 'cat_ngan' in result['warnings']
    assert events[-1]['event'] == 'final'


def test_next_up_prefers_nearest_later_requires_and_excludes_other_edge_types():
    from doc2roadmap.application.phase_b.lectures import _next_up
    from doc2roadmap.domain.source_labels import SourceRegistry
    graph = SimpleNamespace(
        modules={f'm{i}': {'index': i, 'title': str(i)} for i in range(3)},
        nodes={name: {'module_id': module, 'name': name} for name, module in
               [('same', 'm0'), ('near', 'm1'), ('far', 'm2'), ('bad', 'm1')]},
        payload={'requires_edges': [{'source': 'a', 'target': name, 'edge_type': edge_type}
                for name, edge_type in [('same', 'requires'), ('bad', 'related'),
                                        ('far', 'requires'), ('near', 'requires')]]},
        chunks={})
    rows = _next_up(graph, 'a', 'm0', SourceRegistry([]), BSettings())
    assert [r['node_id'] for r in rows] == ['near', 'far']
    assert all('quote' not in r for r in rows)
