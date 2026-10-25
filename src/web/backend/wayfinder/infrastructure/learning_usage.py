"""Query learner-facing ratios from the canonical typed PostgreSQL ledger."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import text


def my_learning_usage(actor, engine, runtime):
    zone = ZoneInfo(runtime.settings.spend_day_timezone)
    day = runtime.clock.now().astimezone(zone).date()
    start = datetime.combine(day, time.min, tzinfo=zone)
    reset = datetime.combine(day + timedelta(days=1), time.min, tzinfo=zone)
    next_month = day.replace(day=28) + timedelta(days=4)
    month_reset = datetime.combine(next_month.replace(day=1), time.min, tzinfo=zone)
    with engine.connect() as c:
        personal = c.scalar(text("SELECT coalesce(sum(cost_usd),0) FROM usage_ledger WHERE learner_id=:owner AND created_at>=:start AND purpose IN ('assistant','document')"),
            {'owner': actor.user_id, 'start': start})
        shared = c.scalar(text("SELECT coalesce(sum(cost_usd),0) FROM usage_ledger WHERE created_at>=:start AND purpose IN ('lecture','quiz_gen','quiz_verify')"), {'start': start})
    ratio = float(personal) / runtime.settings.learner_daily_max_usd
    return {'contract_version': 'usage-1',
        'build_month_resets_at': month_reset.isoformat(),
        'learner_today': {'used_ratio': min(1.0, max(0.0, ratio)), 'limited': ratio >= 1.0, 'resets_at': reset.isoformat()},
        'shared_content_today': {'limited': float(shared) >= runtime.settings.system_daily_max_usd}}
