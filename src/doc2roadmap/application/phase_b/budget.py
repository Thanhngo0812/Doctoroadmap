"""Daily spending checks over measured, timestamped ledger entries."""
from datetime import datetime
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

    def check(self, purpose, estimated_usd, owner=None):
        personal = purpose in {"assistant", "document"}
        if not personal and purpose not in {"lecture", "quiz_gen", "quiz_verify"}:
            return True
        if personal and not owner:
            raise ValueError("learner_id is required for personal spending")
        purposes = {"assistant", "document"} if personal else {"lecture", "quiz_gen", "quiz_verify"}
        zone = ZoneInfo(self.settings.spend_day_timezone)
        today = self.clock.today(self.settings.spend_day_timezone)
        spent = 0.0
        for row in self.store.usage_rows():
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
