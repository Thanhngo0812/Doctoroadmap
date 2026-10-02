from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from time import sleep

from doc2roadmap.infrastructure.llm.rate_limit import AdaptiveModelLimiter


def test_limiter_never_exceeds_in_flight_cap():
    limiter = AdaptiveModelLimiter(4, 1_000_000)
    barrier, lock = Barrier(4), Lock()
    active = peak = 0

    def call():
        nonlocal active, peak
        permit = limiter.acquire(10)
        with lock:
            active += 1
            peak = max(peak, active)
        barrier.wait()
        sleep(0.01)
        with lock:
            active -= 1
        limiter.release(permit, success=True)

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(lambda _: call(), range(12)))
    assert peak == limiter.max_observed == 4


def test_limiter_respects_rolling_token_budget_with_fake_clock():
    now = [0.0]
    limiter = AdaptiveModelLimiter(2, 100, clock=lambda: now[0], sleeper=lambda seconds: now.__setitem__(0, now[0] + seconds))
    first = limiter.acquire(80)
    limiter.release(first, success=True)
    second = limiter.acquire(30)
    assert now[0] >= 60
    limiter.release(second, success=True)


def test_limiter_respects_optional_request_budget_with_fake_clock():
    now = [0.0]
    limiter = AdaptiveModelLimiter(
        2,
        1_000_000,
        requests_per_minute=1,
        clock=lambda: now[0],
        sleeper=lambda seconds: now.__setitem__(0, now[0] + seconds),
    )
    first = limiter.acquire(1)
    limiter.release(first, success=True)
    second = limiter.acquire(1)
    assert now[0] >= 60
    limiter.release(second, success=True)


def test_limiter_halves_on_throttle_then_recovers():
    now = [0.0]
    limiter = AdaptiveModelLimiter(100, 1_000_000, recovery_successes=2,
                                   clock=lambda: now[0], sleeper=lambda seconds: now.__setitem__(0, now[0] + seconds),
                                   jitter=lambda: 0)
    failed = limiter.acquire(10)
    limiter.release(failed, success=False, throttled=True, retry_after=3)
    assert limiter.current_limit == 50
    recovered = limiter.acquire(10)
    assert now[0] >= 3
    limiter.release(recovered, success=True)
    recovered = limiter.acquire(10)
    limiter.release(recovered, success=True)
    assert limiter.current_limit == 51
