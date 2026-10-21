"""One queue consumer. BuildRunner and all external services are injected."""
import logging
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, Thread

from doc2roadmap.application.ports.build import BUILD_STEPS, BuildResult
from wayfinder.domain.file_paths import safe_path

logger=logging.getLogger(__name__)


class BuildWorker:
    def __init__(self,service,*,runner_factory,graph_loader,mailer,worker_id):
        self.service=service
        self.store,self.settings,self.clock=service.store,service.settings,service.clock
        self.runner_factory,self.graph_loader,self.mailer=runner_factory,graph_loader,mailer
        self.worker_id=worker_id

    def run_next_job(self):
        self.store.reclaim(self.clock.now(),self.settings)
        job=self.store.claim(self.worker_id,self.clock.now(),self.settings)
        if job is None: return None
        bid,lease=job['id'],job['lease_id']
        stopped,lost=Event(),Event()
        state={'cap':False,'recorded':False,'step':'doc_reading','result':None}

        def heartbeat():
            while not stopped.wait(30):
                try:
                    if not self.store.heartbeat(bid,lease,self.clock.now()): lost.set()
                except Exception:
                    lost.set()
                    logger.exception('Build heartbeat failed build=%s',bid)

        def cancelled():
            current=self.store.get_job(bid)
            state['cap']=self.store.cap_reached(self.clock.now(),self.settings.system_daily_build_max_usd)
            return lost.is_set() or current['lease_id']!=lease or current['cancel_requested'] or state['cap']

        def progress(step,data):
            if step not in BUILD_STEPS: raise ValueError('Unknown build step')
            if data.get('status')=='started' and cancelled():
                raise InterruptedError('Build stopped at step boundary')
            state['step']=step
            if not self.store.checkpoint(bid,lease,step,self.clock.now()):
                lost.set()
                raise InterruptedError('Worker lease was revoked')
            if isinstance(data.get('usage'),dict):
                self.store.record_usage(bid,lease,data['usage'],self.clock.now(),step=step)

        def record(result):
            if state['recorded']: return
            if result.doc_id!=job['doc_id'] or result.pipeline_version!=job['pipeline_version']:
                raise ValueError('Runner result identity differs from queue job')
            if result.status not in {'succeeded','failed','rejected','cancelled'}:
                raise ValueError('Runner returned a nonterminal result')
            state['result']=result
            metadata=None
            if self.store.get_job(bid)['cancel_requested']:
                result.status='cancelled'
                result.error=None
            elif state['cap']:
                result.status='failed'
                result.error={'code':'het_tran_he_thong','message':'Đã chạm trần dựng hôm nay','retryable':True}
            if result.status=='succeeded':
                graph=self.graph_loader(job['doc_id'],result.graph_version)
                if graph.doc_id!=job['doc_id'] or graph.graph_version!=result.graph_version:
                    raise ValueError('Published graph does not match build result')
                metadata={'module_count':len(graph.modules)}
                self.publish_formula_images(job,lease)
                for asset in result.step_details.get('learning_prep',{}).get('confirmed_media',[]):
                    if asset.get('confirmed') is not True: continue
                    relative='media/'+job['doc_id']+'/'+asset['path']
                    path=safe_path(self.settings.artifact_root,relative)
                    self.publish_asset(job,lease,asset['asset_key'],path,'media')
            if result.error:
                code=result.error.get('code','loi_noi_bo')
                messages={'ban_quet':'Tài liệu không đủ văn bản; hãy chọn bản có chữ',
                    'chu_loi':'Văn bản của tài liệu bị lỗi','ngon_ngu_khong_ho_tro':'Chỉ hỗ trợ tài liệu tiếng Việt',
                    'loi_mang':'Kết nối bị gián đoạn; bạn có thể thử lại',
                    'het_tran_he_thong':'Đã chạm trần dựng hôm nay','loi_noi_bo':'Không thể hoàn tất bản dựng'}
                if code not in messages: code='loi_noi_bo'
                result.error={'code':code,'message':messages[code],'retryable':code in {'loi_mang','het_tran_he_thong'}}
            accepted=self.store.record_usage(bid,lease,result.to_dict(),self.clock.now(),result=result,metadata=metadata)
            state['recorded']=True
            if accepted and result.status in {'succeeded','failed','rejected'}:
                for recipient in self.store.recipients(bid):
                    try:
                        self.mailer.send(recipient['email'],'Bản dựng xong' if result.status=='succeeded' else 'Bản dựng lỗi',
                            f"Xem khoá học: {self.settings.public_base_url}/khoa-hoc/{recipient['course_id']}")
                    except Exception:
                        logger.exception('Build notification failed build=%s',bid)

        thread=Thread(target=heartbeat,daemon=True,name='build-heartbeat-'+bid)
        thread.start()
        try:
            with TemporaryDirectory(prefix='wayfinder-worker-') as directory:
                upload=self.store.one('SELECT * FROM upload WHERE id=:id',{'id':job['upload_id']})
                source=Path(directory)/('source.'+upload['kind'])
                downloaded=self.service.media.download(upload['public_id'],destination=source)
                if downloaded!=source: raise ValueError('MediaStore did not respect worker destination')
                if sha256(source.read_bytes()).digest()!=upload['sha256']:
                    raise ValueError('Downloaded source checksum differs from upload')
                runner=self.runner_factory(record)
                result=runner.execute(source,job['doc_id'],language='vi',progress=progress,cancelled=cancelled)
                if not state['recorded']: record(result)
        except Exception as exc:
            if not state['recorded']:
                # A raised exception has unknown usage; never pretend it proves zero cost.
                current=self.store.get_job(bid)
                result=state['result'] or BuildResult(job['doc_id'],'failed',job['pipeline_version'],usage_complete=False)
                result.status='cancelled' if current['cancel_requested'] else 'failed'
                result.error={'code':'loi_mang' if isinstance(exc,(ConnectionError,TimeoutError)) else 'loi_noi_bo',
                              'message':'Không thể hoàn tất bản dựng'}
                record(result)
                logger.exception('Build execution failed build=%s',bid)
        finally:
            stopped.set()
            thread.join(timeout=5)
        return self.store.get_job(bid)

    def publish_formula_images(self,job,lease):
        root=safe_path(self.settings.artifact_root,'phase_b/formula_images/'+job['doc_id'])
        if not root.exists(): return
        for path in sorted(root.rglob('*')):
            safe_path(root,path.relative_to(root).as_posix())
            if not path.is_file() or path.suffix.lower() not in {'.png','.webp','.jpg','.jpeg'}: continue
            key=path.relative_to(root).as_posix()
            self.publish_asset(job,lease,key,path,'formula')

    def publish_asset(self,job,lease,key,path,kind):
        if self.store.one('SELECT asset_key FROM media_asset WHERE doc_id=:doc AND asset_key=:key',{'doc':job['doc_id'],'key':key}): return
        current=self.store.get_job(job['id'])
        if current['lease_id']!=lease: raise InterruptedError('Worker lease revoked')
        public=self.service.media.upload(path,self.settings.cloudinary_folder+'/media/'+job['doc_id'],'image')
        try:
            with self.store.atomic():
                current=self.store.one('SELECT * FROM build WHERE id=:id FOR UPDATE',{'id':job['id']})
                if current['lease_id']!=lease: raise InterruptedError('Worker lease revoked')
                self.store.put_asset(job['doc_id'],key,public,kind,path.stat().st_size,self.clock.now())
        except Exception:
            self.service.media.delete(public)
            raise
