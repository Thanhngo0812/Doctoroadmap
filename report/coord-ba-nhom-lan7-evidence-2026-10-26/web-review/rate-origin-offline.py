"""Offline production WebLearningRuntime tool boundary probe; no PG/provider."""
import sys,json
from pathlib import Path
ROOT=Path(r'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w10-quiz-documents')
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/web/backend')]
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
from wayfinder.fakes.lecture import ScriptedLectureModel
from wayfinder.testing import _sample_graph,FakeClock
store=InMemoryPhaseBStore(); graph=_sample_graph(); clock=FakeClock()
model=ScriptedLectureModel([['# Tài liệu\n\nNội dung [S1]']])
runtime=WebLearningRuntime(store,clock=clock,model_for=lambda purpose:model)
home={'kind':'module','module_id_at_creation':'m1','graph_version_at_creation':graph.graph_version,'node_ids':['a']}
owner='independent-r7-user'
for i in range(10):
    row=runtime.document(graph).create(graph.doc_id,graph.graph_version,graph,'Ôn tập',{'module_ids':['m1']},owner=owner,origin='button',home_scope=home,allow_spend=True)
    assert row['status']=='ready'
before_calls=len(model.calls)
assistant=runtime.assistant(graph)
row=assistant.content_tools['make_document']('Tạo thêm tài liệu','m1',owner=owner,home_scope=home,session_id='r7-session')
records=store.list_records('documents',owner=owner,doc_id=graph.doc_id)
result={'status':row['status'],'callsBeforeTool':before_calls,'callsAfterTool':len(model.calls),'documentCount':len(records),'assistantDocumentCount':sum(r['origin']=='assistant' for r in records),'sameHour':len({r['created_at'] for r in records})==1,'scope':'real runtime assistant tool closure + core document in memory; direct 10 core calls do not emulate PostgreSQL admission','costUSD':0}
assert result['status']=='ready' and result['callsAfterTool']==11 and result['documentCount']==11
print(json.dumps(result,ensure_ascii=False))
