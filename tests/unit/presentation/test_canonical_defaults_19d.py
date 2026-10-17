import pytest

from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.config import Settings
from tests.unit.application.test_a4_pipeline import embedding, fixture_store
from tests.unit.application.test_canonical_gop import AnchorModel, DOC


def test_default_gop_uses_individual_anchor_calls(tmp_path):
    model = AnchorModel()
    result, _ = Canonicalize(fixture_store(tmp_path), embedding(), reasoning=CanonicalReasoning(model, model)).execute(DOC)
    assert model.anchor_calls and not result.payload['stats'].get('anchor_in_a5_calls', 0)
    assert all('anchor_candidates' not in call for call in model.calls)


@pytest.mark.parametrize('mode', ['--names-only', '--prepare'])
def test_names_only_and_prepare_keep_the_frozen_v3_path(tmp_path, monkeypatch, capsys, mode):
    from doc2roadmap import composition
    from doc2roadmap.presentation.cli import main as cli
    store, embed = fixture_store(tmp_path), embedding()
    monkeypatch.setattr(cli, 'build_artifact_store', lambda: store)
    monkeypatch.setattr(composition, '_a3_dependencies', lambda: (Settings(_env_file=None), store, embed))
    monkeypatch.setattr(cli, 'build_canonical', composition.build_canonical)
    assert cli.main(['a4', '--doc-id', DOC, mode]) == 0
    capsys.readouterr()
    result = store.load_latest_canonical(DOC)
    assert 'upstream_chain' not in result.manifest['config']
    assert 'canonical_has_anchors' not in result.payload
    assert result.payload['stage'] == ('names' if mode == '--names-only' else 'nominations')


def test_default_a4_changes_next_roadmap_chain_on_an_old_document(tmp_path, monkeypatch, capsys):
    import json
    from doc2roadmap import composition
    from doc2roadmap.presentation.cli import main as cli
    from tests.unit.application.test_gop_graph import GOP_STAGES, pipeline

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
        assert kwargs == {"allow_spend": False}
        graph, _ = pipeline()
        graph.clusters.store = store
        return graph, settings

    monkeypatch.setattr(cli, "build_learning_graph", build_graph)
    roadmap = ["roadmap", "--doc-id", DOC, "--dry-run"]
    assert cli.main(roadmap) == 2
    assert "canonical gop" in capsys.readouterr().err
    args = ["a4", "--doc-id", DOC, "--gold", "gold.json", "--allow-spend"]
    assert cli.main(args) == 0
    capsys.readouterr()
    current = store.load_latest_canonical(DOC)
    chain = current.manifest["config"].get("upstream_chain", "v3")
    assert chain == "gop"
    assert current.version > old.version
    assert bool(current.payload.get("canonical_has_anchors")) is True
    assert cli.main(roadmap) == 0
    stages = [row["stage"] for row in json.loads(capsys.readouterr().out)["stages"]]
    assert stages == GOP_STAGES
