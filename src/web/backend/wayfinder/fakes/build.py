"""Scripted W-13 runner: synthetic usage is deliberately nonzero, never provider spend."""
from doc2roadmap.application.ports.build import BUILD_STEPS, BuildResult


class ScriptedBuildRunner:
    def __init__(self,*,recorder=None,pipeline_version='web-fake-v1',error=None,hook=None,complete=True):
        self.recorder,self.pipeline_version=recorder,pipeline_version
        self.error,self.hook,self.complete=error,hook,complete
        self.calls=0
        self.sources=[]
        self.started=[]

    def execute(self,file_path,doc_id,*,language='vi',progress=None,cancelled=None,dry_run=False):
        self.calls+=1
        self.sources.append(file_path)
        result=BuildResult(doc_id,'failed',self.pipeline_version)
        for index,step in enumerate(BUILD_STEPS):
            if cancelled and cancelled():
                result.status='cancelled'
                break
            self.started.append(step)
            if progress: progress(step,{'status':'started'})
            calls=index
            result.spent_usd=calls*.001
            result.model_calls=calls
            result.input_tokens=calls*100
            result.output_tokens=calls*20
            result.usage_complete=self.complete
            result.elapsed_seconds=index+.5
            if self.hook: self.hook(step,result)
            if self.error and step==self.error.get('stage','concepts'):
                result.status='rejected' if self.error['code'] in {'ban_quet','chu_loi','ngon_ngu_khong_ho_tro'} else 'failed'
                result.error=self.error
                break
            result.completed_steps.append(step)
            if step=='graph': result.graph_version=8
            if progress: progress(step,{'status':'completed','usage':result.to_dict()})
        else: result.status='succeeded'
        if self.recorder: self.recorder(result)
        return result
