import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.a4_gold import gold_items, write_gold_sheet, load_gold, evaluate_canonical
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.embedding.replay import ReplayEmbedding
from doc2roadmap.domain.canonical import digest


def fixture_store(tmp_path):
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    store = JsonArtifactStore(tmp_path)
    doc = "baocao-canhan"
    base = tmp_path / "candidates" / doc / f"v{source['candidate_version']}"
    store._write(base / "candidates.json", source["candidate_payload"])
    store._write(base / "manifest.json", source["candidate_manifest"])
    base = tmp_path / "chunks" / doc / f"v{source['chunk_version']}"
    store._write(base / "manifest.json", source["chunk_manifest"])
    store._write(base / "sections.json", source["chunks"]["sections"])
    store._write(base / "chunks.json", source["chunks"]["chunks"])
    store._write(base / "document.json", {"normalized_full_text": source["chunks"]["normalized_full_text"]})
    return store


def embedding():
    return ReplayEmbedding(Path("tests/fixtures/a4/baocao-canhan/name-vectors.json"), expected_model_id="gemini-embedding-001:768")


class FakeModel:
    model_id = "fixture-model"
    def __init__(self, invalid=0, description_invalid=False, merge_all=False):
        self.calls, self.invalid, self.description_invalid, self.merge_all = [], invalid, description_invalid, merge_all
    def start_session(self, prompt):
        return self
    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        self.calls.append(data)
        if self.invalid:
            self.invalid -= 1
            return SimpleNamespace(payload={})
        if "groups" in data:
            assert "description_draft" not in json.dumps(data) and '"draft"' not in json.dumps(data)
            ids = [g["group_id"] for g in data["groups"]]
            groups = [ids] if self.merge_all else [[id] for id in ids]
            value = {"nodes": [{"groups": g, "reason": "fixture"} for g in groups], "deferred": [], "relations": []}
        elif "pairs" in data:
            value = {"pairs": [{"pair_id": p["pair_id"], "label": "different", "child": "", "chunk_ids": [], "reason": "fixture"} for p in data["pairs"]]}
        elif "nodes" in data:
            value = {"nodes": [{"node_id": n["node_id"], "keep": True, "reason": "fixture supported"} for n in data["nodes"]]}
        else:
            chunk = "outside" if self.description_invalid else data["chunks"][-1]["chunk_id"]
            value = {"sentences": [{"text": "Tài liệu trình bày khái niệm này.", "chunk_ids": [chunk]}],
                     "defining_chunk_ids": [chunk], "nghi_gop_nham": False, "reason": "fixture"}
        return SimpleNamespace(payload=value)


def test_canonical_concurrency_bound_order_retry_and_cache(tmp_path):
    class Probe:
        model_id = "fixture-model"
        def __init__(self, limit):
            self.limit, self.lock = limit, threading.Lock()
            self.active = self.peak = 0
            self.stages, self.attempts, self.calls = {}, {}, 0
            self.barriers = {s: threading.Barrier(limit, timeout=2) for s in ["merge", "repair", "describe", "check"]}
        def start_session(self, prompt):
            probe = self
            class Session(FakeModel):
                def ask_json(self, prompt, *, response_schema):
                    data = json.loads(prompt.split("\nCorrect this validation error:")[0])
                    stage = "repair" if data.get("repair_of_cut_edge") else "merge" if "groups" in data else "check" if "nodes" in data else "describe"
                    key = json.dumps(data, sort_keys=True)
                    with probe.lock:
                        probe.active += 1
                        probe.peak = max(probe.peak, probe.active)
                        probe.calls += 1
                        count = probe.stages.get(stage, 0)
                        probe.stages[stage] = count + 1
                        attempt = probe.attempts.get(key, 0)
                        probe.attempts[key] = attempt + 1
                    try:
                        if count < probe.limit:
                            probe.barriers[stage].wait()
                        time.sleep(.002)
                        if not attempt:
                            return SimpleNamespace(payload={})
                        return super().ask_json(prompt, response_schema=response_schema)
                    finally:
                        with probe.lock:
                            probe.active -= 1
            return Session()
    outputs = []
    for limit in [1, 4]:
        store, model = fixture_store(tmp_path / str(limit)), Probe(limit)
        reasoning = CanonicalReasoning(model, model, concurrency=limit, batch_size=1)
        use_case = Canonicalize(store, embedding(), reasoning=reasoning)
        result, _ = use_case.execute("baocao-canhan")
        assert model.peak == limit
        assert set(model.stages) == {"merge", "repair", "describe", "check"}
        assert all(r["retries"] == 1 for r in result.payload["decision_log"] if "retries" in r)
        assert not any(r.get("valid") is False for r in result.payload["decision_log"])
        calls, config = model.calls, reasoning.config()
        reasoning.concurrency = 2
        assert reasoning.config() == config
        assert use_case.execute("baocao-canhan")[1]
        assert model.calls == calls
        outputs.append(result.payload)
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_canonical_concurrency_rejects_invalid(value):
    with pytest.raises(ValueError):
        CanonicalReasoning(FakeModel(), FakeModel(), concurrency=value)


def test_canonical_concurrency_setting(monkeypatch):
    from doc2roadmap.config import Settings
    from pydantic import ValidationError
    monkeypatch.setenv("DOC2ROADMAP_CANONICAL_CONCURRENCY", "7")
    assert Settings(_env_file=None).canonical_concurrency == 7
    monkeypatch.setenv("DOC2ROADMAP_CANONICAL_CONCURRENCY", "0")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_writer_wrong_language_retries_then_falls_back(tmp_path):
    class EnglishWriter(FakeModel):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            if "sentences" in reply.payload:
                reply.payload["sentences"][0]["text"] = "This is an English description."
            return reply
    store, writer = fixture_store(tmp_path), EnglishWriter()
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(FakeModel(), writer)).execute("baocao-canhan")
    multi = [n for n in result.payload["nodes"] if not n["media_id"] and len(n["members"]) > 1]
    assert multi
    for node in multi:
        assert node["description_status"] == "draft_fallback_invalid"
        assert sum(c.get("node_id") == node["node_id"] for c in writer.calls) == 2


def test_a5_defining_chunk_moves_order_and_preserves_conflict(tmp_path):
    class ConflictWriter(FakeModel):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            if "sentences" in reply.payload:
                reply.payload.update(nghi_gop_nham=True, reason="Sources disagree; no reconciliation")
            return reply
    store = fixture_store(tmp_path)
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(FakeModel(), ConflictWriter())).execute("baocao-canhan")
    source = store.load_latest_candidates("baocao-canhan")
    order = {c.chunk_id: c.order_index for c in store.load_chunks("baocao-canhan", source.manifest["upstream_version"]).result.chunks}
    moved = []
    for node in result.payload["nodes"]:
        if node["media_id"] or len(node["members"]) < 2:
            continue
        expected = max(order[c] for c in node["source_chunk_ids"])
        assert node["first_order_index"] == expected
        assert node["nghi_gop_nham"] is True
        assert node["description_reason"] == "Sources disagree; no reconciliation"
        assert node["description"].startswith("Tài liệu trình bày khái niệm này.")
        moved.append(expected > node["first_mention_index"])
    assert any(moved)


def test_real_fixture_names_nominations_and_no_network(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: pytest.fail("network forbidden"))
    store = fixture_store(tmp_path)
    artifact, reused = Canonicalize(store, embedding()).execute("baocao-canhan")
    assert not reused
    assert artifact.payload["stats"]["text_node_count"] == 46
    assert all(len(c) <= 9 for c in artifact.payload["nominations"]["clusters"])
    names = {n["node_id"]: n["name"] for n in artifact.payload["nodes"]}
    pairs = {frozenset((names[e["source"]], names[e["target"]])) for e in artifact.payload["nominations"]["edges"]}
    for a, b in [("WebSocket", "WebSockets"), ("Tranh chấp dữ liệu", "Race Condition"), ("Kiến trúc Hub - Client", "Mô hình Hub - Client")]:
        assert frozenset((a, b)) in pairs
    assert Canonicalize(store, embedding()).execute("baocao-canhan")[1]


def test_reasoning_fixture_cache_and_language_invalidation(tmp_path):
    store, judge, writer = fixture_store(tmp_path), FakeModel(), FakeModel()
    reasoning = CanonicalReasoning(judge, writer)
    assert reasoning.config()["partition_validation"] == "consistency-v1"
    first, _ = Canonicalize(store, embedding(), reasoning=reasoning).execute("baocao-canhan")
    assert first.payload["stage"] == "complete"
    assert any(n.get("description_sentences") for n in first.payload["nodes"])
    assert all(n["first_order_index"] >= n["first_mention_index"] for n in first.payload["nodes"])
    counts = len(judge.calls), len(writer.calls)
    assert Canonicalize(store, embedding(), reasoning=reasoning).execute("baocao-canhan")[1]
    assert counts == (len(judge.calls), len(writer.calls))
    reasoning.language_rule = "same-rule-new-version"
    second, _ = Canonicalize(store, embedding(), reasoning=reasoning).execute("baocao-canhan")
    assert len(judge.calls) == counts[0]
    assert len(writer.calls) > counts[1]
    assert any(row.get("reused") for row in second.payload["decision_log"])
    assert not (set(second.payload["members"]) & set(second.payload["redirects"]))
    for key in ["duplicate_description_count", "duplicate_description_name_count", "evidence_missing_name_count"]:
        assert first.manifest["stats"][key] == first.payload["candidate_quality"][key]
    assert first.payload["stats"]["merged_group_count"] == first.payload["stats"]["name_group_count"] - first.payload["stats"]["node_count"]
    assert first.payload["stats"]["cut_pairs_judged"] <= first.payload["stats"]["cut_edge_count"]
    assert isinstance(first.payload["deferred_pairs"], list)
    for key in ("partition_contradictions", "contradiction_retried_calls",
                "contradiction_deferred_calls", "merge_cache_invalid", "repair_cache_invalid"):
        assert first.payload["stats"][key] == 0


def test_invalid_cached_partition_is_replaced_by_one_model_call(tmp_path):
    store, judge, writer = fixture_store(tmp_path), FakeModel(), FakeModel()
    reasoning = CanonicalReasoning(judge, writer)
    first, _ = Canonicalize(store, embedding(), reasoning=reasoning).execute("baocao-canhan")
    payload = json.loads(json.dumps(first.payload))
    target = next(row for row in payload["decision_log"]
                  if row.get("stage") == "merge" and len(row["input"]["groups"]) >= 2)
    a, b = target["input"]["groups"][:2]
    target["output"]["relations"] = [{
        "source": a["group_id"], "target": b["group_id"], "edge_type": "same_as",
        "chunk_ids": [a["evidence"][0]["chunk_id"]], "reason": "stale cache fixture",
    }]
    store._write(first.path / "canonical.json", payload)
    calls = len(judge.calls)

    reasoning.language_rule = "same-rule-new-version"
    second, _ = Canonicalize(store, embedding(), reasoning=reasoning).execute("baocao-canhan")

    assert len(judge.calls) == calls + 1
    assert second.payload["stats"]["merge_cache_invalid"] == 1
    rows = [row for row in second.payload["decision_log"]
            if row.get("input_hash") == target["input_hash"]]
    assert len(rows) == 1 and rows[0]["reused"] is False
    assert "R2" in rows[0]["cache_invalid_error"]


def test_bad_model_is_deferred_and_bad_citations_keep_draft(tmp_path):
    store = fixture_store(tmp_path)
    judge, writer = FakeModel(invalid=10000), FakeModel(description_invalid=True)
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(judge, writer)).execute("baocao-canhan")
    assert result.payload["deferred"]
    assert result.payload["stats"]["text_node_count"] == 46
    # Clusters fail for a shape error, not a contradiction: they must not be counted as contradiction deferrals.
    assert result.payload["stats"]["merge_invalid"] > 0
    assert result.payload["stats"]["contradiction_deferred_calls"] == 0
    assert any(n.get("description_status") == "draft_fallback_invalid" for n in result.payload["nodes"])
    assert not any("outside" in (n["description"] or "") for n in result.payload["nodes"])


@pytest.mark.parametrize("repair", [False, True])
def test_merge_and_cut_pair_apply_to_real_fixture(tmp_path, monkeypatch, repair):
    store = fixture_store(tmp_path)
    def graph(groups, vectors, **kwargs):
        ids = {members[0].name: id for id, members in groups.items()}
        pair = [ids["WebSocket"], ids["WebSockets"]]
        edge = {"source": pair[0], "target": pair[1], "channels": ["alias"], "weight": 1.}
        return {"clusters": [] if repair else [pair], "edges": [edge], "cut_edges": [edge] if repair else [], "metrics": {}}
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    class Judge(FakeModel):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            if "pairs" in reply.payload:
                for row in reply.payload["pairs"]:
                    row["label"] = "same"
            return reply
    judge = Judge(invalid=1, merge_all=True)
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(judge, FakeModel())).execute("baocao-canhan")
    raw = {e["candidate_id"]: e["name"] for e in result.payload["source_candidates"]}
    assert any({"WebSocket", "WebSockets"} <= {raw[id] for id in n["members"]} for n in result.payload["nodes"])
    assert result.payload["stats"]["text_node_count"] == 45
    assert any(row.get("retries") == 1 for row in result.payload["decision_log"])


def test_gold_sheet_blind_deterministic_and_loader(tmp_path):
    store = fixture_store(tmp_path)
    Canonicalize(store, embedding()).execute("baocao-canhan")
    data = gold_items(store, ["baocao-canhan"])
    assert data == gold_items(store, ["baocao-canhan"])
    html = tmp_path / "sheet.html"
    write_gold_sheet(data, html)
    text = html.read_text(encoding="utf-8")
    assert "localStorage" in text and "Xuất JSON" in text
    assert '"channels"' not in text and '"weight"' not in text and "description_draft" not in text
    labeled = {**data, "annotator": "test", "annotated_at": "2026-09-11T00:00:00Z", "blind_before_first_a4_run": True,
               "items": [dict(item, label="uncertain" if item["kind"] == "pair" else "one_entity") for item in data["items"]]}
    path = tmp_path / "gold.json"
    store._write(path, labeled)
    assert load_gold(path, store, expected=data)["annotator"] == "test"
    assert load_gold(path, store, require_complete=True)["annotator"] == "test"
    raw = {e["candidate_id"]: e for e in store.load_latest_candidates("baocao-canhan").payload["entities"]}
    chunks = store.load_chunks("baocao-canhan", store.load_latest_candidates("baocao-canhan").manifest["upstream_version"])
    sections = {c.chunk_id: c.section_path for c in chunks.result.chunks}
    for item in data["items"]:
        for group in item["groups"]:
            for member in group["members"]:
                candidate = raw[member["candidate_id"]]
                own_ids = sorted({r["chunk_id"] for r in candidate["evidence"] + candidate["source_refs"]})
                assert member["section_paths"] == [sections[c] for c in own_ids]
    for field, value in [("group_id", "invalid"), ("symbols", ["invalid"])]:
        bad = json.loads(json.dumps(labeled))
        bad["items"][0]["groups"][0][field] = value
        store._write(path, bad)
        with pytest.raises(ValueError):
            load_gold(path, store)
    for mutation in [lambda d: d.update(blind_before_first_a4_run=False),
                     lambda d: d["items"][0].update(label="unknown"),
                     lambda d: d["items"][0].pop("label"),
                     lambda d: d["items"][0]["groups"][0]["members"][0].update(candidate_id="missing"),
                     lambda d: d["items"].pop()]:
        bad = json.loads(json.dumps(labeled)); mutation(bad); store._write(path, bad)
        with pytest.raises(ValueError):
            load_gold(path, store, expected=data)
        with pytest.raises(ValueError):
            load_gold(path, store, require_complete=True)


def test_legacy_gold_preserves_labels_and_rejects_changed_context(tmp_path):
    store = fixture_store(tmp_path)
    prepared, _ = Canonicalize(store, embedding()).execute("baocao-canhan")
    data = gold_items(store, ["baocao-canhan"])
    source = store.load_latest_candidates("baocao-canhan")
    sections = {c.chunk_id: c.section_path for c in store.load_chunks("baocao-canhan", source.manifest["upstream_version"]).result.chunks}
    nodes = {n["node_id"]: n for n in prepared.payload["nodes"]}
    for item in data["items"]:
        item["label"] = "related" if item["kind"] == "pair" else "one_entity"
        for group in item["groups"]:
            for member in group["members"]:
                member["section_paths"] = [sections[c] for c in nodes[group["group_id"]]["source_chunk_ids"]]
    data.update(annotator="legacy AI annotator", annotated_at="2026-09-11T16:38:45+07:00", blind_before_first_a4_run=True)
    data["sheet_id"] = digest([data["documents"], data["seed"], [i["item_id"] for i in data["items"]]])
    path = tmp_path / "legacy.json"
    store._write(path, data)
    for complete in [False, True]:
        assert load_gold(path, store, require_complete=complete) == data
    data["items"][0]["groups"][0]["members"][0]["section_paths"] = [["tampered"]]
    store._write(path, data)
    for complete in [False, True]:
        with pytest.raises(ValueError):
            load_gold(path, store, require_complete=complete)


def test_evaluation_hand_computed_eight_pairs():
    groups = {c: {"group_id": c, "members": [{"candidate_id": c}]} for c in "abcdef"}
    pairs = [("a", "b", "same"), ("c", "d", "same"), ("a", "e", "same"),
             ("a", "c", "different"), ("a", "d", "different"), ("b", "f", "related"),
             ("d", "e", "parent_child"), ("e", "f", "uncertain")]
    items = [{"item_id": str(i), "kind": "pair", "doc_id": "doc", "groups": [groups[a], groups[b]],
              "label": label, **({"child": 0} if label == "parent_child" else {})}
             for i, (a, b, label) in enumerate(pairs)]
    artifact = SimpleNamespace(version=4, payload={"doc_id": "doc", "nodes": [
        {"node_id": "n1", "members": ["a", "b", "c"]}, {"node_id": "n2", "members": ["d"]},
        {"node_id": "n3", "members": ["e"]}, {"node_id": "n4", "members": ["f"]}],
        "nominations": {"edges": [{"source": "a", "target": "b"}, {"source": "c", "target": "d"}]},
        "edges": [
            {"source": "n2", "target": "n3", "edge_type": "subtype_of", "origins": ["2a"]},
            {"source": "n1", "target": "n4", "edge_type": "subtype_of", "origins": ["2a"]},
            {"source": "n1", "target": "n4", "edge_type": "uses", "origins": ["2a"]},
            {"source": "n2", "target": "n1", "edge_type": "contrasts_with", "origins": ["2a"]},
            {"source": "n1", "target": "n4", "edge_type": "uses", "origins": ["a3"]},
        ]})
    second = [dict(i) for i in items]
    second[0]["label"] = "different"
    result = evaluate_canonical(artifact, {"items": items}, {"items": second})
    assert (result["tp"], result["fp"], result["fn"]) == (1, 1, 2)
    assert result["precision"] == .5 and result["recall"] == pytest.approx(1/3)
    assert result["f1"] == pytest.approx(.4)
    assert result["nomination_recall"] == pytest.approx(2/3)
    assert result["subtype_recall"] == 1 and result["uncertain_count"] == 1
    assert result["subtype_incorrect"] == 1 and result["subtype_precision"] == .5
    assert result["relations_2a_on_gold"] == {
        "same": 1, "parent_child": 0, "related": 1, "different": 1,
    }
    excluded = evaluate_canonical(artifact, {"items": items}, exclude_subtype_items={"6"})
    assert excluded["subtype_recall"] is None
    assert excluded["subtype_precision"] == .5
    # Agreement=7/8; expected agreement=(3*2+2*3+1+1+1)/64=15/64.
    assert result["agreement"]["kappa"] == pytest.approx(41/49)


def test_relation_on_collapsed_gold_pairs_is_counted_for_every_label():
    groups = {id: {"group_id": id, "members": [{"candidate_id": id}]} for id in "abcd"}
    gold = {"items": [
        {"item_id": "related", "kind": "pair", "doc_id": "doc",
         "groups": [groups["a"], groups["c"]], "label": "related"},
        {"item_id": "different", "kind": "pair", "doc_id": "doc",
         "groups": [groups["b"], groups["d"]], "label": "different"},
    ]}
    artifact = SimpleNamespace(version=1, payload={
        "doc_id": "doc",
        "nodes": [{"node_id": "n1", "members": ["a", "b"]},
                  {"node_id": "n2", "members": ["c", "d"]}],
        "nominations": {"edges": []},
        "edges": [{"source": "n1", "target": "n2", "edge_type": "uses", "origins": ["2a"]}],
    })

    result = evaluate_canonical(artifact, gold)

    assert result["relations_2a_on_gold"] == {
        "same": 0, "parent_child": 0, "related": 1, "different": 1,
    }


def test_changed_evidence_only_invalidates_affected_merge_decisions(tmp_path):
    store, judge, writer = fixture_store(tmp_path), FakeModel(), FakeModel()
    use_case = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(judge, writer))
    first, _ = use_case.execute("baocao-canhan")
    merge_log = [r for r in first.payload["decision_log"] if r.get("stage") == "merge"]
    target = merge_log[0]["input"]["groups"][0]["group_id"]
    candidate_id = first.payload["members"][target][0]
    source = store.load_latest_candidates("baocao-canhan")
    changed = json.loads(json.dumps(source.payload))
    entity = next(e for e in changed["entities"] if e["candidate_id"] == candidate_id)
    entity["evidence"][0]["quote"] += " changed evidence"
    store.save_candidates("baocao-canhan", source.manifest["source_hash"], "changed-evidence", {}, changed,
                          upstream_version=source.manifest["upstream_version"])
    second, _ = use_case.execute("baocao-canhan")
    new = [r for r in second.payload["decision_log"] if r.get("stage") == "merge"]
    assert sum(not r["reused"] for r in new) == 1
    assert sum(r["reused"] for r in new) == len(merge_log)-1
    assert any(not r["reused"] for r in second.payload["decision_log"] if r.get("stage") in {"describe", "check"})


@pytest.mark.parametrize("draft,keep,rewritten", [
    ("This is an English description.", True, True),
    ("Đây là mô tả được tài liệu hỗ trợ.", True, False),
    ("Đây là mô tả không được tài liệu hỗ trợ.", False, True),
])
def test_singleton_language_and_support_are_independent(tmp_path, monkeypatch, draft, keep, rewritten):
    store = fixture_store(tmp_path)
    prepared, _ = Canonicalize(store, embedding()).execute("baocao-canhan")
    target = next(n for n in prepared.payload["nodes"] if not n["media_id"] and len(n["members"]) == 1)
    source = store.load_latest_candidates("baocao-canhan")
    next(e for e in source.payload["entities"] if e["candidate_id"] == target["members"][0])["description_draft"] = draft
    store.save_candidates("baocao-canhan", source.manifest["source_hash"], "new-draft", {}, source.payload,
                          upstream_version=source.manifest["upstream_version"])
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph",
                        lambda *a, **k: {"clusters": [], "edges": [], "cut_edges": [], "metrics": {}})
    class Writer(FakeModel):
        def ask_json(self, prompt, *, response_schema):
            result = super().ask_json(prompt, response_schema=response_schema)
            for row in result.payload.get("nodes", []):
                if row["node_id"] == target["node_id"]:
                    row["keep"] = keep
            return result
    writer = Writer()
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(FakeModel(), writer)).execute("baocao-canhan")
    node = next(n for n in result.payload["nodes"] if n["node_id"] == target["node_id"])
    assert any(c.get("node_id") == target["node_id"] for c in writer.calls) == rewritten
    assert (draft in node["description"]) == (not rewritten)
    assert node["description_sentences"][0]["chunk_ids"]


def test_invalid_kept_draft_has_its_own_rewrite_metric(tmp_path, monkeypatch):
    store = fixture_store(tmp_path)
    prepared, _ = Canonicalize(store, embedding()).execute("baocao-canhan")
    target = next(n for n in prepared.payload["nodes"] if not n["media_id"] and len(n["members"]) == 1)
    source = store.load_latest_candidates("baocao-canhan")
    next(e for e in source.payload["entities"] if e["candidate_id"] == target["members"][0])["description_draft"] = "Một. Hai. Ba. Bốn. Năm."
    store.save_candidates("baocao-canhan", source.manifest["source_hash"], "invalid-draft", {}, source.payload,
                          upstream_version=source.manifest["upstream_version"])
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph",
                        lambda *a, **k: {"clusters": [], "edges": [], "cut_edges": [], "metrics": {}})
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(FakeModel(), FakeModel())).execute("baocao-canhan")
    node = next(n for n in result.payload["nodes"] if n["node_id"] == target["node_id"])
    assert "Một. Hai." not in node["description"]
    assert result.payload["stats"]["a5_rewritten_invalid_draft"] >= 1


@pytest.mark.parametrize("uncertain", [False, True])
def test_partition_subtype_direction_and_uncertainty(tmp_path, monkeypatch, uncertain):
    store = fixture_store(tmp_path)
    pair = []
    def graph(groups, vectors, **kwargs):
        ids = {members[0].name: id for id, members in groups.items()}
        pair[:] = [ids["WebSocket"], ids["WebSockets"]]
        return {"clusters": [pair], "edges": [], "cut_edges": [], "metrics": {}}
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph)
    class Judge(FakeModel):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            if uncertain:
                reply.payload = {"nodes": [], "deferred": [{"group_id": id, "reason": "uncertain fixture"} for id in pair], "relations": []}
            else:
                data = self.calls[-1]
                reply.payload["relations"] = [{"source": pair[0], "target": pair[1], "edge_type": "subtype_of",
                    "chunk_ids": [data["groups"][0]["evidence"][0]["chunk_id"]], "reason": "fixture direction"}]
            return reply
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(Judge(), FakeModel())).execute("baocao-canhan")
    assert result.payload["stats"]["text_node_count"] == 46
    if uncertain:
        assert set(result.payload["deferred"]) == set(pair)
        assert not any(e["edge_type"] == "subtype_of" for e in result.payload["edges"])
    else:
        assert any((e["source"], e["target"], e["edge_type"]) == (*pair, "subtype_of") for e in result.payload["edges"])


NAMES = ["WebSocket", "WebSockets", "Giao thức WebSockets", "Golang"]


def graph_with(clusters_by_name, cut_by_name):
    def graph(groups, vectors, **kwargs):
        ids = {members[0].name: id for id, members in groups.items()}
        edge = lambda a, b: {"source": ids[a], "target": ids[b], "channels": ["name"], "weight": .9}
        cut = [edge(a, b) for a, b in cut_by_name]
        inner = [edge(c[i], c[j]) for c in clusters_by_name for i in range(len(c)) for j in range(i + 1, len(c))]
        return {"clusters": [[ids[n] for n in c] for c in clusters_by_name], "edges": inner + cut,
                "cut_edges": cut, "metrics": {}}
    return graph


class NamedJudge(FakeModel):
    def __init__(self, partition=None, repair=None, subtype=None, relation=None):
        super().__init__()
        self.partition, self.repair, self.subtype = partition or {}, repair, subtype
        self.relation, self.prompts = relation, []

    def ask_json(self, prompt, *, response_schema):
        self.prompts.append(prompt)
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        if "groups" in data:
            by = {g["name"]: g["group_id"] for g in data["groups"]}
            key = frozenset(by)
            if key not in self.partition and self.repair == "invalid":
                return SimpleNamespace(payload={"nodes": [], "deferred": [], "relations": []}, raw_text="invalid repair")
            if key not in self.partition and self.repair == "uncertain":
                return SimpleNamespace(payload={"nodes": [], "deferred": [{"group_id": id, "reason": "uncertain fixture"} for id in by.values()],
                                                "relations": []}, raw_text="uncertain repair")
            plan = self.partition.get(key, [[*by]] if self.repair == "same" else [[n] for n in by])
            nodes = [{"groups": [by[n] for n in group], "reason": "fixture"} for group in plan if not group[0].startswith("~")]
            deferred = [{"group_id": by[group[0][1:]], "reason": "fixture"} for group in plan if group[0].startswith("~")]
            relation = self.relation or ((*self.subtype[:2], "subtype_of", self.subtype[2]) if self.subtype else None)
            edges = []
            if relation and {relation[0], relation[1]} <= set(by):
                source, target, edge_type, chunk = relation
                edges = [{"source": by[source], "target": by[target], "edge_type": edge_type,
                          "chunk_ids": [chunk], "reason": "fixture"}]
            return SimpleNamespace(payload={"nodes": nodes, "deferred": deferred, "relations": edges}, raw_text="rejected fixture")
        return super().ask_json(prompt, response_schema=response_schema)


def run_named(tmp_path, monkeypatch, judge, clusters, cut):
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph_with(clusters, cut))
    store = fixture_store(tmp_path)
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(judge, FakeModel())).execute("baocao-canhan")
    raw = {e["candidate_id"]: e["name"] for e in result.payload["source_candidates"]}
    nodes = [frozenset(raw[m] for m in n["members"]) & set(NAMES) for n in result.payload["nodes"]]
    return result, [n for n in nodes if n]


def test_start_session_error_is_logged_and_retried_not_crash(tmp_path, monkeypatch):
    pair = ["WebSocket", "WebSockets"]

    class FlakySession(NamedJudge):
        failed = False

        def start_session(self, prompt):
            if not FlakySession.failed:
                FlakySession.failed = True
                raise ValueError("phiên hỏng")
            return self

    judge = FlakySession(partition={frozenset(pair): [pair]})
    result, nodes = run_named(tmp_path, monkeypatch, judge, [pair], [])

    assert frozenset(pair) in nodes
    row = next(
        item
        for item in result.payload["decision_log"]
        if item.get("stage") == "merge"
    )
    assert row["retries"] == 1
    assert row["attempts"][0]["raw_text"] is None


def test_repair_merges_only_when_whole_union_becomes_one_node(
    tmp_path, monkeypatch
):
    left = ["WebSocket", "WebSockets"]
    combined = [*left, "Giao thức WebSockets"]
    judge = NamedJudge(
        partition={
            frozenset(left): [left],
            frozenset(combined): [
                ["WebSockets", "Giao thức WebSockets"],
                ["WebSocket"],
            ],
        }
    )

    result, nodes = run_named(
        tmp_path,
        monkeypatch,
        judge,
        [left],
        [("WebSockets", "Giao thức WebSockets")],
    )

    assert frozenset(left) in nodes
    assert frozenset({"Giao thức WebSockets"}) in nodes
    assert result.payload["stats"].get("repair_merged_pairs", 0) == 0


def test_uncertain_repair_is_pair_scoped_not_group_deferral(
    tmp_path, monkeypatch
):
    pair = ["WebSocket", "WebSockets"]
    judge = NamedJudge(partition={frozenset(pair): [pair]}, repair="uncertain")

    result, _ = run_named(
        tmp_path,
        monkeypatch,
        judge,
        [pair],
        [("WebSockets", "Giao thức WebSockets")],
    )

    assert result.payload["deferred"] == []
    assert len(result.payload["deferred_pairs"]) == 1


def test_invalid_relation_is_dropped_not_the_partition(tmp_path, monkeypatch):
    trio = ["WebSocket", "WebSockets", "Giao thức WebSockets"]
    judge = NamedJudge(partition={frozenset(trio): [["WebSocket", "WebSockets"], ["Giao thức WebSockets"]]},
                       subtype=("Giao thức WebSockets", "WebSocket", "c_outside"))
    result, nodes = run_named(tmp_path, monkeypatch, judge, [trio], [])
    assert frozenset({"WebSocket", "WebSockets"}) in nodes
    assert not [e for e in result.payload["edges"] if e["edge_type"] == "subtype_of"]
    rejected = next(r["edge"] for r in result.payload["decision_log"] if r.get("stage") == "relation_rejected")
    assert rejected["source"] and rejected["target"]
    assert rejected["invalid_chunk_ids"] == ["c_outside"]
    assert rejected["allowed_chunk_ids"]


def test_requires_from_judge_is_rejected_before_artifact(tmp_path, monkeypatch):
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"] if e["name"] == "WebSocket")["evidence"][0]["chunk_id"]
    pair = ["WebSocket", "WebSockets"]
    judge = NamedJudge(relation=(pair[0], pair[1], "requires", chunk))

    result, _ = run_named(tmp_path, monkeypatch, judge, [pair], [])

    assert not [e for e in result.payload["edges"]
                if e["edge_type"] == "requires" and "2a" in e["origins"]]
    assert any(row.get("stage") == "relation_rejected"
               and row["edge"]["edge_type"] == "requires" for row in result.payload["decision_log"])


def test_open_relation_becomes_proposed_edge_with_2a_origin_and_metrics(tmp_path, monkeypatch):
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"] if e["name"] == "WebSocket")["evidence"][0]["chunk_id"]
    pair = ["WebSocket", "WebSockets"]
    judge = NamedJudge(relation=(pair[0], pair[1], " Uses ", chunk))

    result, _ = run_named(tmp_path, monkeypatch, judge, [pair], [])

    names = {n["node_id"]: n["name"] for n in result.payload["nodes"]}
    edge = next(e for e in result.payload["edges"]
                if (names[e["source"]], names[e["target"]], e["edge_type"]) == (*pair, "uses"))
    assert edge["origins"] == ["2a"] and edge["proposal"] and not edge["confirmed"]
    assert result.payload["stats"]["relation_types"] == {"uses": 1}
    assert result.payload["stats"]["relation_edges"] == result.payload["stats"]["relation_new_pair"] == 1
    assert result.payload["stats"]["relation_rejected"] == result.payload["stats"]["relation_self_removed"] == 0


def test_relation_matching_a3_edge_is_merged_with_both_origins(tmp_path, monkeypatch):
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"] if e["name"] == "Mutex")["evidence"][0]["chunk_id"]
    pair = ["Mutex", "Race Condition"]
    judge = NamedJudge(relation=(pair[0], pair[1], "uses", chunk))

    result, _ = run_named(tmp_path, monkeypatch, judge, [pair], [])

    names = {n["node_id"]: n["name"] for n in result.payload["nodes"]}
    edges = [e for e in result.payload["edges"]
             if (names[e["source"]], names[e["target"]], e["edge_type"]) == (*pair, "uses")]
    assert len(edges) == 1
    assert edges[0]["origins"] == ["2a", "a3"]
    assert edges[0]["evidence"] and edges[0]["reason"] == "fixture"
    assert result.payload["stats"]["relation_same_as_a3"] == 1
    assert result.payload["stats"]["relation_other_type_than_a3"] == 0


def test_relation_on_reversed_a3_pair_with_other_type_is_counted(tmp_path, monkeypatch):
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"] if e["name"] == "Race Condition")["evidence"][0]["chunk_id"]
    pair = ["Race Condition", "Mutex"]
    judge = NamedJudge(relation=(pair[0], pair[1], "contrasts_with", chunk))

    result, _ = run_named(tmp_path, monkeypatch, judge, [pair], [])

    stats = result.payload["stats"]
    assert stats["relation_edges"] == stats["relation_other_type_than_a3"] == 1
    assert stats["relation_same_as_a3"] == stats["relation_new_pair"] == 0
    assert stats["relation_edges"] == sum(stats[key] for key in
        ("relation_same_as_a3", "relation_same_type_reversed_a3",
         "relation_other_type_than_a3", "relation_new_pair"))


def test_relation_with_same_type_reversed_from_a3_is_not_counted_as_other_type(tmp_path, monkeypatch):
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"] if e["name"] == "Race Condition")["evidence"][0]["chunk_id"]
    pair = ["Race Condition", "Mutex"]
    judge = NamedJudge(relation=(pair[0], pair[1], "uses", chunk))

    result, _ = run_named(tmp_path, monkeypatch, judge, [pair], [])

    stats = result.payload["stats"]
    assert stats["relation_edges"] == stats["relation_same_type_reversed_a3"] == 1
    assert stats["relation_other_type_than_a3"] == 0


def test_duplicate_relations_across_calls_are_merged_deterministically(tmp_path, monkeypatch):
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"] if e["name"] == "WebSocket")["evidence"][0]["chunk_id"]
    pair = ["WebSocket", "WebSockets"]
    class DifferentReasons(NamedJudge):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            for edge in reply.payload.get("relations", []):
                edge["reason"] = "repair reason" if data.get("repair_of_cut_edge") else "merge reason"
            return reply

    judge = DifferentReasons(relation=(pair[0], pair[1], "uses", chunk))

    result, _ = run_named(tmp_path, monkeypatch, judge, [pair], [(pair[0], pair[1])])

    names = {n["node_id"]: n["name"] for n in result.payload["nodes"]}
    edges = [e for e in result.payload["edges"]
             if (names[e["source"]], names[e["target"]], e["edge_type"]) == (*pair, "uses")]
    assert len(edges) == 1
    assert edges[0]["reason"] == "merge reason"
    assert result.payload["stats"]["relation_edges"] == 1


@pytest.mark.parametrize("always_contradictory", [False, True])
def test_contradictory_partition_is_retried_then_applied_or_deferred(
    tmp_path, monkeypatch, always_contradictory
):
    pair = ["WebSocket", "WebSockets"]

    class ContradictingJudge(NamedJudge):
        partition_calls = 0

        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if "groups" in data:
                self.partition_calls += 1
                if always_contradictory or self.partition_calls == 1:
                    ids = [group["group_id"] for group in data["groups"]]
                    reply.payload = {
                        "nodes": [{"groups": ids, "reason": "fixture"}], "deferred": [],
                        "relations": [{"source": ids[0], "target": ids[1], "edge_type": "uses",
                                       "chunk_ids": [data["groups"][0]["evidence"][0]["chunk_id"]],
                                       "reason": "contradictory fixture"}],
                    }
                    reply.raw_text = "contradictory fixture"
            return reply

    judge = ContradictingJudge(partition={frozenset(pair): [pair]})
    result, nodes = run_named(tmp_path, monkeypatch, judge, [pair], [])
    row = next(item for item in result.payload["decision_log"] if item.get("stage") == "merge")
    stats = result.payload["stats"]

    assert "R1" in row["attempts"][0]["error"]
    contradiction_attempts = sum(
        "R1:" in attempt["error"] or "R2:" in attempt["error"]
        for item in result.payload["decision_log"]
        for attempt in item.get("attempts", [])
    )
    assert stats["partition_contradictions"] == contradiction_attempts
    assert stats["partition_contradictions"] == (2 if always_contradictory else 1)
    assert stats["contradiction_retried_calls"] == 1
    assert stats["contradiction_deferred_calls"] == int(always_contradictory)
    if always_contradictory:
        assert row["valid"] is False and len(result.payload["deferred"]) == 2
        assert all(frozenset([name]) in nodes for name in pair)
    else:
        assert row["valid"] is True and row["retries"] == 1
        assert frozenset(pair) in nodes


def test_contradiction_metrics_survive_a_rerun_from_cache(tmp_path, monkeypatch):  # F82
    pair = ["WebSocket", "WebSockets"]

    class ContradictOnce(NamedJudge):
        partition_calls = 0

        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if "groups" in data:
                self.partition_calls += 1
                if self.partition_calls == 1:
                    ids = [group["group_id"] for group in data["groups"]]
                    reply.payload = {
                        "nodes": [{"groups": ids, "reason": "fixture"}], "deferred": [],
                        "relations": [{"source": ids[0], "target": ids[1], "edge_type": "uses",
                                       "chunk_ids": [data["groups"][0]["evidence"][0]["chunk_id"]],
                                       "reason": "contradictory fixture"}],
                    }
            return reply

    judge = ContradictOnce(partition={frozenset(pair): [pair]})
    first, _ = run_named(tmp_path, monkeypatch, judge, [pair], [])
    calls = judge.partition_calls
    reasoning = CanonicalReasoning(judge, FakeModel())
    reasoning.language_rule = "same-rule-new-version"  # new artifact, same merge decisions

    second, reused = Canonicalize(JsonArtifactStore(tmp_path), embedding(), reasoning=reasoning).execute("baocao-canhan")

    assert not reused and judge.partition_calls == calls
    assert first.payload["stats"]["partition_contradictions"] == 1
    for key in ("partition_contradictions", "contradiction_retried_calls", "contradiction_deferred_calls"):
        assert second.payload["stats"][key] == first.payload["stats"][key]


def test_relation_from_repair_between_groups_merged_by_cluster_is_removed(tmp_path, monkeypatch):
    pair = ["WebSocket", "WebSockets"]
    third = "Giao thức WebSockets"
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"]
                 if e["name"] == pair[0])["evidence"][0]["chunk_id"]

    class RepairRelation(NamedJudge):
        def ask_json(self, prompt, *, response_schema):
            reply = super().ask_json(prompt, response_schema=response_schema)
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            if data.get("repair_of_cut_edge"):
                by = {group["name"]: group["group_id"] for group in data["groups"]}
                reply.payload["relations"] = [{
                    "source": by[pair[0]], "target": by[pair[1]], "edge_type": "uses",
                    "chunk_ids": [chunk], "reason": "repair fixture",
                }]
            return reply

    judge = RepairRelation(partition={frozenset(pair): [pair]})
    result, nodes = run_named(tmp_path, monkeypatch, judge, [pair], [(pair[1], third)])

    assert frozenset(pair) in nodes
    assert result.payload["stats"]["relation_self_removed"] == 1
    assert not [edge for edge in result.payload["edges"] if "2a" in edge["origins"]]


@pytest.mark.parametrize("repair", ["uncertain", "invalid"])
def test_repair_deferral_keeps_existing_cluster_merge(tmp_path, monkeypatch, repair):
    pair = ["WebSocket", "WebSockets"]
    judge = NamedJudge(partition={frozenset(pair): [pair]}, repair=repair)
    result, nodes = run_named(tmp_path, monkeypatch, judge, [pair], [("WebSockets", "Giao thức WebSockets")])
    assert frozenset(pair) in nodes and frozenset({"Giao thức WebSockets"}) in nodes
    assert result.payload["stats"]["transitive_conflicts"] == 0
    if repair == "invalid":
        assert result.payload["stats"].get("cut_pairs_judged", 0) == 0


def test_cluster_deferred_group_is_not_merged_later_and_does_not_undo_others(tmp_path, monkeypatch):
    left, right = ["WebSocket", "WebSockets"], ["Giao thức WebSockets", "Golang"]
    judge = NamedJudge(partition={frozenset(left): [left], frozenset(right): [["~Giao thức WebSockets"], ["Golang"]]},
                       repair="same")
    result, nodes = run_named(tmp_path, monkeypatch, judge, [left, right], [("WebSockets", "Giao thức WebSockets")])
    assert frozenset(left) in nodes and frozenset({"Giao thức WebSockets"}) in nodes
    assert result.payload["stats"]["transitive_conflicts"] == 0


def test_cut_edge_is_rejudged_as_a_cluster_with_both_nodes_context(tmp_path, monkeypatch):
    left = ["WebSocket", "WebSockets"]
    combined = [*left, "Giao thức WebSockets"]
    judge = NamedJudge(partition={frozenset(left): [left], frozenset(combined): [combined]})
    result, nodes = run_named(tmp_path, monkeypatch, judge, [left], [("WebSockets", "Giao thức WebSockets")])
    assert frozenset(combined) in nodes
    repair_inputs = [json.loads(p.split("\nCorrect this validation error:")[0]) for p in judge.prompts
                     if {g["name"] for g in json.loads(p.split("\nCorrect this validation error:")[0]).get("groups", [])} == set(combined)]
    assert len(repair_inputs) == 1
    assert result.payload["stats"]["repair_merged_pairs"] == 1


def test_retry_names_missing_group_and_log_keeps_rejected_output(tmp_path, monkeypatch):
    trio = ["WebSocket", "WebSockets", "Giao thức WebSockets"]
    judge = NamedJudge(partition={frozenset(trio): [["WebSocket"], ["WebSockets"]]})
    result, _ = run_named(tmp_path, monkeypatch, judge, [trio], [])
    missing = next(g["group_id"] for g in json.loads(judge.prompts[0])["groups"] if g["name"] == "Giao thức WebSockets")
    assert missing in judge.prompts[1].split("Correct this validation error:")[1]
    row = next(r for r in result.payload["decision_log"] if r.get("stage") == "merge" and r.get("valid") is False)
    assert row.get("attempts") and all(a["raw_text"] == "rejected fixture" for a in row["attempts"])


def test_transport_error_aborts_without_freezing_artifact(tmp_path, monkeypatch):
    from doc2roadmap.application.ports.extraction import ModelTransportError
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph",
                        graph_with([["WebSocket", "WebSockets"]], []))
    class Flaky(FakeModel):
        down = True
        def ask_json(self, prompt, *, response_schema):
            if Flaky.down and '\"groups\"' in prompt:
                raise ModelTransportError("Gemini API trả HTTP 503")
            return super().ask_json(prompt, response_schema=response_schema)
    store = fixture_store(tmp_path)
    make = lambda: Canonicalize(store, embedding(), reasoning=CanonicalReasoning(Flaky(merge_all=True), FakeModel()))
    with pytest.raises(ModelTransportError):
        make().execute("baocao-canhan")
    Flaky.down = False
    result, reused = make().execute("baocao-canhan")
    assert not reused and result.payload["stats"]["deferred_groups"] == 0


def test_subtype_conflicting_with_a3_edge_is_kept_and_logged(tmp_path, monkeypatch):  # F75
    source = json.loads(Path("tests/fixtures/a4/baocao-canhan/input.json").read_text(encoding="utf-8"))
    chunk = next(e for e in source["candidate_payload"]["entities"] if e["name"] == "Mutex")["evidence"][0]["chunk_id"]
    pair = ["Mutex", "Race Condition"]
    judge = NamedJudge(partition={frozenset(pair): [["Mutex"], ["Race Condition"]]},
                       subtype=("Mutex", "Race Condition", chunk))
    result, _ = run_named(tmp_path, monkeypatch, judge, [pair], [])
    names = {n["node_id"]: n["name"] for n in result.payload["nodes"]}
    typed = {(names[e["source"]], names[e["target"]], e["edge_type"]) for e in result.payload["edges"]}
    # A3 and 2a disagree; the gold set sided with 2a in most such pairs, so both edges stay.
    assert ("Mutex", "Race Condition", "uses") in typed
    assert ("Mutex", "Race Condition", "subtype_of") in typed
    row = next(r for r in result.payload["decision_log"] if r.get("stage") == "subtype_conflicts_a3")
    assert row["edge"]["a3_edge_types"] == ["uses"]
    assert result.payload["stats"]["subtype_conflicts_a3"] == 1
