from pathlib import Path

import pytest

from doc2roadmap.application.ports.build import BUILD_STEPS, BuildRejected
from doc2roadmap.application.use_cases.build_document import BuildDocument


class FakePipeline:
    def __init__(self, pages=None):
        self.pages = pages or ["Tiếng Việt có đầy đủ nội dung học tập. " * 12]
        self.calls = []
        self.cache = set()
        self.totals = {"spent_usd": 1.25, "model_calls": 8, "input_tokens": 90, "output_tokens": 40}
        self.fail_roadmap = False

    def _step(self, name, value=None):
        self.calls.append(name)
        if name not in self.cache:
            if name == "roadmap" and self.fail_roadmap:
                self.fail_roadmap = False
                raise RuntimeError("graph unavailable")
            self.cache.add(name)
            self.totals["model_calls"] += 1
        return value or {"stage": name, "revision": 3}

    def read(self, path, doc_id):
        self.calls.append("read")
        return {"page_texts": self.pages, "chunks_version": 2, "parse_version": "p2"}

    def label_roles(self, doc_id): return self._step("label_roles")
    def a3(self, doc_id): return self._step("a3")
    def canonical(self, doc_id, language): return self._step("canonical")
    def roadmap(self, doc_id): return self._step("roadmap", {"graph_version": 7, "stage": "roadmap"})
    def learning_prep(self, path, doc_id, graph_version): return self._step("learning_prep")
    def inspect(self, doc_id): return {"dependencies": {"cached": True}}
    def usage(self): return dict(self.totals)


def test_runs_steps_in_order_preserves_metadata_and_records_usage_delta():
    pipeline = FakePipeline()
    recorded = []
    runner = BuildDocument(pipeline, "w13", recorder=recorded.append)

    result = runner.execute(Path("in.pdf"), "doc-1")

    assert pipeline.calls == ["read", "label_roles", "a3", "canonical", "roadmap", "learning_prep"]
    assert result.completed_steps == list(BUILD_STEPS)
    assert result.step_details["doc_reading"]["chunks_version"] == 2
    assert "page_texts" not in result.step_details["doc_reading"]
    assert result.step_details["concepts"]["canonical"]["revision"] == 3
    assert result.graph_version == 7
    assert (result.spent_usd, result.model_calls, result.input_tokens, result.output_tokens) == (0, 5, 0, 0)
    assert recorded == [result]


@pytest.mark.parametrize("pages,language,code", [
    (["x" * 30], "vi", "ban_quet"),
    (["Tiếng Việt đủ chữ. " * 20, ""], "vi", "ban_quet"),
    (["English text with enough letters. " * 20], "vi", "ngon_ngu_khong_ho_tro"),
])
def test_input_gates_reject_before_pipeline_steps(pages, language, code):
    pipeline = FakePipeline(pages)
    runner = BuildDocument(pipeline, "w13")

    result = runner.execute(Path("in.pdf"), "doc-1", language=language)

    assert result.status == "rejected"
    assert result.error["code"] == code
    assert pipeline.calls == ["read"]


@pytest.mark.parametrize("pages,language,status,code", [
    (["á" * 3000, "", ""], "vi", "rejected", "ban_quet"),
    (["á" * 600, ""], "vi", "succeeded", None),
    (["á" * 200], "vi", "succeeded", None),
    (["á" * 199], "vi", "rejected", "ban_quet"),
    (["á" * 300], "en", "rejected", "ngon_ngu_khong_ho_tro"),
])
def test_page_gate_boundaries_and_unsupported_languages(pages, language, status, code):
    pipeline = FakePipeline(pages)
    result = BuildDocument(pipeline, "w13", scan_min_chars_per_page=200).execute(
        Path("x"), "d", language=language)
    assert result.status == status
    if status == "rejected":
        assert result.error["code"] == code
        assert pipeline.calls == ["read"]


def test_calibrated_default_threshold_accepts_150_letters():
    result = BuildDocument(FakePipeline(["á" * 150]), "w13").execute(Path("x"), "d")
    assert result.status == "succeeded"


@pytest.mark.parametrize("page,status", [("á" * 2 + "a" * 198, "succeeded"), ("á" + "a" * 299, "rejected")])
def test_vietnamese_diacritic_ratio_boundary(page, status):
    result = BuildDocument(FakePipeline([page]), "w13").execute(Path("x"), "d")
    assert result.status == status
    if status == "rejected":
        assert result.error["code"] == "ngon_ngu_khong_ho_tro"


def test_invalid_doc_id_is_rejected_before_pipeline_calls():
    pipeline = FakePipeline()
    result = BuildDocument(pipeline, "w13").execute(Path("x"), "../bad")
    assert result.status == "failed"
    assert pipeline.calls == []


def test_pipeline_text_quality_rejection_and_recorder_on_rejection():
    class BadText(FakePipeline):
        def read(self, path, doc_id):
            self.calls.append("read")
            raise BuildRejected("chu_loi", "bad OCR")

    pipeline = BadText()
    recorded = []
    result = BuildDocument(pipeline, "w13", recorder=recorded.append).execute(Path("x"), "d")
    assert result.status == "rejected" and result.error["code"] == "chu_loi"
    assert pipeline.calls == ["read"]
    assert recorded == [result]


def test_paid_step_denial_keeps_stage_message_and_marks_failure():
    class Denied(FakePipeline):
        def label_roles(self, doc_id):
            from doc2roadmap.application.spend_guard import SpendNotAllowed
            raise SpendNotAllowed("roles")

    result = BuildDocument(Denied(), "w13").execute(Path("x"), "d")
    assert result.status == "failed"
    assert result.error["stage"] == "concepts"
    assert "roles" in result.error["message"]
    assert result.error["retryable"] is False


@pytest.mark.parametrize("error,retryable,code", [
    (TimeoutError("timed out"), True, "loi_mang"),
    (RuntimeError("broken"), False, "loi_noi_bo"),
])
def test_errors_use_stable_codes_and_retryability(error, retryable, code):
    class Broken(FakePipeline):
        def label_roles(self, doc_id): raise error

    result = BuildDocument(Broken(), "w13").execute(Path("x"), "d")
    assert result.error["code"] == code
    assert result.error["error_type"] == type(error).__name__
    assert result.error["retryable"] is retryable


def test_cancel_after_concepts_prevents_graph_and_retry_reuses_completed_work():
    pipeline = FakePipeline()
    runner = BuildDocument(pipeline, "w13")
    cancel = lambda: "canonical" in pipeline.calls

    first = runner.execute(Path("x"), "d", cancelled=cancel)
    assert first.status == "cancelled"
    assert "roadmap" not in pipeline.calls

    pipeline.calls.clear()
    pipeline.fail_roadmap = True
    failed = runner.execute(Path("x"), "d")
    assert failed.status == "failed"
    counts = {name: pipeline.calls.count(name) for name in ("label_roles", "a3", "canonical")}
    pipeline.calls.clear()
    completed = runner.execute(Path("x"), "d")
    assert completed.status == "succeeded"
    assert {name: pipeline.calls.count(name) for name in counts} == {name: 1 for name in counts}
    assert completed.model_calls == 2  # graph retry plus the first learning-prep call


def test_dry_run_reads_and_inspects_without_executing_pipeline_steps():
    pipeline = FakePipeline()
    progress = []
    result = BuildDocument(pipeline, "w13").execute(Path("x"), "d", dry_run=True,
                                                     progress=lambda *event: progress.append(event))
    assert result.status == "dry_run"
    assert pipeline.calls == ["read"]
    assert result.completed_steps == ["doc_reading"]
    assert [event for event in progress if event[1]["status"] == "completed"]
    assert [event[0] for event in progress if event[1]["status"] == "planned"] == list(BUILD_STEPS[1:])


def test_progress_started_is_emitted_before_pipeline_work():
    events = []
    class Observed(FakePipeline):
        def read(self, path, doc_id):
            events.append("read")
            return super().read(path, doc_id)

    def progress(step, details):
        events.append((step, details["status"]))

    BuildDocument(Observed(), "w13").execute(Path("x"), "d", dry_run=True, progress=progress)
    assert events[:2] == [("doc_reading", "started"), "read"]


def test_provider_marked_incomplete_usage_stays_incomplete():
    class Incomplete(FakePipeline):
        def usage(self):
            usage = dict(self.totals)
            usage["usage_complete"] = False
            return usage

    result = BuildDocument(Incomplete(), "w13").execute(Path("x"), "d")
    assert result.usage_complete is False


def test_historical_missing_usage_does_not_poison_a_cached_attempt():
    class PreviouslyIncomplete(FakePipeline):
        def usage(self):
            return {**self.totals, "usage_complete": False, "missing_usage_calls": 2}

    pipeline = PreviouslyIncomplete()
    pipeline.cache.update(("label_roles", "a3", "canonical", "roadmap", "learning_prep"))
    result = BuildDocument(pipeline, "w13").execute(Path("x"), "d")
    assert result.model_calls == result.spent_usd == 0
    assert result.usage_complete is True


def test_embedding_network_failure_cause_is_retryable():
    from urllib.error import URLError

    class Broken(FakePipeline):
        def a3(self, doc_id):
            try:
                raise URLError("connection lost")
            except URLError as cause:
                raise RuntimeError("embedding request failed") from cause

    result = BuildDocument(Broken(), "w13").execute(Path("x"), "d")
    assert result.error["code"] == "loi_mang"
    assert result.error["retryable"] is True


def test_nonfinite_provider_usage_stays_incomplete():
    class InvalidUsage(FakePipeline):
        def usage(self):
            usage = dict(self.totals)
            usage["spent_usd"] = float("nan")
            return usage

    result = BuildDocument(InvalidUsage(), "w13").execute(Path("x"), "d")
    assert result.usage_complete is False


def test_usage_is_per_run_and_recorder_exception_propagates():
    pipeline = FakePipeline()
    pipeline.totals.update(spent_usd=.75, model_calls=3, input_tokens=12, output_tokens=6)
    runner = BuildDocument(pipeline, "w13")
    first = runner.execute(Path("x"), "d")
    second = runner.execute(Path("x"), "d")
    assert first.spent_usd == second.spent_usd == 0
    assert first.model_calls == 5 and second.model_calls == 0

    with pytest.raises(LookupError, match="recorder"):
        BuildDocument(FakePipeline(), "w13", recorder=lambda result: (_ for _ in ()).throw(LookupError("recorder"))).execute(
            Path("x"), "other")
