"""Exercise the actual web callback, with scripted providers and no external spend."""
import pytest

from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
from wayfinder.testing import FakeClock, ScriptedModel, _sample_graph


@pytest.mark.parametrize('cache_only', [None, False, True])
def test_w09_lecture_callback_respects_cache_flag_and_reuses_ready_content(cache_only):
    graph, store = _sample_graph(), InMemoryPhaseBStore()
    model = ScriptedModel(text_replies=[['Nội dung bài giảng mới. [S1]']])
    runtime = WebLearningRuntime(store, model=model, clock=FakeClock())
    kwargs = {} if cache_only is None else {'cache_only': cache_only}
    result = runtime.assistant(graph).content_tools['get_lecture']('a', owner='learner-a', allow_spend=True, **kwargs)
    assert result['status'] == ('not_cached' if cache_only else 'ready')
    assert len(model.text_calls) == (0 if cache_only else 1)
    if not cache_only:
        own = runtime.assistant(graph).content_tools['get_lecture']('a', owner='learner-a', cache_only=True)
        other = runtime.assistant(graph).content_tools['get_lecture']('a', owner='learner-b', cache_only=True)
        assert own['status'] == other['status'] == 'ready'
        assert own['lecture_key'] == other['lecture_key'] == result['lecture_key']
        assert len(model.text_calls) == 1


@pytest.mark.parametrize('allow_spend', [None, False, True])
def test_w09_lecture_callback_forwards_spend_permission_without_widening_it(monkeypatch, allow_spend):
    graph = _sample_graph()
    runtime = WebLearningRuntime(InMemoryPhaseBStore(), clock=FakeClock())
    calls = []
    class Reader:
        def make(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {'status': 'ready'}
    monkeypatch.setattr(runtime, 'lecture', lambda actual: Reader() if actual is graph else pytest.fail('wrong graph'))
    kwargs = {} if allow_spend is None else {'allow_spend': allow_spend}
    runtime.assistant(graph).content_tools['get_lecture']('a', owner='learner-a', cache_only=False, **kwargs)
    assert calls == [((graph.doc_id, graph.graph_version, graph, 'a'),
        {'owner': 'learner-a', 'cache_only': False, 'allow_spend': bool(allow_spend)})]


def test_w09_ordinary_assistant_tool_generates_an_uncached_lecture():
    graph, store = _sample_graph(), InMemoryPhaseBStore()
    model = ScriptedModel(tool_turns=[
        [ToolCall('get_lecture', {'concept': 'a'}, 'open-lecture'), Done({})],
        [Delta('Đã mở bài học.'), Done({})],
    ], text_replies=[['Nội dung bài giảng mới. [S1]']])
    runtime = WebLearningRuntime(store, model=model, clock=FakeClock())
    sid = runtime.sessions(graph).create_session('learner-a', graph.doc_id, {'kind': 'roadmap'})['session_id']
    answer = runtime.assistant(graph).ask(graph.doc_id, graph.graph_version, sid, 'Mở bài giảng tập hợp',
        owner='learner-a', client_turn_id='ordinary-lecture', allow_spend=True)
    assert answer['tool_calls'][0]['result_summary']['status'] == 'ready'
    assert 'Nội dung bài giảng mới' in answer['tool_calls'][0]['result_summary']['body_md']
    assert len(model.text_calls) == 1


@pytest.mark.parametrize('permission', [None, False])
def test_w09_uncached_ordinary_tool_cannot_generate_without_spend_permission(permission):
    graph, store = _sample_graph(), InMemoryPhaseBStore()
    model = ScriptedModel(text_replies=[['Must not be generated']])
    runtime = WebLearningRuntime(store, model=model, clock=FakeClock())
    kwargs = {} if permission is None else {'allow_spend': permission}
    result = runtime.assistant(graph).content_tools['get_lecture']('a', owner='learner-a', **kwargs)
    assert result['status'] == 'failed'
    assert not model.text_calls


def test_w09_focus_hit_and_miss_never_generate_and_keep_learner_status_private():
    graph, store = _sample_graph(), InMemoryPhaseBStore()
    model = ScriptedModel(tool_turns=[[Delta('Lượt đầu.'), Done({})], [Delta('Lượt sau.'), Done({})]],
        text_replies=[['FOCUS_CACHE_SENTINEL. [S1]']])
    runtime = WebLearningRuntime(store, model=model, clock=FakeClock())
    sid = runtime.sessions(graph).create_session('learner-a', graph.doc_id, {'kind': 'roadmap'})['session_id']
    assistant = runtime.assistant(graph)
    assistant.ask(graph.doc_id, graph.graph_version, sid, 'Đọc bài', owner='learner-a',
        client_turn_id='miss', focus_node_id='a', allow_spend=True)
    assert not model.text_calls
    assert 'FOCUS_CACHE_SENTINEL' not in str(model.tool_calls[-1])
    runtime.lecture(graph).make(graph.doc_id, graph.graph_version, graph, 'a', owner='learner-b', allow_spend=True)
    assistant.ask(graph.doc_id, graph.graph_version, sid, 'Đọc tiếp', owner='learner-a',
        client_turn_id='hit', focus_node_id='a', allow_spend=True)
    assert 'FOCUS_CACHE_SENTINEL' in str(model.tool_calls[-1])
    assert len(model.text_calls) == 1
