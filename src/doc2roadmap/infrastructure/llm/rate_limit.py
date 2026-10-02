from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from random import random
from threading import Condition
from time import monotonic, sleep
from typing import Callable


@dataclass(slots=True)
class _Permit:
    event: list[float]
    generation: int
    released: bool = False


class AdaptiveModelLimiter:
    """One process-wide gate for concurrent calls and a rolling token budget."""

    def __init__(
        self,
        max_in_flight: int,
        tokens_per_minute: int,
        *,
        requests_per_minute: int | None = None,
        clock: Callable[[], float] = monotonic,
        sleeper: Callable[[float], None] = sleep,
        jitter: Callable[[], float] = random,
    ) -> None:
        if max_in_flight < 2 or tokens_per_minute < 1 or (
            requests_per_minute is not None and requests_per_minute < 1
        ):
            raise ValueError("trần đồng thời phải từ 2; ngân sách mô hình phải dương")
        self.max_in_flight = max_in_flight
        self.tokens_per_minute = tokens_per_minute
        self.requests_per_minute = requests_per_minute
        self.current_limit = max_in_flight
        self._clock, self._sleep, self._jitter = clock, sleeper, jitter
        self._condition = Condition()
        self._active = self._success_streak = 0
        self._generation = 0
        self._events: deque[list[float]] = deque()
        self._blocked_until = 0.0
        self.max_observed = self.throttle_count = 0

    def _purge(self, now: float) -> None:
        while self._events and self._events[0][0] <= now - 60:
            self._events.popleft()

    def acquire(self, estimated_tokens: int) -> _Permit:
        tokens = min(max(int(estimated_tokens), 1), self.tokens_per_minute)
        while True:
            with self._condition:
                now = self._clock()
                self._purge(now)
                used = sum(event[1] for event in self._events)
                within_rpm = self.requests_per_minute is None or len(self._events) < self.requests_per_minute
                if (
                    now >= self._blocked_until
                    and self._active < self.current_limit
                    and used + tokens <= self.tokens_per_minute
                    and within_rpm
                ):
                    event = [now, float(tokens)]
                    self._events.append(event)
                    self._active += 1
                    self.max_observed = max(self.max_observed, self._active)
                    return _Permit(event, self._generation)
                waits = [0.05]
                if now < self._blocked_until:
                    waits.append(self._blocked_until - now)
                if self._events and used + tokens > self.tokens_per_minute:
                    waits.append(max(0.01, self._events[0][0] + 60 - now))
                if self._events and not within_rpm:
                    waits.append(max(0.01, self._events[0][0] + 60 - now))
                wait = max(waits) if now < self._blocked_until else min(waits)
            self._sleep(wait)

    def release(self, permit: _Permit, *, success: bool, throttled: bool = False, retry_after: float | None = None) -> None:
        with self._condition:
            if permit.released:
                return
            permit.released = True
            self._active -= 1
            if not success:
                try:
                    self._events.remove(permit.event)
                except ValueError:
                    pass
            if throttled:
                self.throttle_count += 1
                if permit.generation == self._generation:
                    self.current_limit = max(2, self.current_limit // 2)
                    self._generation += 1
                    self._success_streak = 0
                pause = retry_after if retry_after is not None else 1 + self._jitter()
                self._blocked_until = max(self._blocked_until, self._clock() + max(pause, 0))
            elif success:
                self._success_streak += 1
                if self._success_streak >= self.current_limit and self.current_limit < self.max_in_flight:
                    self.current_limit += 1
                    self._success_streak = 0
            self._condition.notify_all()

    def reconcile(self, permit: _Permit, actual_tokens: int) -> None:
        with self._condition:
            permit.event[1] = float(min(max(int(actual_tokens), 1), self.tokens_per_minute))
            self._condition.notify_all()

    def snapshot(self) -> dict[str, int | None]:
        with self._condition:
            return {
                "max_in_flight": self.max_in_flight,
                "current_limit": self.current_limit,
                "max_observed": self.max_observed,
                "throttle_count": self.throttle_count,
                "generation": self._generation,
                "tokens_per_minute": self.tokens_per_minute,
                "requests_per_minute": self.requests_per_minute,
            }
