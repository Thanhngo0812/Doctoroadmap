from types import SimpleNamespace

import pytest

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.spend_guard import SpendGuard, SpendNotAllowed


class Model:
    model_id = "fixture-model"

    def __init__(self):
        self.sessions = 0

    def start_session(self, system_prompt):
        self.sessions += 1
        return self

    def ask_json(self, prompt, *, response_schema):
        return SimpleNamespace(payload={"ok": True}, usage=None)


def job(model):
    return ModelJob("secondary", model, "system", "hash", {"x": 1}, {"type": "object"}, lambda value: None)


def test_a_blocked_model_refuses_the_first_paid_call_and_the_executor_does_not_swallow_it():
    # run_model_jobs coi RuntimeError là phản hồi hỏng rồi thử lại. Nếu lỗi chặn chi lọt vào nhánh đó, pipeline chạy tiếp
    # và sinh artifact toàn "không hợp lệ" mà không báo gì — tệ hơn cả việc tiêu tiền.
    inner = Model()
    with pytest.raises(SpendNotAllowed):
        run_model_jobs([job(SpendGuard(inner, allowed=False))], [], concurrency=1)
    assert inner.sessions == 0


def test_an_allowed_model_calls_through_and_keeps_its_identity():
    inner = Model()
    guarded = SpendGuard(inner, allowed=True)
    values, _, _ = run_model_jobs([job(guarded)], [], concurrency=1)
    assert values == [{"ok": True}] and inner.sessions == 1
    assert guarded.model_id == "fixture-model"  # prompt_hash và khoá cache đều dùng model_id


def test_a_cached_answer_needs_no_permission():
    inner = Model()
    _, rows, _ = run_model_jobs([job(SpendGuard(inner, allowed=True))], [], concurrency=1)
    values, _, _ = run_model_jobs([job(SpendGuard(inner, allowed=False))], rows, concurrency=1)
    assert values == [{"ok": True}] and inner.sessions == 1
