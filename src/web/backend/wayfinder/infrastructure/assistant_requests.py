"""Atomic web turn admission and payload identity, using existing PostgreSQL tables."""
import json
import math
from contextlib import contextmanager
from datetime import timedelta

from sqlalchemy import text
import psycopg
from doc2roadmap.domain.phase_b_limits import context_hash
from wayfinder.api.errors import WebError


class AssistantRequests:
    def __init__(self, engine, settings, clock):
        self.engine, self.settings, self.clock = engine, settings, clock

    @contextmanager
    def serial(self, sid):
        # Dedicated lock connection: never occupy the query pool while a model is streaming.
        # A mutex must not coalesce different intents, unlike PhaseBStore.single_flight.
        url = self.engine.url.set(drivername='postgresql').render_as_string(hide_password=False)
        with psycopg.connect(url, autocommit=True) as c:
            c.execute("SELECT set_config('lock_timeout','120s',false)")
            c.execute('SELECT pg_advisory_lock(hashtextextended(%s,0))', ('web-session:' + sid,))
            try:
                yield
            finally:
                c.execute('SELECT pg_advisory_unlock(hashtextextended(%s,0))', ('web-session:' + sid,))

    def admit(self, actor, course, sid, key, question, focus):
        identity = context_hash([actor.user_id, course.doc_id, sid, key])
        payload = {'question': question, 'focus_node_id': focus}
        now = self.clock.now()
        bucket = 'assistant:' + actor.user_id
        with self.engine.begin() as c:
            c.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:bucket,0))'), {'bucket': bucket})
            old = c.scalar(text("SELECT value FROM phase_b_record WHERE kind='web_assistant_intent' AND record_id=:id"), {'id': identity})
            if old:
                if old['payload'] != payload:
                    raise WebError('conflict', 'Mã lượt hỏi đã dùng cho một câu hỏi khác. Hãy tạo lượt mới.')
                return
            times = list(c.scalars(text('SELECT at FROM rate_limit_event WHERE bucket=:bucket AND at>:since ORDER BY at'),
                {'bucket': bucket, 'since': now - timedelta(minutes=1)}))
            if len(times) >= self.settings.assistant_turns_per_minute:
                raise WebError('rate_limited', 'Bạn đang gửi câu hỏi quá nhanh. Hãy chờ một chút rồi thử lại.',
                    retry_after=max(1, math.ceil((times[0] + timedelta(minutes=1) - now).total_seconds())))
            c.execute(text('INSERT INTO rate_limit_event(bucket,at) VALUES(:bucket,:now)'), {'bucket': bucket, 'now': now})
            c.execute(text("INSERT INTO phase_b_record(kind,record_id,owner,doc_id,value) VALUES('web_assistant_intent',:id,:owner,:doc,cast(:value as jsonb))"),
                {'id': identity, 'owner': actor.user_id, 'doc': course.doc_id,
                 'value': json.dumps({'owner': actor.user_id, 'doc_id': course.doc_id, 'session_id': sid, 'payload': payload})})
