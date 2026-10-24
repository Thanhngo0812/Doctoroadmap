"""SA-70: the thinking level reaches the request body only when it is set, and record/replay carry it."""
import json

import pytest

from doc2roadmap.infrastructure.llm import phase_b
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel, ReplayToolModel
from test_phase_b_lecture3_client_sa64 import _Response, _events


def body_of(monkeypatch, **options):
    seen = {}
    monkeypatch.setattr(phase_b, "urlopen", lambda request, timeout: seen.setdefault("body", json.loads(request.data))
                        and _Response(_events("a")))
    list(GeminiToolModel("key", temperature=1.0, max_output_tokens=4096).start_session("s").stream_text("p", **options))
    return seen["body"]


def test_no_thinking_config_unless_a_level_is_given(monkeypatch):
    assert body_of(monkeypatch)["generationConfig"] == {"temperature": 1.0, "maxOutputTokens": 4096}
    assert body_of(monkeypatch, thinking_level=None)["generationConfig"] == {"temperature": 1.0, "maxOutputTokens": 4096}


def test_a_level_becomes_thinking_config(monkeypatch):
    config = body_of(monkeypatch, thinking_level="low")["generationConfig"]
    assert config["thinkingConfig"] == {"thinkingLevel": "low"} and config["temperature"] == 1.0


class _Delegate:
    last_usage, last_ttft_ms, last_finish_reason = {}, 1, "STOP"

    def __init__(self):
        self.options = []

    def start_session(self, system, tools=()):
        return self

    def stream_text(self, prompt, *, images=(), **options):
        self.options.append(options)
        yield "a"


def test_recording_passes_the_level_only_when_set_and_replay_refuses_a_different_one(tmp_path):
    delegate, path = _Delegate(), tmp_path / "t.json"
    session = RecordingToolModel(delegate, path, prompt_hash="h").start_session("s")
    list(session.stream_text("p", temperature=1.0, thinking_level="low"))
    list(session.stream_text("p", temperature=1.0))
    assert delegate.options == [{"temperature": 1.0, "thinking_level": "low"}, {"temperature": 1.0}]
    replay = ReplayToolModel(path, prompt_hash="h").start_session("s")
    assert list(replay.stream_text("p", temperature=1.0, thinking_level="low")) == ["a"]
    with pytest.raises(ValueError):
        list(replay.stream_text("p", temperature=1.0, thinking_level="high"))
