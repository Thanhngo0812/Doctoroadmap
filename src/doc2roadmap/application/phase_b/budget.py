"""Daily spending checks include measured usage and calls still in flight."""
from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.domain.phase_b_limits import BSettings


class DailyLimitExceeded(RuntimeError):
    pass


class DailySpendGuard:
    def __init__(self, store, *, settings=None, clock=None):
        self.store = store
        self.settings = settings or BSettings()
        self.clock = clock or SystemClock()

    def check(self, purpose, estimated_usd, owner=None, *, at=None):
        personal = purpose in {"assistant", "document"}
        if not personal and purpose not in {"lecture", "quiz_gen", "quiz_verify"}:
            return True
        if personal and not owner:
            raise ValueError("learner_id is required for personal spending")
        purposes = {"assistant", "document"} if personal else {"lecture", "quiz_gen", "quiz_verify"}
        zone = ZoneInfo(self.settings.spend_day_timezone)
        today = (self.clock.today(self.settings.spend_day_timezone) if at is None
                 else at.astimezone(zone).date())
        with self.store.atomic():
            rows = [*self.store.usage_rows(), *self.store.list_records('spend_reservation')]
        spent = 0.0
        for row in rows:
            if row.get("purpose") not in purposes or (personal and row.get("learner_id") != owner):
                continue
            raw = row.get("created_at")
            if not raw:
                # Historic B1 rows predate timestamped daily accounting.
                continue
            at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if at.tzinfo is None:
                raise ValueError("usage created_at must include timezone")
            if at.astimezone(zone).date() == today:
                spent += float(row.get("cost_usd", 0))
        cap = self.settings.learner_daily_max_usd if personal else self.settings.system_daily_max_usd
        return spent + max(0.0, estimated_usd) <= cap + 1e-12

    def reserve(self, purpose, estimated_usd, owner=None):
        if purpose not in {'assistant', 'document', 'lecture', 'quiz_gen', 'quiz_verify'}:
            return None
        with self.store.atomic():
            admitted_at = self.clock.now()
            if not self.check(purpose, estimated_usd, owner, at=admitted_at):
                raise DailyLimitExceeded(purpose)
            token = uuid4().hex
            self.store.put_record('spend_reservation', token, {
                'purpose': purpose, 'learner_id': owner, 'cost_usd': max(0.0, estimated_usd),
                'created_at': admitted_at.isoformat(),
            })
            return token

    def release(self, token):
        if token is not None:
            with self.store.atomic():
                self.store.delete_record('spend_reservation', token)


@contextmanager
def spending_call(guard, purpose, estimated_usd, owner=None, *, replayed=False, clock=None):
    """Keep the reservation until the caller has recorded success or failure usage."""
    clock = clock or getattr(guard, 'clock', None) or SystemClock()
    if replayed:
        yield clock.now().isoformat()
        return
    # Check-only injected guards remain supported; production guards reserve.
    if not hasattr(guard, 'reserve'):
        if not guard.check(purpose, estimated_usd, owner):
            raise DailyLimitExceeded(purpose)
        yield clock.now().isoformat()
        return
    token = guard.reserve(purpose, estimated_usd, owner)
    try:
        reserved = guard.store.get_record('spend_reservation', token) if token else None
        yield reserved['created_at'] if reserved else clock.now().isoformat()
    finally:
        guard.release(token)
