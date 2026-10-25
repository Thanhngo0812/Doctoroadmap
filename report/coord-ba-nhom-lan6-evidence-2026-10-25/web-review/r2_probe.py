"""Independent no-DB/no-provider core callback probe, no worker source mutation."""
import json, socket, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=HERE.parent/'w09-assistant'
sys.path[:0]=[str(WORK/'src'),str(WORK/'src/web/backend')]
def deny(*args,**kwargs): raise AssertionError('Network forbidden in review probe')
socket.create_connection=deny
socket.socket.connect=deny
from wayfinder.testing import FakeClock, ScriptedModel, _sample_graph
from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
from doc2roadmap.application.ports.phase_b import Delta,Done,ToolCall
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
ns={}
exec(compile((HERE/'old_learning_runtime.py').read_text(),str(HERE/'old_learning_runtime.py'),'exec'),ns)
OldRuntime=ns['WebLearningRuntime']
def matrix(cls):
    rows=[]
    for cache in [None,False,True]:
      for permission in [None,False,True]:
        graph,store=_sample_graph(),InMemoryPhaseBStore()
        model=ScriptedModel(text_replies=[['INDEPENDENT_NEW_LECTURE. [S1]']])
        runtime=cls(store,model=model,clock=FakeClock())
        kwargs={'owner':'review-owner'}
        if cache is not None:kwargs['cache_only']=cache
        if permission is not None:kwargs['allow_spend']=permission
        result=runtime.assistant(graph).content_tools['get_lecture']('a',**kwargs)
        rows.append(dict(cache_only=cache,allow_spend=permission,status=result['status'],calls=len(model.text_calls)))
    return rows
current,old=matrix(WebLearningRuntime),matrix(OldRuntime)
for row in current:
    expected='not_cached' if row['cache_only'] else ('ready' if row['allow_spend'] else 'failed')
    assert row['status']==expected,row
    assert row['calls']==int(expected=='ready'),row
def ask(cls,focus=False):
    graph,store=_sample_graph(),InMemoryPhaseBStore()
    model=ScriptedModel(tool_turns=[[ToolCall('get_lecture',{'concept':'a'},'requested'),Done({})],[Delta('Done.'),Done({})]],text_replies=[['INDEPENDENT_NEW_LECTURE. [S1]']])
    runtime=cls(store,model=model,clock=FakeClock())
    sid=runtime.sessions(graph).create_session('review-owner',graph.doc_id,{'kind':'roadmap'})['session_id']
    result=runtime.assistant(graph).ask(graph.doc_id,graph.graph_version,sid,'Open requested lesson',owner='review-owner',client_turn_id='review-ordinary',allow_spend=True)
    return dict(status=result['tool_calls'][0]['result_summary']['status'],calls=len(model.text_calls))
actual,old_actual=ask(WebLearningRuntime),ask(OldRuntime)
assert actual==dict(status='ready',calls=1)
assert old_actual==dict(status='not_cached',calls=0)
graph,store=_sample_graph(),InMemoryPhaseBStore()
model=ScriptedModel(tool_turns=[[Delta('Focus miss.'),Done({})],[Delta('Focus hit.'),Done({})]],text_replies=[['INDEPENDENT_FOCUS_CACHE. [S1]']])
runtime=WebLearningRuntime(store,model=model,clock=FakeClock())
sid=runtime.sessions(graph).create_session('focus-owner',graph.doc_id,{'kind':'roadmap'})['session_id']
assistant=runtime.assistant(graph)
assistant.ask(graph.doc_id,graph.graph_version,sid,'Context',owner='focus-owner',client_turn_id='focus-miss',focus_node_id='a',allow_spend=True)
assert not model.text_calls
assert 'INDEPENDENT_FOCUS_CACHE' not in str(model.tool_calls[-1])
runtime.lecture(graph).make(graph.doc_id,graph.graph_version,graph,'a',owner='different-owner',allow_spend=True)
assistant.ask(graph.doc_id,graph.graph_version,sid,'Context again',owner='focus-owner',client_turn_id='focus-hit',focus_node_id='a',allow_spend=True)
assert len(model.text_calls)==1
assert 'INDEPENDENT_FOCUS_CACHE' in str(model.tool_calls[-1])
result=dict(current_matrix=current,old_matrix=old,ordinary_current=actual,ordinary_old=old_actual,focus_miss_calls=0,focus_hit_additional_calls=0,external_cost_usd=0)
(HERE/'r2-independent.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
