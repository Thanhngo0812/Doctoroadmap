"""Wall clock default; callers can inject a clock that advances in tests."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class SystemClock:
    def now(self):
        return datetime.now(timezone.utc)

    def today(self, timezone):
        return self.now().astimezone(ZoneInfo(timezone)).date()
