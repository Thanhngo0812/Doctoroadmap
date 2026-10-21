"""PostgreSQL serializes confirmation, deduplication and worker leases."""
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import json
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text

from wayfinder.api.errors import WebError
from wayfinder.infrastructure.course_store import PostgresCourseStore
from wayfinder.infrastructure.phase_b_schema import usage


def month_start(now):
    return now.astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).replace(day=1,hour=0,minute=0,second=0,microsecond=0)


def day_start(now):
    return now.astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).replace(hour=0,minute=0,second=0,microsecond=0)


class PostgresBuildStore(PostgresCourseStore):
    def execute(self, sql, params=None):
        with self._connection() as conn:
            result=conn.execute(text(sql), params or {})
            if result.returns_rows:
                return [{k:str(v) if isinstance(v,UUID) else v for k,v in row.items()}
                        for row in result.mappings()]
            return []

    def one(self, sql, params=None):
        rows=self.execute(sql,params)
        return rows[0] if rows else None

    def document_lock(self, doc, pipeline):
        self.execute('SELECT pg_advisory_xact_lock(hashtextextended(:key,0))',{'key':doc+':'+pipeline})

    def quota(self, uid, now, default, *, lock=False):
        account=self.one('SELECT build_monthly_max FROM account WHERE id=:uid'+(' FOR UPDATE' if lock else ''),{'uid':uid})
        maximum=account['build_monthly_max'] if account['build_monthly_max'] is not None else default
        used=self.one('SELECT count(*) AS n FROM build WHERE requested_by=:uid AND counts_quota AND queued_at>=:start',
                      {'uid':uid,'start':month_start(now)})['n']
        return {'builds_used':used,'build_monthly_max':maximum,
                'builds_remaining':None if maximum is None else max(0,maximum-used)}

    def check_quota(self,uid,now,default,*,lock=False):
        quota=self.quota(uid,now,default,lock=lock)
        if quota['builds_remaining']==0:
            raise WebError('quota_exceeded','Đã hết lượt dựng trong tháng')
        return quota

    def reusable(self, doc, pipeline):
        return self.one("SELECT * FROM build WHERE doc_id=:doc AND pipeline_version=:pipeline AND status IN "
            "('succeeded','awaiting_confirmation','queued','reading','running') ORDER BY (status='succeeded') DESC,created_at LIMIT 1",
            {'doc':doc,'pipeline':pipeline})

    def get_job(self, bid):
        return self.one('SELECT * FROM build WHERE id=:id',{'id':bid})

    def upload_for(self, uid, upload_id):
        try: upload_id=str(UUID(upload_id))
        except (ValueError,TypeError): return None
        return self.one('SELECT u.*,c.build_id FROM upload u JOIN course c ON c.id=u.course_id '
                        'WHERE u.id=:id AND u.account_id=:uid',{'id':upload_id,'uid':uid})

    def upload_for_build(self, uid, bid):
        try: bid=str(UUID(bid))
        except (ValueError,TypeError): return None
        return self.one('SELECT u.*,c.build_id FROM upload u JOIN course c ON c.id=u.course_id '
            'WHERE c.build_id=:id AND u.account_id=:uid ORDER BY u.created_at,u.id LIMIT 1',{'id':bid,'uid':uid})

    def expire(self,now):
        with self.atomic():
            rows=self.execute("UPDATE build SET status='cancelled',finished_at=:now,error_code='confirmation_expired',"
                "error_message='Đã hết hạn xác nhận dựng' WHERE status='awaiting_confirmation' AND confirmation_expires_at<=:now RETURNING id",{'now':now})
            for row in rows:
                self.execute("UPDATE course SET status='failed',updated_at=:now WHERE build_id=:id",{'id':row['id'],'now':now})

    def cap_reached(self,now,maximum):
        if maximum is None: return False
        total=self.one("SELECT coalesce(sum(cost_usd),0) AS total FROM usage_ledger WHERE purpose='build' AND created_at>=:start",{'start':day_start(now)})['total']
        return total>=Decimal(str(maximum))

    def claim(self,worker,now,settings):
        self.expire(now)
        with self.atomic():
            self.execute('SELECT pg_advisory_xact_lock(140006)')
            if self.cap_reached(now,settings.system_daily_build_max_usd): return None
            row=self.one("SELECT * FROM build WHERE status='queued' AND NOT cancel_requested ORDER BY queued_at,id FOR UPDATE SKIP LOCKED LIMIT 1")
            if row is None: return None
            lease=str(uuid4())
            row=self.one("UPDATE build SET status='reading',step='doc_reading',claim_count=claim_count+1,"
                "claimed_by=:worker,lease_id=:lease,heartbeat_at=:now,started_at=coalesce(started_at,:now) WHERE id=:id RETURNING *",
                {'worker':worker,'lease':lease,'now':now,'id':row['id']})
            self.execute('INSERT INTO build_attempt(build_id,lease_id,claim_count) VALUES(:id,:lease,:claim)',{'id':row['id'],'lease':lease,'claim':row['claim_count']})
            return row

    def heartbeat(self,bid,lease,now):
        return bool(self.execute("UPDATE build SET heartbeat_at=:now WHERE id=:id AND lease_id=:lease AND status IN ('reading','running') RETURNING id",
                                 {'id':bid,'lease':lease,'now':now}))

    def reclaim(self,now,settings):
        with self.atomic():
            rows=self.execute("SELECT * FROM build WHERE status IN ('reading','running') AND heartbeat_at<:cutoff FOR UPDATE SKIP LOCKED",
                {'cutoff':now-timedelta(minutes=settings.build_heartbeat_timeout_minutes)})
            for row in rows:
                terminal=row['cancel_requested'] or row['claim_count']>=2
                status=('cancelled' if row['cancel_requested'] else 'failed') if terminal else 'queued'
                self.execute("UPDATE build SET status=:status,lease_id=NULL,usage_complete=false,"
                    "finished_at=:finish,error_code=:error,error_message=:message WHERE id=:id",
                    {'id':row['id'],'status':status,'now':now,'finish':now if terminal else None,
                     'error':'loi_noi_bo' if status=='failed' else None,
                     'message':'Worker mất nhịp tim quá số lần cho phép' if status=='failed' else None})
                if terminal:
                    self.execute("UPDATE course SET status='failed',updated_at=:now WHERE build_id=:id",{'id':row['id'],'now':now})
            return len(rows)

    def checkpoint(self,bid,lease,step,now):
        return bool(self.execute("UPDATE build SET status=:status,step=:step,heartbeat_at=:now "
            "WHERE id=:id AND lease_id=:lease AND status IN ('reading','running') RETURNING id",
            {'id':bid,'lease':lease,'step':step,'now':now,'status':'reading' if step=='doc_reading' else 'running'}))

    def record_usage(self,bid,lease,counters,now,*,step=None,result=None,metadata=None):
        """Progress counters are cumulative per attempt; final BuildResult is a delta per execution."""
        with self.atomic():
            job=self.one('SELECT * FROM build WHERE id=:id FOR UPDATE',{'id':bid})
            active=job['lease_id']==lease and job['status'] in ('reading','running')
            attempt=self.one('SELECT * FROM build_attempt WHERE build_id=:id AND lease_id=:lease FOR UPDATE',{'id':bid,'lease':lease})
            if attempt is None or attempt['result'] is not None: return False
            if not active and result is None: return False
            fields=('spent_usd','model_calls','input_tokens','output_tokens')
            complete=counters.get('usage_complete',True) and attempt['usage_complete']
            values={}
            for key in fields:
                value=counters.get(key)
                try: valid=not isinstance(value,bool) and value is not None and Decimal(str(value)).is_finite() and value>=0
                except (ValueError,TypeError,InvalidOperation): valid=False
                if valid and key!='spent_usd' and int(value)!=value: valid=False
                if not valid or (valid and Decimal(str(value))<attempt[key]):
                    complete=False
                    value=attempt[key]
                values[key]=Decimal(str(value)) if key=='spent_usd' else int(value)
            delta={key:values[key]-attempt[key] for key in fields}
            if result is not None or any(delta.values()):
                with self._connection() as conn:
                    conn.execute(usage.insert().values(created_at=now,purpose='build',doc_id=job['doc_id'],
                        learner_id=job['requested_by'],cost_usd=delta['spent_usd'],input_tokens=delta['input_tokens'],
                        output_tokens=delta['output_tokens'],failed=bool(result and result.status!='succeeded'),replayed=False,
                        extra={'created_at':now.isoformat(),'purpose':'build','doc_id':job['doc_id'],
                               'learner_id':job['requested_by'],'cost_usd':float(delta['spent_usd']),
                               'input_tokens':int(delta['input_tokens']),'output_tokens':int(delta['output_tokens']),
                               'build_id':bid,'user_id':job['requested_by'],'claim_count':attempt['claim_count'],'lease_id':lease,
                               'step':step,'model_calls':int(delta['model_calls']),'usage_complete':bool(complete),
                               'attribution_complete':step is not None}))
            params=values|{'id':bid,'lease':lease,'complete':bool(complete),
                          'result':json.dumps(result.to_dict()) if result else None}
            self.execute('UPDATE build_attempt SET spent_usd=:spent_usd,model_calls=:model_calls,input_tokens=:input_tokens,'
                'output_tokens=:output_tokens,usage_complete=usage_complete AND :complete,result=cast(:result AS jsonb) '
                'WHERE build_id=:id AND lease_id=:lease',params)
            self.execute('UPDATE build SET spent_usd=spent_usd+:spent_usd,model_calls=model_calls+:model_calls,'
                'input_tokens=input_tokens+:input_tokens,output_tokens=output_tokens+:output_tokens,usage_complete=usage_complete AND :complete WHERE id=:id',
                delta|{'id':bid,'complete':bool(complete)})
            if result:
                self.execute('UPDATE build SET elapsed_seconds=elapsed_seconds+:elapsed WHERE id=:id',
                             {'id':bid,'elapsed':result.elapsed_seconds})
            if result and active:
                error=result.error or {}
                self.execute('UPDATE build SET status=:status,finished_at=:now,heartbeat_at=:now,'
                    'error_code=:code,error_message=:message,retryable=:retryable,graph_version=:version,module_count=:modules WHERE id=:id',
                    {'id':bid,'status':result.status,'now':now,'elapsed':result.elapsed_seconds,'code':error.get('code'),
                     'message':error.get('message'),'retryable':error.get('retryable',False),'version':result.graph_version,
                     'modules':(metadata or {}).get('module_count',0)})
                self.execute('UPDATE course SET status=:status,published_graph_version=:version,module_count=:modules,updated_at=:now WHERE build_id=:id',
                    {'id':bid,'now':now,'status':'ready' if result.status=='succeeded' else 'failed',
                     'version':result.graph_version if result.status=='succeeded' else None,'modules':(metadata or {}).get('module_count',0)})
            return active

    def put_asset(self,doc,key,public_id,kind,size,now):
        self.execute('INSERT INTO media_asset(doc_id,asset_key,public_id,kind,bytes,created_at) '
            'VALUES(:doc,:key,:public,:kind,:size,:now) ON CONFLICT(doc_id,asset_key) DO NOTHING',
            {'doc':doc,'key':key,'public':public_id,'kind':kind,'size':size,'now':now})

    def recipients(self,bid):
        return self.execute('SELECT DISTINCT a.email,c.id AS course_id FROM course c JOIN account a ON a.id=c.owner_id '
                            'WHERE c.build_id=:id',{'id':bid})
