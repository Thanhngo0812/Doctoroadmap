"""Canonical gop behavior on the real baocao-canhan extraction fixture."""
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from tests.unit.application.test_a4_pipeline import FakeModel, embedding, fixture_store


DOC = "baocao-canhan"


class AnchorModel(FakeModel):
    def __init__(self, anchor_error=None):
        super().__init__(usage={"promptTokenCount": 10, "candidatesTokenCount": 2})
        self.anchor_error, self.anchor_calls, self.prior_calls = anchor_error, [], []

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        if "items" in data:
            self.calls.append(data)
            return SimpleNamespace(payload={"items": [{"item_id": item["item_id"], "partition": {
                "nodes": [{"groups": [group["group_id"]], "reason": "fixture"} for group in item["groups"]],
                "relations": [], "deferred": []}} for item in data["items"]]}, usage=self.usage)
        if "candidates" in data:
            self.anchor_calls.append(data)
            selected = data["candidates"][-1]
            value = {"node_id": data["node_id"], "status": "defined_here",
                     "anchor": selected["cand_id"], "quote": selected["sentence"], "reason": "fixture"}
            if self.anchor_error == "candidate":
                value["anchor"] = "missing-candidate"
            elif self.anchor_error == "quote":
                value["quote"] = "Câu không hề có trong tài liệu này."
            elif self.anchor_error == "prior":
                value["status"] = "prior_knowledge"
            return SimpleNamespace(payload=value, usage=self.usage)
        if "concept" in data and "quote" in data:
            self.prior_calls.append(data)
            return SimpleNamespace(payload={"node_id": data["node_id"], "explicit_prior": False,
                                            "reason": "không có điều kiện kiến thức nền"}, usage=self.usage)
        return super().ask_json(prompt, response_schema=response_schema)


def gop(tmp_path, *, model=None, store=None, **kwargs):
    store, model = store or fixture_store(tmp_path), model or AnchorModel()
    use_case = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(model, model), **kwargs)
    return store, model, use_case


def test_gop_execute_writes_c8_fields_append_only_definition_and_reuses_all(tmp_path):
    store, model, use_case = gop(tmp_path)
    artifact, reused = use_case.execute(DOC)
    assert not reused and model.anchor_calls
    assert artifact.payload["canonical_has_anchors"] is True
    assert artifact.manifest["canonical_has_anchors"] is True
    assert artifact.manifest["config"]["upstream_chain"] == "gop"
    assert artifact.payload["anchor_decision_log"] and artifact.payload["anchor_log"]
    order = {c.chunk_id: c.order_index for c in store.load_role_chunks(
        DOC, store.load_latest_candidates(DOC).manifest["upstream_version"]).result.chunks}
    by_id = {node["node_id"]: node for node in artifact.payload["nodes"]}
    for call in model.anchor_calls:
        node = by_id[call["node_id"]]
        assert node["teaching_status"] == "taught"
        assert node["teaching_chunk_ids"] == [node["anchor"]["chunk_id"]]
        assert node["teaching_order_index"] == order[node["anchor"]["chunk_id"]]
        assert node["teaching_conflict"] is False
        assert set(node["defining_chunk_ids_source"]) <= set(node["defining_chunk_ids"])
        assert node["anchor"]["chunk_id"] in node["defining_chunk_ids"]
        assert node["first_order_index"] == min(order[c] for c in node["defining_chunk_ids"])
    count = len(model.calls), len(model.anchor_calls)
    again, reused = use_case.execute(DOC)
    assert reused and again.version == artifact.version
    assert count == (len(model.calls), len(model.anchor_calls))
    phases = artifact.payload["cost_summary"]["phases"]
    assert {"merge", "repair", "describe", "check", "anchor", "anchor_prior_verify"} <= set(phases)
    assert phases["anchor"]["calls"] == len(model.anchor_calls)
    assert artifact.payload["cost_summary"]["total"]["usd"] == artifact.payload["cost_summary"]["usd"]
    assert "runtime_seconds" not in json.dumps(artifact.payload)
    assert artifact.manifest["phase_measurements"]["anchor"]["runtime_seconds"] >= 0


@pytest.mark.parametrize("error,reason", [("candidate", "anchor không phải mã"),
                                          ("quote", "quote không có")])
def test_invalid_anchor_candidate_or_quote_is_rejected_then_kept_uncertain(tmp_path, error, reason):
    _, model, use_case = gop(tmp_path, model=AnchorModel(error))
    artifact, _ = use_case.execute(DOC)
    rows = artifact.payload["anchor_decision_log"]
    assert rows and all(not row["valid"] and reason in row["error"] for row in rows)
    assert len(model.anchor_calls) == 2 * len(rows)
    judged = {row["node_id"] for row in model.anchor_calls}
    assert all(node["teaching_status"] == "uncertain" and node["anchor"] is None
               for node in artifact.payload["nodes"] if node["node_id"] in judged)


def test_unconfirmed_prior_is_lowered_to_uncertain(tmp_path):
    _, model, use_case = gop(tmp_path, model=AnchorModel("prior"))
    artifact, _ = use_case.execute(DOC)
    assert model.prior_calls and len(model.prior_calls) == len(model.anchor_calls)
    assert artifact.payload["anchor_prior_verify_decision_log"]
    judged = {row["node_id"] for row in model.prior_calls}
    assert all(node["teaching_status"] == "uncertain" for node in artifact.payload["nodes"]
               if node["node_id"] in judged)


def test_gop_requires_full_a4_and_dry_run_makes_no_paid_calls(tmp_path):
    store = fixture_store(tmp_path)
    model = AnchorModel()
    with pytest.raises(ValueError, match="embedding"):
        Canonicalize(store, reasoning=CanonicalReasoning(model, model))
    _, model, use_case = gop(tmp_path, store=store)
    use_case.embedding.embed = lambda requests: pytest.fail("dry-run called embedding")
    plan = use_case.plan(DOC)
    assert not model.calls and not model.anchor_calls and not model.prior_calls
    assert set(plan) >= {"embedding", "merge", "repair", "describe", "check", "anchor", "anchor_prior_verify"}
    assert plan["anchor"].status == "unknown" and plan["anchor"].calls_estimate is None
    assert not list((tmp_path / "canonical").glob("**/canonical.json"))


def test_gop_reads_roles_pinned_to_a3_and_no_candidates_make_no_anchor_calls(tmp_path):
    store, model, use_case = gop(tmp_path)
    version = store.load_latest_candidates(DOC).manifest["upstream_version"]
    base = store.load_chunks(DOC, version)
    for chunk in base.result.chunks:
        chunk.role = "mo_dau"
    labeled = store.save_chunks(DOC, base.manifest["source_hash"], "outside-roles", {},
                                base.manifest["parse_version"], base.result,
                                manifest_fields={"semantic_roles": True, "roles_from_chunks_version": version})
    artifact, _ = use_case.execute(DOC)
    assert not model.anchor_calls and not model.prior_calls
    eligible = [node for node in artifact.payload["nodes"] if node.get("learnable") and not node.get("media_id")]
    assert eligible and all(node["teaching_status"] == "mentioned_only" for node in eligible)
    assert all(node["mentioned_in"] == "mo_dau" for node in eligible)
    assert artifact.manifest["config"]["anchor_chunks_version"] == labeled.version

    # A later role artifact for another chunk version must not override A3's roles.
    for chunk in base.result.chunks:
        chunk.role = "noi_dung"
    store.save_chunks(DOC, base.manifest["source_hash"], "wrong-source-roles", {},
                      base.manifest["parse_version"], base.result,
                      manifest_fields={"semantic_roles": True, "roles_from_chunks_version": version - 1})
    assert use_case.execute(DOC)[1] and not model.anchor_calls
    new_roles = store.save_chunks(DOC, base.manifest["source_hash"], "inside-roles", {},
                                  base.manifest["parse_version"], base.result,
                                  manifest_fields={"semantic_roles": True, "roles_from_chunks_version": version})
    changed, reused = use_case.execute(DOC)
    assert not reused and changed.version != artifact.version and model.anchor_calls
    assert changed.manifest["config"]["anchor_chunks_version"] == new_roles.version


def test_gop_candidates_scan_exact_names_without_dense_or_provenance(tmp_path):
    store, model, use_case = gop(tmp_path)
    load_roles = store.load_role_chunks
    def role_chunks(doc, version):
        artifact = load_roles(doc, version)
        for chunk_id, text, order in (("extra-exact", "WebSocket là giao thức nối hai đầu.", -2),
                                      ("dense-only", "WebSockets hỗ trợ trao đổi đồng thời.", -1)):
            chunk = deepcopy(artifact.result.chunks[0])
            chunk.chunk_id, chunk.text, chunk.order_index = chunk_id, text, order
            chunk.section_path, chunk.role = ["Vùng bổ sung"], "noi_dung"
            artifact.result.chunks.append(chunk)
        return artifact
    store.load_role_chunks = role_chunks
    # A graph can contain these dense/provenance proposals; canonical must not read it.
    store.load_latest_graph = lambda *a, **k: pytest.fail("canonical consulted dense/provenance graph")
    store.load_graph = lambda *a, **k: pytest.fail("canonical consulted dense/provenance graph")
    use_case.execute(DOC)
    websocket = next(call for call in model.anchor_calls if call["concept"]["name"] == "WebSocket")
    candidates = {candidate["chunk_id"] for candidate in websocket["candidates"]}
    assert "extra-exact" in candidates
    assert "dense-only" not in candidates
