"""Execution telemetry, separate from semantic payloads and cache keys."""
from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
from threading import Lock
from time import perf_counter
import warnings


_current = ContextVar("stage_measurements", default=None)
_COUNTS = ("model_calls", "input_tokens", "output_tokens", "embedding_model_calls", "embedding_input_tokens")


class _Measurements:
    def __init__(self, name):
        self.name = name
        self.started = perf_counter()
        self.previous_seconds = 0
        self.previous_counts = dict.fromkeys(_COUNTS, 0)
        self.counts = dict.fromkeys(_COUNTS, 0)
        self.usage_responses = 0
        self.previous_usage_responses = 0
        self.history_complete = True
        self.checkpoint_key = None
        self.saved_checkpoints = set()
        self.loaded_paths = {}
        self.checkpoint_paths = {}
        self.lock = Lock()
        self.manifests = []
        self.phases = {}

    def snapshot(self):
        with self.lock:
            return {"runtime_seconds": self.previous_seconds + perf_counter() - self.started,
                    **{key: self.previous_counts[key] + self.counts[key] for key in _COUNTS},
                    "usage_responses": self.previous_usage_responses + self.usage_responses,
                    "token_usage_complete": self.previous_counts["model_calls"] + self.counts["model_calls"] == self.previous_usage_responses + self.usage_responses,
                    "measurement_history_complete": self.history_complete}

    def restore(self, value):
        if not value:
            self.history_complete = False  # old checkpoint has no timing/HTTP-attempt telemetry
            return
        if value.get("stage") != self.name:
            return
        # Several checkpoints in one stage describe the same cumulative run, not separate runs.
        self.previous_seconds = max(self.previous_seconds, value["runtime_seconds"])
        for key in _COUNTS:
            self.previous_counts[key] = max(self.previous_counts[key], value.get(key, 0))
        self.previous_usage_responses = max(self.previous_usage_responses, value.get("usage_responses", 0))
        self.history_complete &= value.get("measurement_history_complete", True)


def measure_stage(execute):
    @wraps(execute)
    def measured(*args, **kwargs):
        state = _Measurements(execute.__qualname__)
        token = _current.set(state)
        try:
            result = execute(*args, **kwargs)
            stats = state.snapshot()
            for store, path, manifest in state.manifests:
                manifest["stats"] = {**manifest.get("stats", {}), **stats}
                if state.phases:
                    manifest["phase_measurements"] = state.phases
                store._write(path / "manifest.json", manifest)
            return result
        except BaseException:
            # Keep completed work frozen; only flush time/HTTP usage of an unfinished batch.
            for store, path in state.checkpoint_paths.values():
                try:
                    if path.exists():
                        payload = store._read(path)
                        payload["stage_measurements"] = {"stage": state.name,
                            "checkpoint_key": state.checkpoint_key, **state.snapshot()}
                        store._write(path, payload, compact=True)
                except OSError as error:
                    warnings.warn(f"Could not flush stage measurements: {error}", RuntimeWarning)
            raise
        finally:
            _current.reset(token)
    return measured


@contextmanager
def measure_phase(name):
    """Accumulate phase time in the enclosing stage's manifest, outside payload/hash."""
    state, started = _current.get(), perf_counter()
    try:
        yield
    finally:
        if state is not None and name:
            phase = state.phases.setdefault(name, {"runtime_seconds": 0.0})
            phase["runtime_seconds"] += perf_counter() - started


def register_manifest(store, path, manifest):
    state = _current.get()
    if state is not None:
        manifest["stats"] = {**manifest.get("stats", {}), **state.snapshot()}
        state.manifests.append((store, path, manifest))


def checkpoint_measurements(payload, *, key, restore=False):
    state = _current.get()
    if state is None or payload is None:
        if state is not None and state.checkpoint_key is None:
            state.checkpoint_key = key
        return payload
    if state.checkpoint_key is None:
        state.checkpoint_key = key
    if restore:
        return payload
    state.saved_checkpoints.add(key)
    return {**payload, "stage_measurements": {"stage": state.name, "checkpoint_key": state.checkpoint_key, **state.snapshot()}}


def resume_measurements(checkpoint):
    """Call only after the stage has accepted checkpoint source/config provenance."""
    state = _current.get()
    if state is not None and checkpoint:
        value = checkpoint.get("stage_measurements", {})
        key = value.get("checkpoint_key", state.checkpoint_key)
        if key not in state.saved_checkpoints and key == state.checkpoint_key:
            state.restore(value)
            location = state.loaded_paths.get(id(checkpoint))
            if location:
                state.checkpoint_paths[str(location[1])] = location


def track_checkpoint(store, path, payload, *, loaded=False):
    state = _current.get()
    if state is not None and payload is not None:
        if loaded:
            state.loaded_paths[id(payload)] = (store, path)
        else:
            state.checkpoint_paths[str(path)] = (store, path)


def record_model_call(*, embedding=False):
    state = _current.get()
    if state is not None:
        with state.lock:
            state.counts["model_calls"] += 1
            if embedding:
                state.counts["embedding_model_calls"] += 1


def record_usage(usage, *, embedding=False):
    state = _current.get()
    if state is not None:
        with state.lock:
            if "promptTokenCount" in usage:
                state.usage_responses += 1
            state.counts["input_tokens"] += int(usage.get("promptTokenCount", 0))
            if embedding:
                state.counts["embedding_input_tokens"] += int(usage.get("promptTokenCount", 0))
            state.counts["output_tokens"] += int(usage.get("candidatesTokenCount", 0)) + int(usage.get("thoughtsTokenCount", 0))
