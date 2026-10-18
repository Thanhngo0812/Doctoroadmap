from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from doc2roadmap.application.phase_b.budget import DailySpendGuard
from doc2roadmap.application.phase_b.common import call_json
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


class CrossingMidnightClock:
    def __init__(self):
        self.at = datetime(2026, 10, 18, 16, 59, tzinfo=timezone.utc)
        self.calls = 0

    def now(self):
        self.calls += 1
        current = self.at
        if self.calls == 1:
            self.at += timedelta(minutes=2)
        return current

    def today(self, zone):
        return self.at.astimezone(ZoneInfo(zone)).date()


def test_usage_is_attributed_to_the_day_reservation_was_admitted():
    clock = CrossingMidnightClock()

    class Store(InMemoryPhaseBStore):
        reservation_created_at = None

        def put_record(self, kind, record_id, value):
            if kind == 'spend_reservation':
                self.reservation_created_at = value['created_at']
            super().put_record(kind, record_id, value)

    store = Store()
    settings = BSettings()
    guard = DailySpendGuard(store, settings=settings, clock=clock)

    class Model:
        model_id = settings.model_id

        def ask_json(self, prompt, **kwargs):
            return SimpleNamespace(payload={'ok': True}, usage={'candidatesTokenCount': 100})

    call_json(Model(), 'request', response_schema={}, store=store, purpose='document',
              doc_id='dev', context_hash='midnight', allow_spend=True,
              learner_id='alice', settings=settings, spend_guard=guard, clock=clock)

    row = store.usage_rows()[0]
    assert store.reservation_created_at is not None
    assert row['created_at'] == store.reservation_created_at
