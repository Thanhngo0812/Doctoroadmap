import time
from types import SimpleNamespace

import pytest

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.domain.canonical import digest
from doc2roadmap.application.ports.extraction import ModelTransportError


class FakeModel:
    model_id = "fixture-model"

    def __init__(self, replies, delays=()):
        self.replies = iter(replies)
        self.delays = iter(delays)
        self.calls = 0

    def start_session(self, system_prompt):
        model = self

        class Session:
            def ask_json(self, prompt, *, response_schema):
                model.calls += 1
                time.sleep(next(model.delays, 0))
                value = next(model.replies)
                return SimpleNamespace(payload=value, raw_text=str(value))

        return Session()


def job(model, value, *, stage="judge"):
    return ModelJob(
        stage=stage,
        model=model,
        system_prompt="system",
        prompt_hash="prompt-v1",
        data={"value": value},
        schema={"type": "object"},
        validate=lambda output: output["ok"] is True or (_ for _ in ()).throw(ValueError("not ok")),
    )


def test_valid_cache_is_reused_without_a_call():
    model = FakeModel([])
    item = job(model, 1)
    key = digest([model.model_id, item.prompt_hash, item.data])
    cached = {"stage": "judge", "input_hash": key, "output": {"ok": True}, "valid": True}

    values, logs, metrics = run_model_jobs([item], [cached], concurrency=1)

    assert values == [{"ok": True}] and model.calls == 0
    assert logs[0]["reused"] is True and metrics["judge_reused"] == 1


def test_invalid_cache_is_replaced_and_records_validator_error():
    model = FakeModel([{"ok": True}])
    item = job(model, 1)
    key = digest([model.model_id, item.prompt_hash, item.data])
    cached = {"stage": "judge", "input_hash": key, "output": {"ok": False}, "valid": True}

    values, logs, metrics = run_model_jobs([item], [cached], concurrency=1)

    assert values == [{"ok": True}] and model.calls == 1
    assert logs[0]["reused"] is False and logs[0]["cache_invalid_error"] == "not ok"
    assert metrics["judge_cache_invalid"] == 1


def test_validation_failure_is_logged_then_retried_once():
    model = FakeModel([{"ok": False}, {"ok": True}])

    values, logs, metrics = run_model_jobs([job(model, 1)], [], concurrency=1)

    assert values == [{"ok": True}] and model.calls == 2
    assert logs[0]["retries"] == 1
    assert logs[0]["attempts"] == [{"error": "not ok", "raw_text": "{'ok': False}"}]
    assert metrics["judge_calls"] == 2


def test_caller_can_disable_validation_retry():
    model = FakeModel([{"ok": False}])

    values, logs, metrics = run_model_jobs(
        [job(model, 1)], [], concurrency=1, max_attempts=1
    )

    assert values == [None] and model.calls == 1
    assert logs[0]["retries"] == 0
    assert metrics["judge_calls"] == metrics["judge_invalid"] == 1


def test_batch_keeps_input_order_when_workers_finish_out_of_order():
    slow = FakeModel([{"ok": True, "value": 1}], delays=[0.02])
    fast = FakeModel([{"ok": True, "value": 2}])

    values, logs, _ = run_model_jobs(
        [job(slow, 1, stage="first"), job(fast, 2, stage="second")],
        [],
        concurrency=2,
    )

    assert [value["value"] for value in values] == [1, 2]
    assert [row["stage"] for row in logs] == ["first", "second"]


def test_completion_callback_reports_finished_rows_and_keeps_return_order():
    slow = FakeModel([{'ok': True, 'value': 1}], delays=[.04])
    fast = FakeModel([{'ok': True, 'value': 2}])
    completed = []
    values, rows, _ = run_model_jobs([job(slow, 1), job(fast, 2)], [], concurrency=2,
        on_complete=lambda row, counts: completed.append((row['input']['value'], counts['judge_calls'])))
    assert completed == [(2, 1), (1, 1)]
    assert [v['value'] for v in values] == [r['input']['value'] for r in rows] == [1, 2]


def test_completion_callback_drains_successes_even_after_a_transport_failure():
    class Broken:
        model_id = 'fixture-model'
        def start_session(self, prompt):
            return self
        def ask_json(self, *args, **kwargs):
            time.sleep(.01)
            raise ModelTransportError('offline failure')
    completed = []
    with pytest.raises(ModelTransportError, match='offline failure'):
        run_model_jobs([job(FakeModel([{'ok': True}], delays=[.03]), 1), job(Broken(), 2),
                        job(FakeModel([{'ok': True}], delays=[.06]), 3)], [], concurrency=3,
            on_complete=lambda row, counts: completed.append(row['input']['value']))
    assert completed == [1, 3]


def test_completed_terminal_failure_is_reused_without_spending_again():
    failed = FakeModel([{'ok': False}, {'ok': False}])
    _, completed, _ = run_model_jobs([job(failed, 1)], [], concurrency=1)
    model = FakeModel([])
    values, rows, metrics = run_model_jobs([job(model, 1)], [], concurrency=1, completed_log=completed)
    assert values == [None] and model.calls == 0
    assert rows[0] == dict(completed[0], reused=True)
    assert metrics['judge_reused'] == 1
