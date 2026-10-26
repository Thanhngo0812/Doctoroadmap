"""Run actual web/core adapter with an isolated in-memory core store; no PostgreSQL/provider."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WORKER=ROOT.parent/'w10-quiz-documents'
sys.path[:0]=[str(ROOT/'backend'),str(WORKER/'src'),str(WORKER/'src/web/backend')]
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.application.ports.phase_b import ToolCall
from wayfinder.infrastructure.learning_runtime import WebLearningRuntime
from wayfinder.fakes.lecture import ScriptedLectureModel
from wayfinder.testing import _sample_graph,FakeClock
from wayfinder.api.errors import WebError
store=InMemoryPhaseBStore(); graph=_sample_graph(); clock=FakeClock()
model=ScriptedLectureModel([['# Tài liệu\n\nNội dung [S1]']])
runtime=WebLearningRuntime(store,clock=clock,model_for=lambda purpose:model)
class Admission:
    def __init__(self): self.owners=[]; self.limit=2; self.other=False
    def admit(self,owner):
        if self.other: raise WebError('forbidden','blocked')
        if len(self.owners)>=self.limit: raise WebError('rate_limited','Đã quá giờ',retry_after=123)
        self.owners.append(owner)
policy=Admission(); runtime.document_requests=policy
assistant=runtime.assistant(graph)
home={'kind':'module','module_id_at_creation':'m1','graph_version_at_creation':graph.graph_version,'node_ids':['a']}
owner='independent-r8-user'; artifacts=[]
def tool():
    return assistant._tool(graph,ToolCall('make_document',{'request':'Ôn tập','scope':'m1'},'r8'),module='m1',owner=owner,doc_id=graph.doc_id,graph_version=graph.graph_version,allow_spend=True,artifacts=artifacts,session_id='r8',session_scope=home)
first=tool(); second=tool(); before=len(model.calls); denied=tool()
observed={'allowed':len(artifacts),'beforeModelCalls':before,'afterModelCalls':len(model.calls),'owners':policy.owners,'denied':denied,'documents':len(store.list_records('documents',owner=owner,doc_id=graph.doc_id)),'costUSD':0,'scope':'actual runtime+WebAssistantUseCase+core generation; isolated stub admission, PostgreSQL checked separately by root'}
print(json.dumps(observed,ensure_ascii=True))
assert before==2 and len(model.calls)==2
assert len(artifacts)==2 and observed['documents']==2
assert denied['error']=={'code':'rate_limited','message':'Đã quá giờ','retry_after':123}
assert policy.owners==[owner,owner]
policy.other=True
try: tool()
except WebError as error: assert error.code=='forbidden'
else: raise AssertionError('non-rate errors must remain raised')
