"""No network, application boot or credentials: the real web runtime with memory ports and scripted models."""
import json
import sys
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
WORK = SCRATCH.parent / 'w09-assistant'
sys.path[:0] = [str(WORK / 'src'), str(WORK / 'src/web/backend')]
from wayfinder.testing import FakeClock, ScriptedModel, _sample_graph
from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def exercise(forward_cache_only):
    graph, store, clock = _sample_graph(), InMemoryPhaseBStore(), FakeClock()
    model = ScriptedModel(tool_turns=[
        [ToolCall('get_lecture', {'concept': 'a'}, 'open-lecture'), Done({})],
        [Delta('Đã mở bài học.'), Done({})],
    ], text_replies=[['Nội dung bài giảng mới. [S1]']])
    runtime = WebLearningRuntime(store, model=model, clock=clock)
    sid = runtime.sessions(graph).create_session('reviewer', graph.doc_id, {'kind': 'roadmap'})['session_id']
    assistant = runtime.assistant(graph)
    if forward_cache_only:
        assistant.content_tools['get_lecture'] = lambda concept, **kwargs: runtime.lecture(graph).make(
            graph.doc_id, graph.graph_version, graph, concept, owner=kwargs.get('owner'),
            cache_only=kwargs.get('cache_only', False), allow_spend=kwargs.get('allow_spend', False))
    answer = assistant.ask(graph.doc_id, graph.graph_version, sid, 'Mở bài giảng tập hợp',
        owner='reviewer', client_turn_id='ordinary-lecture-review', allow_spend=True)
    summary = answer['tool_calls'][0]['result_summary']
    return {'toolResult': summary, 'lectureModelCalls': len(model.text_calls), 'answerStatus': answer['status']}


result = {'actualWebRuntime': exercise(False), 'canonicalForwardingControl': exercise(True)}
(SCRATCH / 'ordinary-lecture-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
assert result['actualWebRuntime']['toolResult']['status'] == 'ready', 'Ordinary get_lecture is incorrectly forced into cache_only and cannot generate the requested lesson'
