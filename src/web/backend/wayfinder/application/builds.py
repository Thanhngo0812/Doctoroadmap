"""User-facing build orchestration; all state is in the injected web store."""
from datetime import timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_raw

from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.application.ports.build import BUILD_STEPS
from wayfinder.api.errors import WebError
from wayfinder.domain.auth import decide
from wayfinder.domain.courses import Course, Membership


def inspect_file(content,settings):
    if len(content)>settings.upload_max_mb*1024*1024:
        raise WebError('file_too_large','Tài liệu quá lớn; hãy tách theo chương')
    if content.startswith(b'%PDF-'):
        try:
            with pdfium.PdfDocument(content) as reader:
                if pdfium_raw.FPDF_GetSecurityHandlerRevision(reader.raw)>=0:
                    raise WebError('file_encrypted','Tài liệu PDF được mã hoá')
                count=len(reader)
            if not count: raise ValueError('empty PDF')
            if settings.build_max_pages and count>settings.build_max_pages:
                raise WebError('too_many_pages','Tài liệu vượt số trang cho phép')
            return 'pdf',count
        except WebError: raise
        except pdfium.PdfiumError:
            if pdfium_raw.FPDF_GetLastError()==pdfium_raw.FPDF_ERR_PASSWORD:
                raise WebError('file_encrypted','Tài liệu PDF được mã hoá') from None
            raise WebError('file_invalid','Tệp PDF không hợp lệ') from None
        except Exception:
            raise WebError('file_invalid','Tệp PDF không hợp lệ') from None
    if content.startswith(b'PK\x03\x04'):
        try:
            with ZipFile(BytesIO(content)) as archive:
                names=archive.namelist()
                if not {'[Content_Types].xml','word/document.xml'}<=set(names): raise ValueError('not DOCX')
                if len(names)>10000 or sum(i.file_size for i in archive.infolist())>100*1024*1024:
                    raise ValueError('oversized DOCX container')
                if archive.testzip() is not None: raise ValueError('corrupt DOCX')
            return 'docx',None
        except (BadZipFile,ValueError,RuntimeError): pass
    raise WebError('file_invalid','Chỉ nhận tài liệu PDF hoặc DOCX hợp lệ')


class BuildService:
    def __init__(self,store,*,settings,media,clock=None,pipeline_version='web-fake-v1'):
        self.store,self.settings,self.media=store,settings,media
        self.clock=clock or SystemClock()
        self.pipeline_version=pipeline_version

    def authorize(self,actor):
        decision=decide(actor,'build',None,None)
        if not decision.allowed: raise WebError(decision.code,'Không có quyền thực hiện yêu cầu')

    def usage(self,actor):
        self.authorize(actor)
        return self.store.quota(actor.user_id,self.clock.now(),self.settings.build_monthly_max)

    def create_upload(self,actor,name,content,*,rights_confirmed):
        self.authorize(actor)
        if not rights_confirmed: raise WebError('validation','Cần xác nhận quyền sử dụng và chia sẻ tài liệu')
        kind,pages=inspect_file(content,self.settings)
        name=Path(name.replace('\\','/')).name[:255]
        if not name or any(ord(char)<32 for char in name):
            raise WebError('validation','Tên tài liệu không hợp lệ')
        digest=sha256(content).digest()
        doc='u-'+digest.hex()[:20]
        now=self.clock.now()
        self.store.expire(now)
        existing=self.store.reusable(doc,self.pipeline_version)
        if existing is None:
            self.store.check_quota(actor.user_id,now,self.settings.build_monthly_max)
        public=None
        try:
            with TemporaryDirectory(prefix='wayfinder-upload-') as directory:
                source=Path(directory)/('source.'+kind)
                source.write_bytes(content)
                public=self.media.upload(source,self.settings.cloudinary_folder+'/uploads','image' if kind=='pdf' else 'raw')
            upload_id,cid=str(uuid4()),str(uuid4())
            with self.store.atomic():
                self.store.document_lock(doc,self.pipeline_version)
                build=self.store.reusable(doc,self.pipeline_version)
                bid=build['id'] if build else str(uuid4())
                self.store.execute('INSERT INTO upload(id,account_id,course_id,sha256,original_name,kind,size_bytes,page_count,public_id,resource_type,rights_confirmed_at,created_at) '
                    'VALUES(:id,:uid,:cid,:sha,:name,:kind,:size,:pages,:public,:resource,:now,:now)',
                    {'id':upload_id,'uid':actor.user_id,'cid':cid,'sha':digest,'name':name,'kind':kind,'size':len(content),
                     'pages':pages,'public':public,'resource':'image' if kind=='pdf' else 'raw','now':now})
                if build is None:
                    self.store.execute("INSERT INTO build(id,doc_id,upload_id,requested_by,status,pipeline_version,confirmation_expires_at,created_at) "
                        "VALUES(:id,:doc,:upload,:uid,'awaiting_confirmation',:pipeline,:expires,:now)",
                        {'id':bid,'doc':doc,'upload':upload_id,'uid':actor.user_id,'pipeline':self.pipeline_version,
                         'expires':now+timedelta(hours=self.settings.confirmation_ttl_hours),'now':now})
                ready=bool(build and build['status']=='succeeded')
                course=Course(cid,actor.user_id,doc,Path(name).stem.strip()[:120] or 'Tài liệu','',
                    'ready' if ready else 'building',build['graph_version'] if ready else None,False,
                    build['module_count'] if ready else 0,public,now,now,build_id=bid)
                self.store.add_course(course)
                self.store.add_membership(Membership(cid,actor.user_id,'owner','owner',now,now))
            return self.get_upload(actor,upload_id)
        except Exception:
            if public: self.media.delete(public)
            raise

    def require_upload(self,actor,upload_id=None,*,build_id=None,course_id=None):
        self.authorize(actor)
        upload=(self.store.upload_for_build(actor.user_id,build_id,course_id) if build_id else self.store.upload_for(actor.user_id,upload_id))
        if upload is None: raise WebError('not_found','Không tìm thấy nội dung yêu cầu')
        return upload

    def get_upload(self,actor,upload_id):
        upload=self.require_upload(actor,upload_id)
        self.store.expire(self.clock.now())
        return {'contract_version':'upload-1','upload_id':upload['id'],'original_name':upload['original_name'],
                'kind':upload['kind'],'size_bytes':upload['size_bytes'],'page_count':upload['page_count'],
                'build':self._view(actor,upload,self.store.get_job(upload['build_id']))}

    def get_build(self,actor,bid,*,course_id=None):
        upload=self.require_upload(actor,build_id=bid,course_id=course_id)
        self.store.expire(self.clock.now())
        return self._view(actor,upload,self.store.get_job(bid))

    def course_build(self,actor,course):
        # Called only after CourseService has checked membership for this card.
        return self._view(actor,{'course_id':course.id},self.store.get_job(course.build_id))

    def _view(self,actor,upload,job):
        owner=job['requested_by']==actor.user_id
        return {'contract_version':'build-1','build_id':job['id'],'course_id':upload['course_id'],
            'status':job['status'],'step':job['step'],'step_index':BUILD_STEPS.index(job['step'])+1 if job['step'] else 0,
            'step_count':4,'started_at':job['started_at'],'finished_at':job['finished_at'],
            'confirmation_expires_at':job['confirmation_expires_at'],'cancel_requested':job['cancel_requested'],
            'can_cancel':owner and job['status'] in {'awaiting_confirmation','queued','reading','running'},
            'can_retry':owner and job['status']=='failed' and job['retryable'],
            'error':({'code':job['error_code'],'message':job['error_message'],'retryable':job['retryable']} if job['error_code'] else None)}

    def confirm_build(self,actor,upload_id,*,title=None):
        upload=self.require_upload(actor,upload_id)
        if title is not None and (not isinstance(title,str) or not 1<=len(title.strip())<=120):
            raise WebError('validation','Tên khoá phải có từ 1 đến 120 ký tự')
        now=self.clock.now()
        self.store.expire(now)
        with self.store.atomic():
            # Lock account first so two different documents cannot overrun the monthly quota.
            quota=self.store.quota(actor.user_id,now,self.settings.build_monthly_max,lock=True)
            job=self.store.get_job(upload['build_id'])
            self.store.document_lock(job['doc_id'],job['pipeline_version'])
            job=self.store.get_job(job['id'])
            upload=self.store.upload_for(actor.user_id,upload_id)
            if job['status']=='cancelled' and job['error_code']=='confirmation_expired':
                raise WebError('confirmation_expired','Đã hết hạn xác nhận; hãy tải lại tài liệu')
            if job['status'] in {'failed','rejected','cancelled'}:
                raise WebError('conflict','Bản dựng không thể xác nhận ở trạng thái này')
            if job['status']=='awaiting_confirmation':
                if quota['builds_remaining']==0: raise WebError('quota_exceeded','Đã hết lượt dựng trong tháng')
                # PostgreSQL rechecks this predicate after a concurrent cancellation commits.
                queued=self.store.execute("UPDATE build SET status='queued',queued_at=:now,requested_by=:uid,upload_id=:upload,counts_quota=true "
                    "WHERE id=:id AND status='awaiting_confirmation' AND NOT cancel_requested RETURNING id",
                    {'id':job['id'],'uid':actor.user_id,'upload':upload_id,'now':now})
                if not queued: raise WebError('conflict','Bản dựng không thể xác nhận ở trạng thái này')
            if upload['confirmed_at'] is None:
                if title is not None:
                    self.store.execute('UPDATE course SET title=:title,updated_at=:now WHERE id=:cid',
                        {'title':title.strip(),'now':now,'cid':upload['course_id']})
                self.store.execute('UPDATE upload SET confirmed_at=:now WHERE id=:id',{'now':now,'id':upload_id})
        return self._view(actor,upload,self.store.get_job(job['id']))

    def cancel_build(self,actor,bid,*,course_id=None):
        upload=self.require_upload(actor,build_id=bid,course_id=course_id)
        now=self.clock.now()
        with self.store.atomic():
            job=self.store.one('SELECT * FROM build WHERE id=:id FOR UPDATE',{'id':bid})
            if job['requested_by']!=actor.user_id: raise WebError('forbidden','Chỉ người yêu cầu dựng được huỷ việc dùng chung')
            if job['status'] in {'awaiting_confirmation','queued'}:
                self.store.execute("UPDATE build SET status='cancelled',cancel_requested=true,finished_at=:now WHERE id=:id",{'id':bid,'now':now})
                self.store.execute("UPDATE course SET status='failed',updated_at=:now WHERE build_id=:id",{'id':bid,'now':now})
            elif job['status'] in {'reading','running'}:
                self.store.execute('UPDATE build SET cancel_requested=true WHERE id=:id',{'id':bid})
        return self._view(actor,upload,self.store.get_job(bid))

    def retry_build(self,actor,bid,*,course_id=None):
        upload=self.require_upload(actor,build_id=bid,course_id=course_id)
        with self.store.atomic():
            job=self.store.get_job(bid)
            self.store.document_lock(job['doc_id'],job['pipeline_version'])
            job=self.store.one('SELECT * FROM build WHERE id=:id FOR UPDATE',{'id':bid})
            if job['requested_by']!=actor.user_id: raise WebError('forbidden','Chỉ người yêu cầu dựng được thử lại')
            if job['status']=='queued': return self._view(actor,upload,job)
            if job['status']!='failed' or not job['retryable']: raise WebError('conflict','Không thể thử lại bản dựng này')
            other=self.store.reusable(job['doc_id'],job['pipeline_version'])
            if other and other['id']!=bid: raise WebError('conflict','Đã có bản dựng khác cho tài liệu này')
            self.store.execute("UPDATE build SET status='queued',cancel_requested=false,claim_count=0,lease_id=NULL,"
                "finished_at=NULL,error_code=NULL,error_message=NULL,retryable=false WHERE id=:id",{'id':bid,'now':self.clock.now()})
            # Each retry receives a fresh lease UUID; previous usage receipts remain immutable.
            self.store.execute("UPDATE course SET status='building',updated_at=:now WHERE build_id=:id",{'id':bid,'now':self.clock.now()})
        return self._view(actor,upload,self.store.get_job(bid))
