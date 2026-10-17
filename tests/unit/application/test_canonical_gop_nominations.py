from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from tests.unit.application.test_a4_pipeline import fixture_store, embedding
from tests.unit.application.test_canonical_gop import AnchorModel, DOC


class CountEmbedding:
    def __init__(self):
        self.delegate, self.requests = embedding(), []
        self.embedding_model_id = self.delegate.embedding_model_id

    def embed(self, requests):
        self.requests.extend(requests)
        return self.delegate.embed(requests)


def test_special_case_stays_separate_and_has_open_proposed_relation(tmp_path):
    class SubtypeModel(AnchorModel):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            value = reply.payload
            if "relations" in value and len(value["nodes"]) >= 2:
                import json
                data = json.loads(prompt.split("\nCorrect this validation error:")[0])
                left, right = data["groups"][:2]
                value["relations"] = [{"source": left["group_id"], "target": right["group_id"],
                    "edge_type": "subtype_of", "chunk_ids": [left["evidence"][0]["chunk_id"]],
                    "reason": "trường hợp riêng"}]
            return reply

    store, model = fixture_store(tmp_path), SubtypeModel()
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model)).execute(DOC)
    edges = [edge for edge in result.payload["edges"] if "2a" in edge["origins"]]
    assert edges and all(edge["source"] != edge["target"] and edge["proposal"] for edge in edges)
    assert any(edge["edge_type"] == "subtype_of" for edge in edges)
