import unicodedata

import pytest

from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges
from doc2roadmap.domain.canonical import digest
from tests.unit.application.test_build_secondary_edges import Store


class Tokenize:
    identifier = "fake-word-tokenizer-v1"

    def __call__(self, text):
        return text.split()


class Scorer:
    metadata = {"version": "fake-v1", "model_sha256": "abc", "calibration_sha256": "def"}

    def __init__(self, scores=None, probability=.8):
        self.scores, self.probability = scores, probability
        self.calls = 0

    def score(self, rows):
        self.calls += 1
        return self.scores if self.scores is not None else [.8] * len(rows)

    def calibrate(self, scores):
        return self.probability if isinstance(self.probability, list) else [self.probability] * len(scores)


def fixture():
    store = Store()
    chunk = store.chunks.result.chunks[0]
    chunk.text = "Alpha là cơ sở. Beta là một Alpha."
    chunk.parent_section_id, chunk.section_path, chunk.role = "s1", ["Chương", "Mục"], "noi_dung"
    for node, name, anchor in zip(store.main.payload["nodes"], ("Alpha", "Beta"),
                                  ("Alpha là cơ sở.", "Beta là một Alpha.")):
        node.update(name=name, teaching_status="taught", anchor={"chunk_id": "c1", "sentence": anchor})
    store.main.manifest["config"] = {"definition_before": 0, "definition_after": 0}
    store.main.payload["cost_summary"] = {"usd": .25, "input_tokens": 10, "output_tokens": 5}
    return store


def test_execute_creates_only_hard_contract_edges_preserves_cost_and_reuses_cache():
    store, scorer = fixture(), Scorer()
    stage = BuildSecondaryMLEdges(store, scorer, Tokenize())
    artifact, reused = stage.execute("doc")
    assert not reused
    edge, = artifact.payload["secondary_edges"]
    assert (edge["source"], edge["target"], edge["quote"]) == ("a", "b", "Beta là một Alpha.")
    assert edge["prerequisite_kind"] == "can_de_hieu" and edge["evidence_kind"] == "trong_dinh_nghia"
    assert not edge.get("soft") and edge["explicit_evidence"]
    assert artifact.payload["secondary_log"][0]["status"] == "created"
    assert artifact.payload["stats"]["expected_positive_count"] == 1
    assert artifact.payload["cost_summary"] == {"usd": .25, "input_tokens": 10, "output_tokens": 5,
                                                "main_usd": .25, "secondary_usd": 0.0}
    assert artifact.manifest["config"]["mode"] == "ml"
    again, reused = stage.execute("doc")
    assert reused and again is artifact and scorer.calls == 1
    fresh, _ = BuildSecondaryMLEdges(fixture(), Scorer(), Tokenize()).execute("doc")
    assert digest(fresh.payload) == digest(artifact.payload)


def test_k_zero_and_no_candidates_never_create_edges():
    for probability in (0.0, .4):
        artifact, _ = BuildSecondaryMLEdges(fixture(), Scorer(probability=probability), Tokenize()).execute("doc")
        assert artifact.payload["secondary_edges"] == []
        assert artifact.payload["secondary_log"][0]["status"] == "below_threshold"
        assert artifact.payload["stats"]["threshold"] is None
    store = fixture()
    store.main.payload["nodes"][1]["teaching_status"] = "mentioned_only"
    artifact, _ = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    assert artifact.payload["stats"]["secondary_candidate_count"] == 0
    assert artifact.payload["secondary_edges"] == []


def test_higher_direction_and_threshold_are_selected_from_calibrated_candidate_scores():
    store = fixture()
    chunk = store.chunks.result.chunks[0]
    chunk.text = "Alpha cần Beta. Beta cần Alpha."
    for node, quote in zip(store.main.payload["nodes"], ("Alpha cần Beta.", "Beta cần Alpha.")):
        node["anchor"]["sentence"] = quote
    # Both directions eligible. k=round(.4+.4)=1, so threshold=.9 and reverse wins.
    artifact, _ = BuildSecondaryMLEdges(store, Scorer([.2, .9], .4), Tokenize()).execute("doc")
    edge, = artifact.payload["secondary_edges"]
    assert (edge["source"], edge["target"]) == ("b", "a")
    assert artifact.payload["stats"]["threshold"] == .9


def test_actual_main_contract_rejects_quote_not_in_original_evidence_chunk():
    store = fixture()
    # Window is NFC, but original evidence is decomposed: the main contract rejects this quote.
    store.chunks.result.chunks[0].text = unicodedata.normalize("NFD", store.chunks.result.chunks[0].text)
    artifact, _ = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    assert artifact.payload["secondary_edges"] == []
    assert artifact.payload["secondary_log"][0]["status"] == "no_evidence"
    assert artifact.payload["executor_log"][0]["error"] == "quote_outside_evidence_chunk"


def test_new_edge_prunes_later_pair_and_main_pruning_excludes_threshold_population():
    store = fixture()
    store.main.payload["suspected_pairs"].append({"pair_id": "zz", "left": "a", "right": "b"})
    artifact, _ = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    assert len(artifact.payload["secondary_edges"]) == 1
    assert [r["status"] for r in artifact.payload["secondary_log"]] == ["created", "pruned_direct_edge"]
    store = fixture()
    store.main.payload["main_edges"] = [{"source": "a", "target": "b", "edge_type": "requires"}]
    artifact, _ = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    assert artifact.payload["stats"]["secondary_candidate_count"] == 0
    assert artifact.payload["stats"]["expected_positive_count"] == 0
    assert artifact.payload["secondary_log"][0]["status"] == "pruned_direct_edge"


def test_plan_zero_cost_no_scoring_and_refuses_incomplete_main():
    store, scorer = fixture(), Scorer()
    stage = BuildSecondaryMLEdges(store, scorer, Tokenize())
    plan = stage.plan("doc").to_dict()
    assert (plan["calls_estimate"], plan["usd_estimate"]) == (0, 0.0)
    assert scorer.calls == 0 and store.saved_versions == 0
    store.main.payload["main_complete"] = False
    with pytest.raises(ValueError, match="pass chính hoàn chỉnh"):
        stage.execute("doc")


@pytest.mark.parametrize("field", ["model_sha256", "calibration_sha256", "version", "feature_names"])
def test_model_hash_changes_invalidate_cache(field):
    store, scorer = fixture(), Scorer()
    BuildSecondaryMLEdges(store, scorer, Tokenize()).execute("doc")
    different = Scorer()
    different.metadata = {**scorer.metadata, field: "changed"}
    _, reused = BuildSecondaryMLEdges(store, different, Tokenize()).execute("doc")
    assert not reused and different.calls == 1 and store.saved_versions == 2


def test_actual_below_threshold_pair_and_main_pruning_do_not_raise_threshold():
    store = fixture()
    nodes = store.main.payload["nodes"]
    nodes.append({**nodes[1], "node_id": "c", "name": "Gamma",
                  "anchor": {"chunk_id": "c1", "sentence": "Gamma là một Alpha."}})
    store.chunks.result.chunks[0].text += " Gamma là một Alpha."
    store.main.payload["suspected_pairs"].append({"pair_id": "ac", "left": "a", "right": "c"})
    artifact, _ = BuildSecondaryMLEdges(store, Scorer([.9, .2], .4), Tokenize()).execute("doc")
    assert [r["status"] for r in artifact.payload["secondary_log"]] == ["created", "below_threshold"]
    assert len(artifact.payload["secondary_edges"]) == 1
    assert artifact.payload["secondary_log"][1]["score"] == .2
    # A high-probability already-solved pair must not enter the threshold population.
    store = fixture()
    store.main.payload["nodes"].append({**store.main.payload["nodes"][1], "node_id": "c", "name": "Gamma",
                                       "anchor": {"chunk_id": "c1", "sentence": "Gamma là một Alpha."}})
    store.chunks.result.chunks[0].text += " Gamma là một Alpha."
    store.main.payload["suspected_pairs"].append({"pair_id": "ac", "left": "a", "right": "c"})
    store.main.payload["main_edges"] = [{"source": "a", "target": "b", "edge_type": "requires"}]
    artifact, _ = BuildSecondaryMLEdges(store, Scorer([.6], .4), Tokenize()).execute("doc")
    assert artifact.payload["stats"]["expected_positive_count"] == 0
    assert artifact.payload["secondary_edges"] == []


def test_new_hard_path_prunes_later_pair_and_model_provenance_changes_cache():
    store = fixture()
    nodes = store.main.payload["nodes"]
    nodes.append({**nodes[1], "node_id": "c", "name": "Gamma",
                  "anchor": {"chunk_id": "c1", "sentence": "Gamma là Beta và Alpha."}})
    store.chunks.result.chunks[0].text += " Gamma là Beta và Alpha."
    store.main.payload["suspected_pairs"] = [
        {"pair_id": "1ab", "left": "a", "right": "b"},
        {"pair_id": "2bc", "left": "b", "right": "c"},
        {"pair_id": "3ac", "left": "a", "right": "c"},
    ]
    artifact, _ = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    assert len(artifact.payload["secondary_edges"]) == 2
    assert [r["status"] for r in artifact.payload["secondary_log"]] == ["created", "created", "pruned_explicit_path"]


def test_quote_nearest_anchor_that_passes_contract_is_used():
    store = fixture()
    store.main.manifest["config"]["definition_before"] = 1
    chunk = store.chunks.result.chunks[0]
    chunk.text = "Une Alpha example. Beta là một Alpha."
    store.main.payload["nodes"][0]["anchor"]["sentence"] = "Une Alpha example."
    artifact, _ = BuildSecondaryMLEdges(store, Scorer([.8], .8), Tokenize()).execute("doc")
    assert artifact.payload["secondary_edges"][0]["quote"] == "Beta là một Alpha."


def test_rejected_nearest_quote_falls_back_to_first_valid_quote():
    store = fixture()
    store.main.manifest["config"]["definition_before"] = 1
    store.chunks.result.chunks[0].text = "Alpha is a basis. " + unicodedata.normalize("NFD", "Beta là một Alpha.")
    store.main.payload["nodes"][0]["anchor"]["sentence"] = "Alpha is a basis."
    artifact, _ = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    assert artifact.payload["executor_log"][0]["error"] == "quote_outside_evidence_chunk"
    assert artifact.payload["secondary_edges"][0]["quote"] == "Alpha is a basis."


def threshold_fixture(specs):
    """One candidate direction per pair; all quotes use the real main contract."""
    store = fixture()
    names = {key: "Concept" + key for spec in specs for key in spec[:2]}
    template = store.main.payload["nodes"][0]
    sentences = {y: f"{names[y]} là khái niệm dùng " + " và ".join(
        names[x] for x in sorted({x for x, target, _, _ in specs if target == y})) + "." for y in names}
    store.main.payload["nodes"] = [
        {**template, "node_id": key, "name": name, "anchor": {"chunk_id": "c1", "sentence": sentences[key]}}
        for key, name in names.items()]
    store.chunks.result.chunks[0].text = " ".join(sentences.values())
    store.main.payload["mention_map"] = {"c1": {key: {} for key in names}}
    store.main.payload["suspected_pairs"] = [
        {"pair_id": f"{i:02}", "left": x, "right": y} for i, (x, y, _, _) in enumerate(specs)]
    scorer = Scorer([score for _, _, score, _ in specs], [p for _, _, _, p in specs])
    return store, scorer


def test_fixed_point_changes_initial_threshold_and_discards_trial_edges_and_logs():
    store, scorer = threshold_fixture([
        ("b", "c", .8, .79), ("b", "d", .7, .71), ("c", "f", .8, .79), ("b", "f", .5, .55)])
    artifact, _ = BuildSecondaryMLEdges(store, scorer, Tokenize()).execute("doc")
    stats = artifact.payload["stats"]
    assert {(e["source"], e["target"]) for e in artifact.payload["secondary_edges"]} == {("b", "c"), ("c", "f")}
    assert stats["threshold_history"] == [.7, .8] and stats["threshold"] == .8
    assert stats["threshold_iterations"] == 2 and not stats["threshold_oscillation"]
    assert stats["expected_positive_count"] == 2
    assert [r["status"] for r in artifact.payload["secondary_log"]] == ["created", "below_threshold", "created", "pruned_explicit_path"]
    assert len(artifact.payload["executor_log"]) == 2  # only final accepted proposals, no trial operations
    assert scorer.calls == 1 and store.saved_versions == 1


def test_two_threshold_cycle_selects_larger_threshold_not_last_computed():
    store, scorer = threshold_fixture([("a", "b", .8, .6), ("a", "b", .8, .6), ("c", "d", .9, .6)])
    artifact, _ = BuildSecondaryMLEdges(store, scorer, Tokenize()).execute("doc")
    stats = artifact.payload["stats"]
    assert {(e["source"], e["target"]) for e in artifact.payload["secondary_edges"]} == {("c", "d")}
    assert stats["threshold_history"] == [.8, .9] and stats["threshold"] == .9
    assert stats["threshold_iterations"] == 2 and stats["threshold_oscillation"]
    assert len(artifact.payload["secondary_log"]) == 3 and len(artifact.payload["executor_log"]) == 1


def test_zero_k_after_dynamic_pruning_removes_trial_edges_and_stops():
    store, scorer = threshold_fixture([("a", "b", .9, .3), ("a", "b", .9, .3)])
    artifact, _ = BuildSecondaryMLEdges(store, scorer, Tokenize()).execute("doc")
    assert artifact.payload["secondary_edges"] == []
    assert artifact.payload["stats"]["threshold"] is None
    assert artifact.payload["stats"]["expected_positive_count"] == 0
    assert artifact.payload["stats"]["threshold_iterations"] == 1
    assert [r["status"] for r in artifact.payload["secondary_log"]] == ["below_threshold", "below_threshold"]
    assert artifact.payload["executor_log"] == []


def test_cycle_reassembles_chosen_threshold_instead_of_saving_last_trial():
    store, scorer = threshold_fixture([
        ("b", "c", .8, .79), ("a", "b", .6, .63), ("a", "c", .1, .23),
        ("c", "d", .9, .87), ("b", "d", .9, .87)])
    store.main.payload["executor_log"] = [{"stage": "main", "keep": True}]
    artifact, _ = BuildSecondaryMLEdges(store, scorer, Tokenize()).execute("doc")
    stats = artifact.payload["stats"]
    assert stats["threshold_history"] == [.8, .6] and stats["threshold"] == .8
    assert stats["threshold_oscillation"] and stats["threshold_final_reassembled"]
    assert {(e["source"], e["target"]) for e in artifact.payload["secondary_edges"]} == {("b", "c"), ("c", "d")}
    assert [r["status"] for r in artifact.payload["secondary_log"]] == [
        "created", "below_threshold", "below_threshold", "created", "pruned_explicit_path"]
    assert all(r["threshold"] == .8 for r in artifact.payload["secondary_log"])
    assert len(artifact.payload["executor_log"]) == 3 and artifact.payload["executor_log"][0] == {"stage": "main", "keep": True}
    assert scorer.calls == 1 and store.saved_versions == 1


def test_cycle_maximum_excludes_transient_threshold_before_cycle():
    store, scorer = threshold_fixture([
        ("c", "d", .5, .6), ("d", "e", .8, .2), ("e", "f", .1, .5), ("e", "f", .5, .1),
        ("e", "f", .2, .7), ("c", "d", .6, .4), ("a", "e", .7, .8), ("a", "c", .8, .1),
        ("a", "f", .7, .4), ("a", "c", .3, .7), ("a", "d", .4, .9), ("a", "d", .1, .6)])
    artifact, _ = BuildSecondaryMLEdges(store, scorer, Tokenize()).execute("doc")
    stats = artifact.payload["stats"]
    assert stats["threshold_history"] == [.5, .8, .6, .7] and stats["threshold"] == .7
    assert stats["threshold_oscillation"] and not stats["threshold_final_reassembled"]
    assert {(e["source"], e["target"]) for e in artifact.payload["secondary_edges"]} == {
        ("d", "e"), ("a", "e"), ("a", "c"), ("a", "f")}


def test_fixed_point_rule_does_not_reuse_old_one_shot_cache():
    store = fixture()
    old, _ = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    old.manifest["config"]["threshold_rule"] = "round-sum-isotonic-on-main-unpruned-directions-v1"
    old.manifest["config_hash"] = digest(old.manifest["config"])
    artifact, reused = BuildSecondaryMLEdges(store, Scorer(), Tokenize()).execute("doc")
    assert not reused and store.saved_versions == 2
    assert artifact.manifest["config"]["threshold_rule"] == "round-sum-isotonic-on-judged-directions-fixed-point-10-v1"


def test_threshold_iteration_limit_is_ten_not_early_convergence_or_unbounded(monkeypatch):
    # Force a long population transient at the selector seam; scoring, assembly,
    # evidence validation and persistence still run through execute.
    import doc2roadmap.application.use_cases.build_secondary_ml_edges as module

    specs = [(chr(97 + 2*i), chr(98 + 2*i), (i + 1)/12, 1.0) for i in range(12)]
    store, scorer = threshold_fixture(specs)
    select, rounds = module.select_secondary_pairs, []

    def shrinking_population(nodes, pairs, ledger, edges, *, route):
        if len(pairs) != 1:
            return select(nodes, pairs, ledger, edges, route=route)
        pair = pairs[0]
        excluded = min(len(rounds) + 1, 11)
        result = ([], [{"pair_id": pair["pair_id"], "status": "pruned_direct_edge"}]) if int(pair["pair_id"]) < excluded else ([pair], [])
        if pair["pair_id"] == "11":
            rounds.append(excluded)
        return result

    monkeypatch.setattr(module, "select_secondary_pairs", shrinking_population)
    artifact, _ = BuildSecondaryMLEdges(store, scorer, Tokenize()).execute("doc")
    stats = artifact.payload["stats"]
    assert stats["threshold_history"] == [(i + 1)/12 for i in range(10)]
    assert stats["threshold_iterations"] == 10 and not stats["threshold_oscillation"]
    assert stats["threshold"] == 10/12
    assert {(e["source"], e["target"]) for e in artifact.payload["secondary_edges"]} == {("u", "v"), ("w", "x")}
    assert len(artifact.payload["secondary_log"]) == 12 and len(artifact.payload["executor_log"]) == 2
    assert scorer.calls == 1 and store.saved_versions == 1
