import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.config import Settings
from tests.unit.application.test_a4_pipeline import embedding, fixture_store
from tests.unit.application.test_canonical_gop import AnchorModel, DOC


def test_default_gop_uses_individual_anchor_calls(tmp_path, monkeypatch):
    monkeypatch.delenv("DOC2ROADMAP_ANCHOR_BATCH_MODE", raising=False)
    assert Settings(_env_file=None).anchor_batch_mode == "single"
    model = AnchorModel()
    result, _ = Canonicalize(fixture_store(tmp_path), embedding(), reasoning=CanonicalReasoning(model, model),
                             upstream_chain="gop").execute(DOC)
    assert result.manifest["config"]["anchor_batch_mode"] == "single"
    assert model.anchor_calls and not result.payload["stats"].get("anchor_in_a5_calls", 0)
    assert all("anchor_candidates" not in call for call in model.calls)


@pytest.mark.parametrize("mode", ["--names-only", "--prepare"])
@pytest.mark.parametrize("explicit", [None, "v3", "gop"])
def test_incomplete_cli_uses_v3_under_gop_default(tmp_path, monkeypatch, capsys, mode, explicit):
    from doc2roadmap.presentation.cli import main as cli
    from doc2roadmap.composition import build_canonical

    monkeypatch.setenv("DOC2ROADMAP_UPSTREAM_CHAIN", "gop")
    store, embed = fixture_store(tmp_path), embedding()
    monkeypatch.setattr(cli, "build_artifact_store", lambda: store)
    monkeypatch.setattr("doc2roadmap.composition._a3_dependencies",
                        lambda: (Settings(_env_file=None), store, embed))
    monkeypatch.setattr(cli, "build_canonical", build_canonical)
    args = ["a4", "--doc-id", DOC, mode]
    if explicit:
        args += ["--upstream-chain", explicit]
    if explicit == "gop":
        assert cli.main(args) == 2
        assert "A4/A5 đầy đủ" in capsys.readouterr().err
        with pytest.raises(FileNotFoundError):
            store.load_latest_canonical(DOC)
    else:
        assert cli.main(args) == 0
        result = store.load_latest_canonical(DOC)
        assert "upstream_chain" not in result.manifest["config"]
        assert "canonical_has_anchors" not in result.payload
        assert result.payload["stage"] == ("names" if mode == "--names-only" else "nominations")


def test_default_chain_is_gop_after_gate_19m(monkeypatch):
    monkeypatch.delenv("DOC2ROADMAP_UPSTREAM_CHAIN", raising=False)
    assert Settings(_env_file=None).upstream_chain == "gop"


@pytest.mark.parametrize("explicit", [None, "v3"])
def test_default_a4_changes_next_roadmap_chain_on_an_old_document(tmp_path, monkeypatch, capsys, explicit):
    import json
    from doc2roadmap import composition
    from doc2roadmap.presentation.cli import main as cli
    from tests.unit.application.test_gop_graph import GOP_STAGES, V3_STAGES, pipeline

    monkeypatch.delenv("DOC2ROADMAP_UPSTREAM_CHAIN", raising=False)
    settings = Settings(_env_file=None)
    store, embed, model = fixture_store(tmp_path), embedding(), AnchorModel()
    embed.limiter = None
    old, _ = Canonicalize(store).execute(DOC)
    monkeypatch.chdir(tmp_path)  # No local .env can supply a chain override.
    monkeypatch.setattr(cli, "build_artifact_store", lambda: store)
    monkeypatch.setattr(composition, "_a3_dependencies", lambda: (settings, store, embed))
    monkeypatch.setattr(composition, "GeminiEntityExtractor", lambda *args, **kwargs: model)
    monkeypatch.setattr(composition, "SentencePieceTokenCounter", lambda *args: None)
    monkeypatch.setattr(cli, "build_canonical", composition.build_canonical)
    monkeypatch.setattr(cli, "load_gold", lambda *args, **kwargs: {"documents": {DOC: {}}})

    def build_graph(**kwargs):
        assert kwargs == {"allow_spend": False, "identity_review": None}
        graph, _ = pipeline()
        graph.clusters.store = store
        return graph, settings

    monkeypatch.setattr(cli, "build_learning_graph", build_graph)
    roadmap = ["roadmap", "--doc-id", DOC, "--dry-run"]
    assert cli.main(roadmap) == 0
    assert [row["stage"] for row in json.loads(capsys.readouterr().out)["stages"]] == V3_STAGES
    args = ["a4", "--doc-id", DOC, "--gold", "gold.json", "--allow-spend"]
    if explicit:
        args += ["--upstream-chain", explicit]
    assert cli.main(args) == 0
    capsys.readouterr()
    current = store.load_latest_canonical(DOC)
    chain = current.manifest["config"].get("upstream_chain", "v3")
    assert chain == (explicit or "gop")
    assert current.version > old.version
    assert bool(current.payload.get("canonical_has_anchors")) is (explicit is None)
    assert cli.main(roadmap) == 0
    stages = [row["stage"] for row in json.loads(capsys.readouterr().out)["stages"]]
    assert stages == (V3_STAGES if explicit else GOP_STAGES)
