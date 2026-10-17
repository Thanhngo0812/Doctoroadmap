import pytest

from doc2roadmap.application.planning import StagePlan
from doc2roadmap.application.spend_guard import SpendNotAllowed
from doc2roadmap.config import Settings
from doc2roadmap.presentation.cli.main import main


def test_gop_cli_dry_run_lists_phases_and_never_executes(monkeypatch, capsys):
    options = []
    class UseCase:
        def plan(self, doc, **kwargs):
            assert doc == "book"
            return {"anchor": StagePlan("unknown", calls_estimate=None, usd_estimate=None)}
        def execute(self, *args, **kwargs):
            pytest.fail("dry-run executed canonical")
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_artifact_store", lambda: object())
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.load_gold", lambda *a, **k: {"documents": {"book": {}}})
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_canonical",
                        lambda **kwargs: options.append(kwargs) or UseCase())
    assert main(["a4", "--doc-id", "book", "--gold", "gold.json", "--allow-spend", "--dry-run"]) == 0
    assert options == [{"allow_spend": False, "dry_run": True}]
    output = capsys.readouterr().out
    assert '"anchor"' in output and "chưa biết" in output


def test_gop_composition_blocks_embedding_and_every_model_before_first_call(monkeypatch):
    from doc2roadmap.composition import build_canonical
    attempts = []
    class Embedding:
        limiter = None
        embedding_model_id = "fake:768"
        def embed(self, requests):
            attempts.append("embedding")
    class Model:
        model_id = "fake"
        def __init__(self, *args, **kwargs):
            pass
        def start_session(self, prompt):
            attempts.append("model")
    settings = Settings(_env_file=None)
    monkeypatch.setattr("doc2roadmap.composition._a3_dependencies", lambda: (settings, object(), Embedding()))
    monkeypatch.setattr("doc2roadmap.composition.GeminiEntityExtractor", Model)
    monkeypatch.setattr("doc2roadmap.composition.SentencePieceTokenCounter", lambda *a: None)
    use_case = build_canonical()
    with pytest.raises(SpendNotAllowed):
        use_case.embedding.embed(["name"])
    for model in (use_case.reasoning.judge, use_case.reasoning.writer, use_case.anchor_model):
        with pytest.raises(SpendNotAllowed):
            model.start_session("prompt")
    assert attempts == []
    allowed = build_canonical(allow_spend=True)
    allowed.embedding.embed(["name"])
    allowed.reasoning.judge.start_session("prompt")
    allowed.reasoning.writer.start_session("prompt")
    allowed.anchor_model.start_session("prompt")
    assert attempts == ["embedding", "model", "model", "model"]
