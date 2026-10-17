import pytest

from doc2roadmap.application.phase_b.common import call_json
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def test_call_json_bills_thought_tokens_and_records_measured_usage():
    class Model:
        model_id = "scripted"

        def ask_json(self, prompt, *, response_schema, system_prompt=""):
            class Reply:
                payload = {"name": "title"}
                usage = {"promptTokenCount": 10, "candidatesTokenCount": 2, "thoughtsTokenCount": 4}
            return Reply()

    store = InMemoryPhaseBStore()
    result = call_json(Model(), "{}", response_schema={"type": "object"}, system_prompt="system",
                       store=store, purpose="module_title", doc_id="d1", context_hash="h", allow_spend=True)
    row = store.usage_rows("d1")[0]
    assert result.payload == {"name": "title"}
    assert row["thought_tokens"] == 4
    assert row["cost_usd"] == pytest.approx((10 * 0.25 + 6 * 1.5) / 1_000_000)


def test_failed_json_attempt_is_ledgered_once_and_dry_run_uses_system_prompt():
    class Broken:
        calls = 0

        def ask_json(self, prompt, *, response_schema, system_prompt=""):
            self.calls += 1
            raise RuntimeError("provider error")

    model = Broken()
    store = InMemoryPhaseBStore()
    with pytest.raises(RuntimeError):
        call_json(model, "{}", response_schema={"type": "object"}, system_prompt="long system",
                  store=store, purpose="module_title", doc_id="d1", context_hash="h", allow_spend=True)
    assert model.calls == 1
    assert len(store.usage_rows("d1")) == 1
    estimate = call_json(model, "{}", response_schema={"type": "object"}, system_prompt="long system",
                         store=store, purpose="module_title", doc_id="d1", context_hash="h", dry_run=True)
    assert estimate.dry_run
    assert estimate.usage["estimated_input_tokens"] > len("{}") // 3
    assert model.calls == 1
    assert len(store.usage_rows("d1")) == 1


def test_failed_session_json_decode_bills_usage_retained_on_session():
    class Session:
        last_usage = {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 5}

        def ask_json(self, prompt, *, response_schema):
            raise ValueError("invalid model payload")

    class Model:
        model_id = "scripted"

        def start_session(self, system_prompt):
            return Session()

    store = InMemoryPhaseBStore()
    with pytest.raises(ValueError):
        call_json(Model(), "{}", response_schema={"type": "object"}, store=store,
                  purpose="document", doc_id="d1", context_hash="ctx", allow_spend=True)
    [row] = store.usage_rows("d1")
    assert row["input_tokens"] == 100
    assert row["output_tokens"] == 20
    assert row["thought_tokens"] == 5
    assert row["cost_usd"] == pytest.approx((100 * .25 + 25 * 1.5) / 1_000_000)


def test_dry_run_quiz_estimates_use_overridden_shared_limits():
    class MustNotCall:
        def ask_json(self, *args, **kwargs):
            raise AssertionError("dry-run called a model")

    settings = BSettings(quiz_generation_max_output_tokens=77, quiz_verifier_max_output_tokens=23)
    store = InMemoryPhaseBStore()
    for purpose, cap in (("quiz_gen", 77), ("quiz_verify", 23)):
        result = call_json(MustNotCall(), "{}", response_schema={"type": "object"}, store=store,
                           purpose=purpose, doc_id="d", context_hash="h", dry_run=True,
                           settings=settings)
        assert result.usage["estimated_output_tokens"] == cap
    assert store.usage_rows("d") == []


def test_replayed_provider_tokens_are_recorded_without_new_spend():
    class Replay:
        is_replay = True
        model_id = 'gemini-3.1-flash-lite'

        def ask_json(self, prompt, *, response_schema):
            from types import SimpleNamespace
            return SimpleNamespace(payload={'ok': True}, usage={'promptTokenCount': 900,
                                    'candidatesTokenCount': 100, 'thoughtsTokenCount': 20})
    store = InMemoryPhaseBStore()
    result = call_json(Replay(), '{}', response_schema={'type': 'object'}, store=store,
                       purpose='document', doc_id='d', context_hash='h', allow_spend=True)
    assert result.cost_usd == 0
    assert store.usage_rows()[0]['cost_usd'] == 0
    assert store.usage_rows()[0]['replayed'] is True
