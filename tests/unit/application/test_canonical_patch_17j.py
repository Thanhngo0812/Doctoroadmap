import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from tests.unit.application.test_a4_pipeline import embedding, fixture_store, graph_with
from tests.unit.application.test_canonical_gop import DOC
CUTS = [("WebSocket", "WebSockets"), ("Mutex", "Race Condition"), ("Golang", "Giao thức WebSockets")]


@pytest.mark.parametrize("route", ["merge", "repair"])
@pytest.mark.parametrize("label,retries", [("synonym", 1), ("same_category", 0),
                                           ("coextensive_with", 1), ("coextensive_with_candidate", 0)])
def test_gop_identity_relation_retries_only_exact_identity_labels(tmp_path, monkeypatch, route, label, retries):
    from tests.unit.application.test_canonical_gop import AnchorModel

    class RelationModel(AnchorModel):
        def __init__(self):
            super().__init__()
            self.judgments = []

        def partition(self, groups):
            value = {"nodes": [{"groups": [group["group_id"]], "reason": "different"} for group in groups],
                     "deferred": [], "relations": []}
            if not self.judgments:
                value["relations"] = [{"source": groups[0]["group_id"], "target": groups[1]["group_id"],
                    "edge_type": label, "chunk_ids": [groups[0]["evidence"][0]["chunk_id"]], "reason": "fixture"}]
            return value

        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if "items" in data:
                value = {"items": [{"item_id": item["item_id"], "partition": self.partition(item["groups"])}
                                    for item in data["items"]]}
            elif "groups" in data:
                value = self.partition(data["groups"])
            else:
                return super().ask_json(prompt, response_schema=response_schema)
            self.judgments.append(data)
            return SimpleNamespace(payload=value, usage=self.usage)

    def graph(*args, **kwargs):
        pair = [CUTS[0]]
        value = graph_with(pair if route == "merge" else [], [] if route == "merge" else pair)(*args, **kwargs)
        value["metrics"]["nomination_channels"] = {}
        return value
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    model = RelationModel()
    artifact, _ = Canonicalize(fixture_store(tmp_path), embedding(), reasoning=CanonicalReasoning(model, model)).execute(DOC)
    assert len(model.judgments) == 1 + retries
    assert artifact.payload["stats"]["partition_contradictions"] == retries
    proposed = [edge for edge in artifact.payload["edges"] if "2a" in edge["origins"]]
    assert any(edge["edge_type"] == label for edge in proposed) == (not retries)
    assert artifact.manifest["config"]["reasoning"]["partition_validation"] == "consistency-gop-identity-labels-v3"
