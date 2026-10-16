"""A5 descriptions and anchors share requests on the real extraction fixture."""
import copy
import json
from collections import Counter
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.prompt_library import load_prompt
from tests.unit.application.test_a4_pipeline import FakeModel, embedding, fixture_store


DOC = "baocao-canhan"
FIELDS = ("teaching_status", "anchor", "teaching_chunk_ids", "teaching_order_index", "teaching_conflict")


class IntegratedModel(FakeModel):
    def __init__(self, *, bad_anchor=None, rewrite=False, bad_description=False, prior=False):
        super().__init__(usage={"promptTokenCount": 10, "candidatesTokenCount": 2})
        self.bad_anchor, self.rewrite, self.bad_description, self.prior = bad_anchor, rewrite, bad_description, prior
        self.target, self.description_target = None, None
        self.anchor_calls, self.prior_calls, self.candidates = [], [], {}
        self.embedded, self.prompts = [], []
        self.description_attempts = Counter()
        self.usage_replies = 0

    def start_session(self, prompt):
        self.prompts.append(prompt)
        return self

    def verdict(self, data, candidates):
        selected = candidates[-1]
        value = {"node_id": data["node_id"], "status": "prior_knowledge" if self.prior else "defined_here",
                 "anchor": selected["cand_id"], "quote": selected["sentence"], "reason": "supported anchor"}
        if data["node_id"] == self.target:
            if self.bad_anchor == "candidate":
                value["anchor"] = "invented"
            elif self.bad_anchor == "quote":
                value["quote"] = "Câu trích hoàn toàn bịa đặt."
            elif self.bad_anchor == "confidence":
                value["confidence"] = 0.9
        return value

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        if "candidates" in data:
            self.anchor_calls.append(data)
            self.candidates[data["node_id"]] = data["candidates"]
            self.usage_replies += 1
            return SimpleNamespace(payload=self.verdict(data, data["candidates"]), usage=self.usage)
        if "concept" in data and "quote" in data:
            self.prior_calls.append(data)
            assert "candidates" not in data and "anchor_verdict" not in data
            self.usage_replies += 1
            return SimpleNamespace(payload={"node_id": data["node_id"], "explicit_prior": False,
                                            "reason": "not explicitly required"}, usage=self.usage)
        reply = super().ask_json(prompt, response_schema=response_schema)
        rows = data.get("nodes", [data]) if "groups" not in data and "pairs" not in data else []
        for item in rows:
            if "anchor_candidates" not in item:
                continue
            if self.target is None and "nodes" in data:
                self.target = item["node_id"]
            self.candidates[item["node_id"]] = copy.deepcopy(item["anchor_candidates"])
            verdict = self.verdict(item, item["anchor_candidates"])
            output = next(row for row in reply.payload["nodes"] if row["node_id"] == item["node_id"]) if "nodes" in data else reply.payload
            output["anchor_verdict"] = verdict
            self.embedded.append(item["node_id"])
            if self.rewrite and item["node_id"] == self.target and "nodes" in data:
                output["keep"] = False
        if self.bad_description and "chunks" in data and "anchor_candidates" in data:
            if self.description_target is None:
                self.description_target = data["node_id"]
            if data["node_id"] == self.description_target:
                self.description_attempts[data["node_id"]] += 1
                if self.description_attempts[data["node_id"]] == 1:
                    reply.payload["sentences"][0]["chunk_ids"] = ["outside-source"]
                else:
                    reply.payload.pop("anchor_verdict", None)
        self.usage_replies += 1
        return reply


def run(tmp_path, model=None, mode=None, store=None):
    store, model = store or fixture_store(tmp_path), model or IntegratedModel()
    use_case = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model),
                           upstream_chain="gop", **({"anchor_batch_mode": mode} if mode else {}))
    artifact, reused = use_case.execute(DOC)
    return store, model, use_case, artifact, reused


def test_valid_a5_anchor_parts_make_zero_separate_calls_and_cost_is_counted_once(tmp_path):
    _, model, use_case, artifact, _ = run(tmp_path)
    assert artifact.manifest["config"]["anchor_batch_mode"] == "a5"
    assert model.embedded and model.anchor_calls == []
    assert artifact.payload["stats"]["anchor_concepts_in_batch"] == len(model.candidates)
    assert artifact.payload["stats"]["anchor_concepts_fallback"] == 0
    combined = [row for row in artifact.payload["decision_log"] if row.get("origin_stage") in {"describe", "check"}]
    assert combined and all(row["stage"] == "anchor" for row in combined)
    assert any(load_prompt("a10", "anchor") in prompt for prompt in model.prompts)
    assert {row["origin_stage"] for row in combined} == {"describe", "check"}
    phases = artifact.payload["cost_summary"]["phases"]
    assert phases["anchor"]["calls"] == artifact.payload["stats"]["anchor_in_a5_calls"] == len(combined)
    assert artifact.payload["cost_summary"]["total"]["calls"] == len(model.calls)
    assert sum(phase["input_tokens"] for phase in phases.values()) == model.usage_replies * 10
    assert sum(phase["output_tokens"] for phase in phases.values()) == model.usage_replies * 2
    assert all("anchor_verdict" not in call for call in model.calls)
    before = len(model.calls)
    assert use_case.execute(DOC)[1] and len(model.calls) == before


@pytest.mark.parametrize("bad", ["candidate", "quote", "confidence"])
def test_one_invalid_anchor_is_retried_alone_and_kept_without_repeating_description(tmp_path, bad):
    _, model, _, artifact, _ = run(tmp_path, IntegratedModel(bad_anchor=bad))
    assert model.target is not None
    assert [call["node_id"] for call in model.anchor_calls] == [model.target, model.target]
    by_id = {node["node_id"]: node for node in artifact.payload["nodes"]}
    assert by_id[model.target]["learnable"] is True and by_id[model.target]["teaching_status"] == "uncertain"
    assert by_id[model.target]["description_status"] == "verified_citations"
    assert artifact.payload["stats"]["anchor_concepts_fallback"] == 1
    assert sum(item["node_id"] == model.target for call in model.calls for item in call.get("nodes", [])) == 1


def test_valid_anchor_survives_rejected_singleton_draft_and_description_retry(tmp_path):
    _, model, _, artifact, _ = run(tmp_path, IntegratedModel(rewrite=True, bad_description=True))
    target = next(node for node in artifact.payload["nodes"] if node["node_id"] == model.target)
    rewrite = [call for call in model.calls if call.get("node_id") == model.target and "chunks" in call]
    assert rewrite and all("anchor_candidates" not in call for call in rewrite)
    assert target["teaching_status"] == "taught" and target["description_status"] == "verified_citations"
    assert model.anchor_calls == [] and model.description_attempts[model.description_target] == 2
    assert any(row.get("origin_stage") == "describe" and row.get("retries") == 1
               for row in artifact.payload["decision_log"])


def test_no_candidates_carry_no_anchor_task_or_separate_call(tmp_path):
    store = fixture_store(tmp_path)
    version = store.load_latest_candidates(DOC).manifest["upstream_version"]
    base = store.load_chunks(DOC, version)
    for chunk in base.result.chunks:
        chunk.role = "mo_dau"
    store.save_chunks(DOC, base.manifest["source_hash"], "all-outside-content", {},
                      base.manifest["parse_version"], base.result,
                      manifest_fields={"semantic_roles": True, "roles_from_chunks_version": version})
    _, model, _, artifact, _ = run(tmp_path, store=store)
    assert model.anchor_calls == [] and model.embedded == [] and model.prior_calls == []
    assert "anchor_candidates" not in json.dumps(model.calls)
    assert all(node["teaching_status"] == "mentioned_only" for node in artifact.payload["nodes"]
               if node.get("learnable") and not node.get("media_id"))


def test_a5_and_single_use_identical_candidates_and_write_identical_anchor_fields(tmp_path):
    outputs, candidates, hashes = [], [], []
    store = fixture_store(tmp_path)
    for mode in ("a5", "single"):
        _, model, use_case, artifact, reused = run(tmp_path, mode=mode, store=store)
        assert not reused
        assert use_case.execute(DOC)[1]
        outputs.append({node["node_id"]: {field: node.get(field) for field in FIELDS}
                        for node in artifact.payload["nodes"]})
        candidates.append(model.candidates)
        hashes.append(artifact.manifest["config_hash"])
    assert candidates[0] == candidates[1] and outputs[0] == outputs[1]
    assert hashes[0] != hashes[1]


def test_a5_prior_knowledge_still_requires_independent_confirmation(tmp_path):
    _, model, _, artifact, _ = run(tmp_path, IntegratedModel(prior=True))
    assert model.anchor_calls == [] and len(model.prior_calls) == len(model.candidates)
    assert all(node["teaching_status"] == "uncertain" for node in artifact.payload["nodes"]
               if node["node_id"] in model.candidates)
    assert artifact.payload["cost_summary"]["total"]["calls"] == len(model.calls) + len(model.prior_calls)
