"""Query learner-facing ratios from the canonical typed PostgreSQL ledger."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore


def my_learning_usage(actor, engine, runtime):
    zone = ZoneInfo(runtime.settings.spend_day_timezone)
    day = runtime.clock.now().astimezone(zone).date()
    start = datetime.combine(day, time.min, tzinfo=zone)
    reset = datetime.combine(day + timedelta(days=1), time.min, tzinfo=zone)
    next_month = day.replace(day=28) + timedelta(days=4)
    month_reset = datetime.combine(next_month.replace(day=1), time.min, tzinfo=zone)
    store = getattr(runtime, 'store', None) or PostgresPhaseBStore(engine)
    def total(purposes, owner=None):
        return sum(float(row.get('cost_usd') or 0) for row in
            store.usage_rows(learner_id=owner, since=start, purposes=purposes)
            if row.get('counted_in') != 'build' and row.get('created_at') and
            start <= datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) < reset)
    personal = total({'assistant', 'document'}, actor.user_id)
    shared = total({'lecture', 'quiz_gen', 'quiz_verify'})
    ratio = personal / runtime.settings.learner_daily_max_usd
    return {'contract_version': 'usage-1',
        'build_month_resets_at': month_reset.isoformat(),
        'learner_today': {'used_ratio': min(1.0, max(0.0, ratio)), 'limited': ratio >= 1.0, 'resets_at': reset.isoformat()},
        'shared_content_today': {'limited': float(shared) >= runtime.settings.system_daily_max_usd}}
