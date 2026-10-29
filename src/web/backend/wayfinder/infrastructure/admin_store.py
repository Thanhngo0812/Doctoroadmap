from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, select, text, update

from wayfinder.infrastructure.auth_store import PostgresAuthStore, _account
from wayfinder.infrastructure.build_store import month_start


class PostgresAdminStore(PostgresAuthStore):
    def list_users(self, *, email, role, status, limit, offset, now, default_max):
        start = month_start(now)
        end = (start + timedelta(days=32)).replace(day=1)
        params = dict(email=email, role=role, status=status, limit=limit, offset=offset, start=start, end=end)
        where = '(:email=\'\' OR strpos(a.email_normalized,:email)>0) AND (CAST(:role AS text) IS NULL OR a.role=:role) AND (CAST(:status AS text) IS NULL OR a.status=:status)'
        with self._use_connection() as conn:
            total = conn.execute(text('SELECT count(*) FROM account a WHERE '+where), params).scalar_one()
            rows = conn.execute(text(self._user_select()+' WHERE '+where+' ORDER BY a.created_at DESC,a.id LIMIT :limit OFFSET :offset'),params).mappings()
            items = [self._summary(row, default_max, end) for row in rows]
        return dict(items=items,total=total,limit=limit,offset=offset)

    def user_summary(self, uid, now, default_max):
        start = month_start(now)
        end = (start+timedelta(days=32)).replace(day=1)
        with self._use_connection() as conn:
            row = conn.execute(text(self._user_select()+' WHERE a.id=:uid'),dict(uid=uid,start=start,end=end)).mappings().one()
            return self._summary(row, default_max, end)

    @staticmethod
    def _user_select():
        # Select only public columns, never load password/session/learning payloads.
        return '''SELECT a.id,a.email,a.display_name,a.role,a.status,a.email_verified_at,
            a.created_at,a.last_login_at,a.build_monthly_max,
            (SELECT a.id=ba.account_id FROM bootstrap_admin ba WHERE singleton) AS is_first_admin,
            (SELECT count(*) FROM course c WHERE c.owner_id=a.id) AS owned_courses,
            (SELECT count(*) FROM build b WHERE b.requested_by=a.id AND b.counts_quota
                AND b.queued_at>=:start AND b.queued_at<:end) AS builds_used FROM account a'''

    @staticmethod
    def _summary(row, default_max, end):
        item = {key: str(value) if isinstance(value, UUID) else value for key,value in row.items()}
        used = item.pop('builds_used')
        maximum = item['build_monthly_max'] if item['build_monthly_max'] is not None else default_max
        item['builds_this_month'] = dict(used=used,max=maximum,resets_at=end)
        return item

    def admin_count(self):
        table = self._table('account')
        with self._use_connection() as conn:
            return conn.scalar(select(func.count()).select_from(table).where(table.c.role=='admin',table.c.status=='active'))

    def update_user(self, uid, changes, at):
        table = self._table('account')
        with self._use_connection(write=True) as conn:
            return _account(conn.execute(update(table).where(table.c.id==uid).values(**changes,updated_at=at).returning(table)).mappings().one())

    def list_audit(self, *, actor_id, action, since, until, limit, offset):
        table = self._table('audit_event')
        predicates = []
        for column,value in ((table.c.actor_id,actor_id),(table.c.action,action)):
            if value is not None:
                predicates.append(column==value)
        if since is not None:
            predicates.append(table.c.at>=since)
        if until is not None:
            predicates.append(table.c.at<until)
        # Deliberately omit meta: even legacy arbitrary payloads cannot reach the API.
        columns = [table.c[key] for key in ('id','at','actor_id','action','target_kind','target_id','ip')]
        with self._use_connection() as conn:
            total = conn.scalar(select(func.count()).select_from(table).where(*predicates))
            rows = conn.execute(select(*columns).where(*predicates).order_by(table.c.at.desc(),table.c.id.desc()).limit(limit).offset(offset)).mappings()
            items = [{key:str(value) if isinstance(value,UUID) or key=='ip' and value is not None else value for key,value in row.items()} for row in rows]
        return dict(items=items,total=total,limit=limit,offset=offset)

    def list_builds(self, *, q, status, usage_complete, since, until, limit, offset):
        params = dict(q=q, status=status, usage_complete=usage_complete, since=since, until=until, limit=limit, offset=offset)
        where = ("(:q='' OR strpos(lower(b.doc_id),:q)>0 OR strpos(a.email_normalized,:q)>0 OR CAST(b.id AS text)=:q)"
            ' AND (CAST(:status AS text) IS NULL OR b.status=:status)'
            ' AND (CAST(:usage_complete AS boolean) IS NULL OR b.usage_complete=:usage_complete)'
            ' AND (CAST(:since AS timestamptz) IS NULL OR b.created_at>=:since)'
            ' AND (CAST(:until AS timestamptz) IS NULL OR b.created_at<:until)')
        join = ' FROM build b LEFT JOIN account a ON a.id=b.requested_by LEFT JOIN upload u ON u.id=b.upload_id WHERE '
        # Explicit allowlist of columns: error_message, claimed_by, lease_id, upload names/public ids and attempt results are never read.
        columns = '''SELECT b.id,b.doc_id,b.status,b.step,b.pipeline_version,b.counts_quota,b.cancel_requested,b.claim_count,
            b.created_at,b.queued_at,b.started_at,b.finished_at,b.error_code,b.retryable,b.spent_usd,b.model_calls,
            b.input_tokens,b.output_tokens,b.usage_complete,b.elapsed_seconds,b.graph_version,b.module_count,
            a.id AS requester_id,a.email AS requester_email,u.kind AS upload_kind,u.page_count AS upload_pages,
            u.size_bytes AS upload_size,(SELECT count(*) FROM course c WHERE c.build_id=b.id) AS course_count'''
        with self._use_connection() as conn:
            total = conn.execute(text('SELECT count(*)' + join + where), params).scalar_one()
            rows = conn.execute(text(columns + join + where + ' ORDER BY b.created_at DESC,b.id LIMIT :limit OFFSET :offset'), params).mappings()
            items = [{key: str(value) if isinstance(value, UUID) else value for key, value in row.items()} for row in rows]
        return dict(items=items, total=total, limit=limit, offset=offset)

    def lock_course(self, cid):
        with self._use_connection(write=True) as conn:
            row = conn.execute(text('SELECT id,doc_id,title,status,is_sample,published_graph_version,module_count,updated_at '
                'FROM course WHERE id=:cid FOR UPDATE'), dict(cid=cid)).mappings().first()
        return {key: str(value) if isinstance(value, UUID) else value for key, value in row.items()} if row else None

    def other_sample_exists(self, doc_id, cid):
        with self._use_connection() as conn:
            return conn.scalar(text('SELECT EXISTS(SELECT 1 FROM course WHERE is_sample AND doc_id=:doc AND id<>:cid)'),
                dict(doc=doc_id, cid=cid))

    def set_course_sample(self, cid, is_sample, at):
        with self._use_connection(write=True) as conn:
            row = conn.execute(text('UPDATE course SET is_sample=:flag,updated_at=:at WHERE id=:cid RETURNING id,doc_id,title,status,'
                'is_sample,published_graph_version,module_count,updated_at'), dict(flag=is_sample, at=at, cid=cid)).mappings().one()
        return {key: str(value) if isinstance(value, UUID) else value for key, value in row.items()}
