"""Account-wide rolling-hour admission for direct document requests."""
from datetime import timedelta
from math import ceil
from sqlalchemy import text
from wayfinder.api.errors import WebError


class DocumentRequests:
    def __init__(self, engine, settings, clock):
        self.engine, self.settings, self.clock = engine, settings, clock

    def admit(self, owner):
        now, bucket = self.clock.now(), 'document:' + owner
        with self.engine.begin() as c:
            c.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:bucket,0))'), {'bucket': bucket})
            times = list(c.scalars(text('SELECT at FROM rate_limit_event WHERE bucket=:bucket AND at>:since ORDER BY at'),
                {'bucket': bucket, 'since': now - timedelta(hours=1)}))
            if len(times) >= self.settings.documents_per_hour:
                raise WebError('rate_limited', 'Bạn đã tạo nhiều tài liệu trong giờ này. Hãy thử lại sau.',
                    retry_after=max(1, ceil((times[0] + timedelta(hours=1) - now).total_seconds())))
            c.execute(text('INSERT INTO rate_limit_event(bucket,at) VALUES(:bucket,:now)'), {'bucket': bucket, 'now': now})
