from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_learning_graph import BuildLearningGraph
from doc2roadmap.application.planning import StagePlan


class Stage:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def execute(self, doc_id, *, upstream=None):
        if self.name != "clusters":
            assert upstream is not None
        self.calls.append(self.name)
        stage = "edges" if self.name in {"main", "secondary"} else self.name
        return SimpleNamespace(payload={"stage": stage}), True


def test_one_use_case_stops_at_each_public_stage_without_touching_later_stages():
    expected = {
        "clusters": ["clusters"],
        "mentions": ["clusters", "mentions"],
        "provenance": ["clusters", "mentions", "provenance"],
        "teaching": ["clusters", "mentions", "provenance", "teaching"],
        "identity": ["clusters", "mentions", "provenance", "teaching", "identity"],
        "edges": ["clusters", "mentions", "provenance", "teaching", "identity", "main", "secondary"],
        "stages": ["clusters", "mentions", "provenance", "teaching", "identity", "main", "secondary", "validated",
                   "stages"],
    }
    for stop_after, wanted in expected.items():
        calls = []
        use_case = BuildLearningGraph(
            Stage("clusters", calls),
            Stage("mentions", calls),
            Stage("provenance", calls),
            Stage("main", calls),
            Stage("secondary", calls),
            Stage("validated", calls),
            Stage("teaching", calls),
            Stage("identity", calls),
            Stage("stages", calls),
        )
        artifact, reused = use_case.execute("doc", stop_after=stop_after)
        assert calls == wanted
        assert reused
        assert artifact.payload["stage"] == stop_after


def test_identity_plan_never_touches_a8():
    calls = []

    class Planned(Stage):
        def plan(self, doc_id, *, upstream=None):
            self.calls.append(self.name)
            return StagePlan("reused", artifact=SimpleNamespace(version=1, payload={"stage": self.name}))

    class Forbidden(Stage):
        def plan(self, *args, **kwargs):
            raise AssertionError("A8 was planned before identity review")

    stages = [Planned(name, calls) for name in
              ("clusters", "mentions", "provenance", "main", "secondary", "validated", "teaching", "identity", "stages")]
    stages[3] = Forbidden("main", calls)
    pipeline = BuildLearningGraph(*stages)
    result = pipeline.plan("doc", stop_after="identity")
    assert [row["stage"] for row in result["stages"]] == [
        "clusters", "mentions", "provenance", "teaching", "identity"]
    assert calls == ["clusters", "mentions", "provenance", "teaching", "identity"]


def test_orchestrator_passes_the_exact_returned_artifact_to_the_next_stage():
    artifacts = []

    class TrackingStage(Stage):
        def execute(self, doc_id, *, upstream=None):
            if artifacts:
                assert upstream is artifacts[-1]
            artifact, reused = super().execute(doc_id, upstream=upstream)
            artifacts.append(artifact)
            return artifact, reused

    calls = []
    names = ("clusters", "mentions", "provenance", "teaching", "identity", "main", "secondary", "validated", "stages")
    stages = [TrackingStage(name, calls) for name in
              ("clusters", "mentions", "provenance", "main", "secondary", "validated", "teaching", "identity", "stages")]
    BuildLearningGraph(*stages).execute("doc")
    assert calls == list(names)


def test_module_titles_run_after_roadmap_and_are_part_of_final_stages():
    calls = []
    stages = [Stage(name, calls) for name in
              ("clusters", "mentions", "provenance", "main", "secondary", "validated", "teaching", "identity", "stages")]
    stage = BuildLearningGraph(*stages, module_titles=Stage("module_titles", calls))
    artifact, reused = stage.execute("doc")
    assert reused and artifact.payload["stage"] == "module_titles"
    assert calls[-2:] == ["stages", "module_titles"]


def test_concept_labels_run_after_identity_without_reexecuting_teaching():
    calls = []
    stages = [Stage(name, calls) for name in
              ("clusters", "mentions", "provenance", "main", "secondary", "validated", "teaching", "identity", "stages")]
    BuildLearningGraph(*stages, concept_labels=Stage("concept_labels", calls)).execute("doc")
    assert calls[-4:] == ["secondary", "validated", "concept_labels", "stages"]


def test_switching_configuration_a_b_a_reuses_the_original_a_chain():
    current = {"value": "A"}

    class Clusters:
        def __init__(self):
            self.cache = {}

        def execute(self, doc_id):
            value = current["value"]
            reused = value in self.cache
            self.cache.setdefault(value, SimpleNamespace(payload={"stage": "clusters", "config": value}))
            return self.cache[value], reused

    class Mentions:
        def __init__(self):
            self.cache = {}
            self.calls = 0

        def execute(self, doc_id, *, upstream):
            value = upstream.payload["config"]
            if value in self.cache:
                return self.cache[value], True
            self.calls += 1
            artifact = SimpleNamespace(payload={"stage": "mentions", "config": value})
            self.cache[value] = artifact
            return artifact, False

    clusters, mentions = Clusters(), Mentions()
    unused = Stage("unused", [])
    use_case = BuildLearningGraph(clusters, mentions, unused, unused, unused, unused, unused, unused, unused)
    first_a, _ = use_case.execute("doc", stop_after="mentions")
    current["value"] = "B"
    use_case.execute("doc", stop_after="mentions")
    current["value"] = "A"
    second_a, reused = use_case.execute("doc", stop_after="mentions")
    assert reused and second_a is first_a and mentions.calls == 2


def test_a_blocked_paid_call_is_reported_with_the_stage_that_made_it():
    import pytest

    from doc2roadmap.application.spend_guard import SpendNotAllowed

    calls = []

    class Paid(Stage):
        def execute(self, doc_id, *, upstream=None):
            calls.append(self.name)
            raise SpendNotAllowed()

    use_case = BuildLearningGraph(
        Stage("clusters", calls), Stage("mentions", calls), Stage("provenance", calls), Stage("main", calls),
        Paid("secondary", calls), Stage("validated", calls), Stage("teaching", calls), Stage("identity", calls),
        Stage("stages", calls),
    )
    with pytest.raises(SpendNotAllowed) as error:
        use_case.execute("doc")
    assert error.value.stage == "secondary_edges" and "secondary_edges" in str(error.value)
    assert calls[-1] == "secondary"  # dừng ngay, không chạy stage nào sau đó
