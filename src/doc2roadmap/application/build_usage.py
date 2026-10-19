from __future__ import annotations

from contextlib import contextmanager
from threading import Lock


class BuildUsage:
    """Counters for calls made during this BuildPipeline instance's lifetime."""

    def __init__(self):
        self._values = {"model_calls": 0, "input_tokens": 0, "output_tokens": 0,
                        "spent_usd": 0.0, "usage_complete": True, "missing_usage_calls": 0}
        self._lock = Lock()

    def add(self, *, model_calls=0, input_tokens=0, output_tokens=0, spent_usd=0.0,
            usage_complete=True):
        with self._lock:
            self._values["model_calls"] += model_calls
            self._values["input_tokens"] += input_tokens
            self._values["output_tokens"] += output_tokens
            self._values["spent_usd"] += spent_usd
            self._values["usage_complete"] &= usage_complete
            if not usage_complete:
                self._values["missing_usage_calls"] += model_calls

    def snapshot(self):
        with self._lock:
            return dict(self._values)

    @contextmanager
    def capture(self, model_id):
        # Provider adapters already report every HTTP attempt and returned usage here.
        # Isolate each operation so parallel model jobs cannot contaminate their deltas.
        from doc2roadmap.application import stage_measurements
        from doc2roadmap.domain.phase_b_pricing import token_cost

        parent = stage_measurements._current.get()
        local = stage_measurements._Measurements("build_usage")
        token = stage_measurements._current.set(local)
        try:
            yield
        finally:
            snapshot = local.snapshot()
            stage_measurements._current.reset(token)
            with self._lock:
                self._values["model_calls"] += snapshot["model_calls"]
                self._values["input_tokens"] += snapshot["input_tokens"]
                self._values["output_tokens"] += snapshot["output_tokens"]
                self._values["spent_usd"] += token_cost(model_id, {
                    "input_tokens": snapshot["input_tokens"],
                    "output_tokens": snapshot["output_tokens"],
                })
                self._values["usage_complete"] &= snapshot["token_usage_complete"]
                self._values["missing_usage_calls"] += max(
                    0, snapshot["model_calls"] - snapshot["usage_responses"])
            if parent is not None:
                with parent.lock:
                    for key in ("model_calls", "input_tokens", "output_tokens", "embedding_model_calls",
                                "embedding_input_tokens"):
                        parent.counts[key] += local.counts[key]
                    parent.usage_responses += local.usage_responses


class MeteredModel:
    def __init__(self, model, usage):
        self._model, self._usage = model, usage

    def __getattr__(self, name):
        return getattr(self._model, name)

    def start_session(self, system_prompt):
        return MeteredSession(self._model.start_session(system_prompt), self._usage,
                              self._model.model_id)


class MeteredSession:
    def __init__(self, session, usage, model_id):
        self._session, self._usage, self._model_id = session, usage, model_id

    def __getattr__(self, name):
        return getattr(self._session, name)

    def ask_json(self, *args, **kwargs):
        with self._usage.capture(self._model_id):
            return self._session.ask_json(*args, **kwargs)


class MeteredEmbedding:
    def __init__(self, embedding, usage):
        self._embedding, self._usage = embedding, usage

    def __getattr__(self, name):
        return getattr(self._embedding, name)

    def embed(self, requests):
        with self._usage.capture(self._embedding.embedding_model_id):
            return self._embedding.embed(requests)
