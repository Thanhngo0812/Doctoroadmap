from types import SimpleNamespace

import pytest
from importlib import import_module

from doc2roadmap.application.use_cases.build_learning_graph import BuildLearningGraph


def test_plan_lists_all_stages_and_marks_unknown_downstream_without_executing_anything():
    from doc2roadmap.application.planning import StagePlan

    visited = []

    class Stage:
        def __init__(self, name, missing=False):
            self.name, self.missing = name, missing

        def execute(self, *args, **kwargs):
            pytest.fail("dry-run executed a stage")

        def plan(self, doc_id, *, upstream=None):
            if visited:
                assert upstream.payload["stage"] == visited[-1]
            visited.append(self.name)
            if self.missing:
                return StagePlan("run", remaining_items=7, calls_estimate=14, usd_estimate=0.03)
            return StagePlan("reused", artifact=SimpleNamespace(payload={"stage": self.name}, version=1))

    names = ["clusters", "mentions", "provenance", "main_edges", "secondary_edges", "validated", "teaching", "identity", "stages"]
    pipeline = BuildLearningGraph(*(Stage(n, n == "secondary_edges") for n in names))
    report = pipeline.plan("doc")
    assert [row["stage"] for row in report["stages"]] == names
    assert [row["status"] for row in report["stages"]] == ["reused"] * 4 + ["run"] + ["unknown"] * 4
    assert report["stages"][4]["remaining_items"] == 7
    assert report["known_usd_estimate"] == 0.03 and not report["estimate_complete"]
    assert visited == names[:5]


def test_secondary_plan_resumes_exact_checkpoint_and_never_calls_or_writes():
    from tests.unit.application.test_build_secondary_edges import Store

    from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges
    from doc2roadmap.domain.canonical import digest

    class NoCalls:
        model_id = "gemini-3.1-flash-lite"

        def start_session(self, *args):
            pytest.fail("dry-run called the model")

    store = Store()
    uc = BuildSecondaryEdges(store, NoCalls())
    first = uc.plan("doc", upstream=store.main)
    assert first.status == "run" and first.remaining_items == 1 and first.calls_estimate == 2
    assert first.usd_estimate > 0 and store.saved_versions == 0 and not store.checkpoints
    store.checkpoints[first.checkpoint_id] = {
        "source_hash": digest(store.main.payload), "completed_secondary_pairs": ["ab"]}
    resumed = uc.plan("doc", upstream=store.main)
    assert resumed.remaining_items == 0 and resumed.calls_estimate == 0 and resumed.usd_estimate == 0
    store.checkpoints[first.checkpoint_id]["source_hash"] = "stale-source"
    assert uc.plan("doc", upstream=store.main).remaining_items == 1
    assert store.saved_versions == 0


def test_dry_run_cli_uses_plan_even_with_allow_spend(monkeypatch, capsys):
    from doc2roadmap.presentation.cli import main as cli

    class Pipeline:
        def plan(self, doc_id, *, stop_after):
            return {"dry_run": True, "doc_id": doc_id, "stages": []}

        def execute(self, *args, **kwargs):
            pytest.fail("CLI executed instead of planning")

    def build(**kwargs):
        assert kwargs["allow_spend"] is False
        return Pipeline(), None

    monkeypatch.setattr(cli, "build_learning_graph", build)
    assert cli.main(["roadmap", "--doc-id", "doc", "--dry-run", "--allow-spend"]) == 0
    assert '"dry_run": true' in capsys.readouterr().out


@pytest.mark.parametrize("module,klass,upstream,expected", [
    ("build_clusters", "BuildClusters", None, 3),
    ("build_mentions", "BuildMentions", "graph", 2),
    ("build_provenance", "BuildProvenance", "mentions", 1),
    ("build_main_edges", "BuildMainEdges", "mentions", 1),
    ("anchor_concepts", "AnchorConcepts", "validated", 2),
    ("judge_identity", "JudgeIdentity", "teaching", 4),
])
def test_each_paid_stage_plan_never_calls_model_or_writes(module, klass, upstream, expected):
    fixture = import_module("tests.unit.application.test_" + module)
    store = fixture.Store()

    class NoCalls:
        model_id = "gemini-3.1-flash-lite"
        identifier = "fake-v1"
        embedding_model_id = "same-model"

        def start_session(self, *args):
            pytest.fail("plan called the model")

        def embed(self, *args):
            pytest.fail("plan called embedding")

    def no_write(*args, **kwargs):
        pytest.fail("plan mutated artifacts or checkpoints")

    store.save_graph = store.save_checkpoint = store.clear_checkpoint = no_write
    uc = getattr(import_module("doc2roadmap.application.use_cases." + module), klass)(store, NoCalls())
    kwargs = {"upstream": getattr(store, upstream)} if upstream else {}
    result = uc.plan("doc", **kwargs)
    assert result.status == "run" and result.calls_estimate == expected
    if module in ("build_clusters", "build_mentions"):
        assert result.usd_estimate is None  # giá embedding chưa khai, không báo giả 0 USD
    else:
        assert result.usd_estimate > 0


def test_anchor_plan_uses_answers_from_only_the_matching_checkpoint():
    from tests.unit.application.test_anchor_concepts import Store
    from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts
    from doc2roadmap.domain.canonical import digest

    store = Store()
    uc = AnchorConcepts(store, SimpleNamespace(model_id="gemini-3.1-flash-lite"))
    plan = uc.plan("doc", upstream=store.validated)
    store.checkpoints[plan.checkpoint_id] = {"source_hash": digest(store.validated.payload),
        "answers": {"cs": {}}, "decision_log": [], "metrics": {}}
    assert uc.plan("doc", upstream=store.validated).calls_estimate == 1
    store.checkpoints[plan.checkpoint_id]["source_hash"] = "wrong-source"
    assert uc.plan("doc", upstream=store.validated).calls_estimate == 2
