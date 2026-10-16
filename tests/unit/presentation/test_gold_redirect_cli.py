import importlib
from pathlib import Path

import pytest


cli = importlib.import_module("doc2roadmap.presentation.cli.main")


@pytest.mark.parametrize("command", ["a8-score", "a8-roadmap-score"])
def test_gold_redirect_cli_forwards_opt_in_only(monkeypatch, command):
    store, calls = object(), []
    monkeypatch.setattr(cli, "build_artifact_store", lambda: store)

    def score(*args, **kwargs):
        calls.append((args, kwargs))
        return {"e2": {"subsets": []}}

    monkeypatch.setattr(cli.a8_score, "score_from_store", score)
    monkeypatch.setattr(cli.a8_score, "score_roadmap_order", score)
    args = [command, "--graph", "graph.json", "--gold", "gold.json"]
    if command == "a8-score":
        args += ["--doc-id", "book"]
    assert cli.main(args) == 0
    assert "remap_gold_ids" not in calls[-1][1]
    assert cli.main([*args, "--remap-gold-ids"]) == 0
    assert calls[-1][1]["remap_gold_ids"] is True
    if command == "a8-roadmap-score":
        assert calls[-1][1]["store"] is store


def test_gold_source_graph_requires_remapping_and_reaches_scorer(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(cli, "build_artifact_store", object)
    monkeypatch.setattr(cli.a8_score, "score_from_store",
                        lambda *args, **kwargs: calls.append(kwargs) or {"e2": {"subsets": []}})
    args = ["a8-score", "--doc-id", "book", "--graph", "graph.json", "--gold", "gold.json",
            "--gold-graph", "source.json"]
    assert cli.main(args) == 2
    assert "--gold-graph cần --remap-gold-ids" in capsys.readouterr().err
    assert calls == []
    assert cli.main([*args, "--remap-gold-ids"]) == 0
    assert calls[0]["gold_graph_path"] == Path("source.json")
