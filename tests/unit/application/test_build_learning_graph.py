from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_learning_graph import BuildLearningGraph


class Stage:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def execute(self, doc_id):
        self.calls.append(self.name)
        stage = "edges" if self.name in {"main", "secondary"} else self.name
        return SimpleNamespace(payload={"stage": stage}), True


def test_one_use_case_stops_at_each_public_stage_without_touching_later_stages():
    expected = {
        "clusters": ["clusters"],
        "mentions": ["clusters", "mentions"],
        "edges": ["clusters", "mentions", "main", "secondary"],
        "stages": ["clusters", "mentions", "main", "secondary", "validated", "stages"],
    }
    for stop_after, wanted in expected.items():
        calls = []
        use_case = BuildLearningGraph(
            Stage("clusters", calls),
            Stage("mentions", calls),
            Stage("main", calls),
            Stage("secondary", calls),
            Stage("validated", calls),
            Stage("stages", calls),
        )
        artifact, reused = use_case.execute("doc", stop_after=stop_after)
        assert calls == wanted
        assert reused
        assert artifact.payload["stage"] == stop_after
