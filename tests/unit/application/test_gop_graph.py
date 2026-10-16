"""Gop graph orchestration, A8 contract and real extraction fixture coverage."""
from types import SimpleNamespace
import hashlib
import json

import pytest

from doc2roadmap.application.planning import StagePlan
from doc2roadmap.application.use_cases.build_learning_graph import BuildLearningGraph
from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges
from tests.unit.application.test_build_main_edges import Model, Store as MainStore


GOP_STAGES = ["clusters", "mentions", "main_edges", "secondary_edges", "validated",
              "concept_labels", "stages", "module_titles"]
V3_STAGES = ["clusters", "mentions", "provenance", "teaching", "identity", *GOP_STAGES[2:]]


def pipeline(*, canonical_chain="gop", upstream_chain=None, identity_review=None, missing=None):
    visited, returned = [], []

    class Stage:
        def __init__(self, name):
            self.name = name

        def execute(self, doc_id, *, upstream=None):
            if returned:
                assert upstream is returned[-1]
            visited.append(self.name)
            artifact = SimpleNamespace(payload={"stage": self.name}, version=len(visited))
            returned.append(artifact)
            return artifact, True

        def plan(self, doc_id, *, upstream=None):
            if returned:
                assert upstream is returned[-1]
            visited.append(self.name)
            if self.name == missing:
                return StagePlan("run", remaining_items=1, calls_estimate=0, usd_estimate=0)
            artifact = SimpleNamespace(payload={"stage": self.name}, version=len(visited))
            returned.append(artifact)
            return StagePlan("reused", artifact=artifact)

    clusters = Stage("clusters")
    clusters.store = SimpleNamespace(load_latest_canonical=lambda doc_id: SimpleNamespace(
        payload={"upstream_chain": canonical_chain}, manifest={"config": {"upstream_chain": canonical_chain}}))
    graph = BuildLearningGraph(clusters, Stage("mentions"), Stage("provenance"), Stage("main_edges"),
                               Stage("secondary_edges"), Stage("validated"), Stage("teaching"), Stage("identity"),
                               Stage("stages"), module_titles=Stage("module_titles"),
                               concept_labels=Stage("concept_labels"), upstream_chain=upstream_chain,
                               identity_review=identity_review)
    return graph, visited


@pytest.mark.parametrize("canonical_chain,expected", [("gop", GOP_STAGES), ("v3", V3_STAGES)])
def test_roadmap_infers_canonical_chain_and_passes_exact_artifacts(canonical_chain, expected):
    graph, visited = pipeline(canonical_chain=canonical_chain)
    _, reused = graph.execute("doc")
    assert visited == expected and reused


@pytest.mark.parametrize("stop_after,last", [("clusters", "clusters"), ("mentions", "mentions"),
                                            ("edges", "secondary_edges"), ("stages", "module_titles")])
def test_gop_stops_at_every_public_stage(stop_after, last):
    graph, visited = pipeline()
    graph.execute("doc", stop_after=stop_after)
    assert visited == GOP_STAGES[:GOP_STAGES.index(last) + 1]


@pytest.mark.parametrize("stop_after", ["provenance", "teaching", "identity"])
@pytest.mark.parametrize("operation", ["execute", "plan"])
def test_gop_rejects_stages_already_in_canonical_before_any_calls(stop_after, operation):
    graph, visited = pipeline()
    with pytest.raises(ValueError, match="đã nằm trong stage canonical"):
        getattr(graph, operation)("doc", stop_after=stop_after)
    assert visited == []


@pytest.mark.parametrize("canonical_chain,option", [("gop", "v3"), ("v3", "gop")])
@pytest.mark.parametrize("operation", ["execute", "plan"])
def test_explicit_chain_mismatch_is_rejected_before_any_calls(canonical_chain, option, operation):
    graph, visited = pipeline(canonical_chain=canonical_chain, upstream_chain=option)
    with pytest.raises(ValueError, match="canonical"):
        getattr(graph, operation)("doc")
    assert visited == []


@pytest.mark.parametrize("operation", ["execute", "plan"])
def test_gop_rejects_identity_review_before_any_calls(operation):
    graph, visited = pipeline(identity_review="review.json")
    with pytest.raises(ValueError, match="A4"):
        getattr(graph, operation)("doc")
    assert visited == []


def test_gop_dry_run_lists_only_gop_stages_and_unknowns_without_running_later_stages():
    graph, visited = pipeline(missing="mentions")
    report = graph.plan("doc")
    assert [row["stage"] for row in report["stages"]] == GOP_STAGES
    assert visited == ["clusters", "mentions"]
    assert [row["status"] for row in report["stages"]] == ["reused", "run"] + ["unknown"] * 6


def test_mixed_graph_and_canonical_chains_are_refused_and_v3_metadata_stays_empty():
    from doc2roadmap.application.graph_chain import graph_chain_fields

    old = SimpleNamespace(payload={}, manifest={})
    current = SimpleNamespace(payload={"upstream_chain": "gop"}, manifest={})
    assert graph_chain_fields(old) == {}
    with pytest.raises(ValueError, match="không khớp canonical"):
        graph_chain_fields(current, old)


def test_clusters_carry_pinned_canonical_anchors_and_keep_v3_cache_keys_unchanged():
    from doc2roadmap.application.use_cases.build_clusters import BuildClusters
    from tests.unit.application.test_build_clusters import Store, Embedding

    store = Store()
    old, _ = BuildClusters(store, Embedding()).execute("doc")
    assert not {"upstream_chain", "canonical_has_anchors"} & set(old.manifest["config"])
    store.canonical.payload.update(upstream_chain="gop", canonical_has_anchors=True)
    current, reused = BuildClusters(store, Embedding()).execute("doc")
    assert not reused and current.manifest["config_hash"] != old.manifest["config_hash"]
    assert current.payload["upstream_chain"] == "gop"
    assert current.payload["canonical_version"] == store.canonical.version
    assert current.payload["canonical_has_anchors"] is True


@pytest.mark.parametrize("chain,stage,declared,edge_count", [
    ("gop", "mentions", True, 0),
    ("gop", "mentions", False, 1),
    ("v3", "identity", False, 0),
    ("v3", "provenance", False, 1),
])
def test_main_contract_follows_pinned_canonical_declaration_and_preserves_v3(chain, stage, declared, edge_count):
    store, model = MainStore(), Model()
    store.mentions.payload.update(stage=stage, upstream_chain=chain, canonical_has_anchors=True)
    store.mentions.manifest["config"] = {"canonical_version": 1, "upstream_chain": chain}
    store.canonical.payload["upstream_chain"] = chain
    store.canonical.manifest["config"] = {"upstream_chain": chain}
    if declared:
        store.canonical.payload["canonical_has_anchors"] = True
    store.load_canonical = lambda doc_id, version: store.canonical if version == 1 else pytest.fail("canonical pin")
    store.load_latest_canonical = lambda *_: pytest.fail("must use pinned canonical")
    artifact, _ = BuildMainEdges(store, model).execute("doc", upstream=store.mentions)
    # Model omits prerequisite_kind: it is rejected only when the actual contract is enabled.
    assert len(artifact.payload["main_edges"]) == edge_count
    assert artifact.payload["definition_contract"] is (edge_count == 0)
    if chain == "gop":
        assert artifact.manifest["config"]["upstream_chain"] == "gop"
        assert artifact.manifest["config"]["canonical_version"] == 1


@pytest.mark.parametrize("secondary_mode", ["ml", "llm"])
def test_real_fixture_canonical_gop_runs_through_roadmap_and_scorers_without_identity_map(tmp_path, secondary_mode):
    from doc2roadmap.application.use_cases.name_modules import NameModules
    from doc2roadmap.application.use_cases.a8_gold import annotation_scope, list_chapters
    from doc2roadmap.application.use_cases.a8_score import score_from_store, score_roadmap_order
    from doc2roadmap.application.use_cases.build_clusters import BuildClusters
    from doc2roadmap.application.use_cases.build_mentions import BuildMentions
    from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
    from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges
    from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges
    from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
    from doc2roadmap.application.use_cases.validate_graph import ValidateGraph
    from tests.unit.application.test_canonical_gop import DOC, gop
    from tests.unit.application.test_build_secondary_ml_edges import Scorer, Tokenize

    store, _, canonical_use_case = gop(tmp_path)
    canonical, _ = canonical_use_case.execute(DOC)
    chunks = store.load_chunks(DOC, store.load_latest_candidates(DOC).manifest["upstream_version"])

    class Embedding:
        identifier = embedding_model_id = "e2e-fake"

        def __init__(self):
            self.calls = 0

        def embed(self, requests):
            self.calls += 1
            return [[1.0, hashlib.sha256(item.text.encode()).digest()[0] / 256, .5] for item in requests]

    class GraphModel:
        model_id = "fixture-model"

        def __init__(self):
            self.calls = []

        def start_session(self, system_prompt):
            return self

        def ask_json(self, prompt, *, response_schema):
            data = json.loads(prompt.split("\nCorrect this validation error:")[0])
            self.calls.append(data)
            if "dossier" in data:
                return SimpleNamespace(payload={"pair_id": data["dossier"]["pair_id"],
                                                "decision": "no_direct_relation", "flags": []})
            if "label" in data:
                return SimpleNamespace(payload={"node_id": data["node_id"], "display_name": data["label"]})
            if "concept_names" in data:
                return SimpleNamespace(payload={"suffix": " · ".join(data["concept_names"][:2])})
            return SimpleNamespace(payload={"edges": [], "flags": []})

    embed, model, scorer = Embedding(), GraphModel(), Scorer(probability=0)
    store.save_retrieval(DOC, chunks.manifest["source_hash"], "e2e-retrieval", {}, {
        "documents": [{"chunk_id": c.chunk_id, "vector": [1.0, i / len(chunks.result.chunks), .5]}
                      for i, c in enumerate(chunks.result.chunks)]}, upstream_version=chunks.version,
        manifest_fields={"embedding_model_id": embed.embedding_model_id})
    secondary = (BuildSecondaryMLEdges(store, scorer, Tokenize()) if secondary_mode == "ml" else
                 BuildSecondaryEdges(store, model))
    forbidden = SimpleNamespace(execute=lambda *_args, **_kwargs: pytest.fail("old stage executed"),
                                plan=lambda *_args, **_kwargs: pytest.fail("old stage planned"))
    graph = BuildLearningGraph(BuildClusters(store, embed), BuildMentions(store, embed), forbidden,
                               BuildMainEdges(store, model), secondary, ValidateGraph(store), forbidden,
                               forbidden, BuildRoadmap(store), NameModules(store, model),
                               NameConceptLabels(store, model))
    # No artifacts exist yet: planning must stop making downstream plans once clusters is unknown.
    report = graph.plan(DOC)
    assert [row["stage"] for row in report["stages"]] == GOP_STAGES
    assert embed.calls == 0 and model.calls == [] and scorer.calls == 0
    artifact, _ = graph.execute(DOC)
    assert artifact.payload["stage"] == "stages" and artifact.payload["sequence"]
    assert "identity_map" not in artifact.payload
    assert (artifact.path / "roadmap.html").exists()
    original = {n["node_id"]: n for n in canonical.payload["nodes"]}
    taught = {key for key, n in original.items() if n.get("learnable") and n.get("teaching_status") == "taught"}
    assert taught and taught <= set(artifact.payload["sequence"])
    for value in artifact.payload["nodes"]:
        for key in ("teaching_status", "anchor", "teaching_chunk_ids", "teaching_order_index", "teaching_conflict"):
            if key in original[value["node_id"]]:
                assert value[key] == original[value["node_id"]][key]
    manifests = [json.loads(path.read_text(encoding="utf-8"))
                 for path in (tmp_path / "graph" / DOC).glob("v*/manifest.json")]
    assert len(manifests) == 8
    assert not {"provenance", "teaching", "identity"} & {m["stage"] for m in manifests}
    for manifest in manifests:
        assert manifest["config"]["upstream_chain"] == "gop"
        assert manifest["config"]["canonical_version"] == canonical.version
        assert manifest["config"]["canonical_has_anchors"] is True
    if secondary_mode == "ml":
        assert scorer.calls == 1
    else:
        assert any("dossier" in call for call in model.calls)
    mentions = next(store.load_graph(DOC, m["version"]) for m in manifests if m["stage"] == "mentions")
    chapter = next(row["section_id"] for row in list_chapters(canonical.payload["nodes"],
        chunks.result.sections, chunks.result.chunks) if row["targets"])
    scope = annotation_scope(DOC, canonical.version, canonical.payload["nodes"], chunks.result.sections,
                             chunks.result.chunks, chapter=chapter, graph_payload=mentions.payload)
    gold = tmp_path / "gold.json"
    gold.write_text(json.dumps({"doc_id": DOC, "canonical_version": canonical.version, "chapter_level": 1,
        "chapter": scope["chapter"], "concept_hash": scope["concept_hash"], "targets": sorted(taught),
        "edges": []}), encoding="utf-8")
    assert score_from_store(store, DOC, mentions.path / "graph.json", [gold], samples=0)["gold"]["edges"] == 0
    assert score_roadmap_order(artifact.path / "graph.json", [gold])["gold_edge_count"] == 0
    count = embed.calls, len(model.calls), scorer.calls
    again, reused = graph.execute(DOC)
    assert reused and again.version == artifact.version and count == (embed.calls, len(model.calls), scorer.calls)


def test_roadmap_cli_passes_explicit_chain_and_dry_run_without_spend(monkeypatch, capsys):
    from doc2roadmap.presentation.cli import main as cli

    seen = []

    def build(**kwargs):
        seen.append(kwargs)
        graph, _ = pipeline()
        return graph, None

    monkeypatch.setattr(cli, "build_learning_graph", build)
    assert cli.main(["roadmap", "--doc-id", "doc", "--upstream-chain", "gop",
                     "--dry-run", "--allow-spend"]) == 0
    assert seen == [{"allow_spend": False, "identity_review": None, "upstream_chain": "gop"}]
    report = json.loads(capsys.readouterr().out)
    assert [row["stage"] for row in report["stages"]] == GOP_STAGES
