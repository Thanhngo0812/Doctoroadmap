import pytest

from doc2roadmap.application.planning import StagePlan
from doc2roadmap.application.spend_guard import SpendNotAllowed
from doc2roadmap.config import Settings
from doc2roadmap.presentation.cli.main import main


@pytest.mark.parametrize("mode", ["--names-only", "--prepare"])
def test_gop_cli_rejects_incomplete_modes_before_any_work(monkeypatch, capsys, mode):
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_artifact_store",
                        lambda: pytest.fail("must reject before reading store"))
    args = ["a4", "--doc-id", "book", mode, "--upstream-chain", "gop"]
    assert main(args) == 2
    assert "A4/A5 đầy đủ" in capsys.readouterr().err


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
    assert main(["a4", "--doc-id", "book", "--gold", "gold.json", "--upstream-chain", "gop",
                 "--anchor-batch-mode", "single", "--allow-spend", "--dry-run"]) == 0
    assert options == [{"upstream_chain": "gop", "anchor_batch_mode": "single",
                        "allow_spend": False, "dry_run": True}]
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
    use_case = build_canonical(upstream_chain="gop")
    with pytest.raises(SpendNotAllowed):
        use_case.embedding.embed(["name"])
    for model in (use_case.reasoning.judge, use_case.reasoning.writer, use_case.anchor_model):
        with pytest.raises(SpendNotAllowed):
            model.start_session("prompt")
    assert attempts == []
    allowed = build_canonical(upstream_chain="gop", allow_spend=True)
    allowed.embedding.embed(["name"])
    allowed.reasoning.judge.start_session("prompt")
    allowed.reasoning.writer.start_session("prompt")
    allowed.anchor_model.start_session("prompt")
    assert attempts == ["embedding", "model", "model", "model"]


def test_chain_and_anchor_settings_are_explicit(monkeypatch):
    from pydantic import ValidationError
    monkeypatch.setenv("DOC2ROADMAP_UPSTREAM_CHAIN", "gop")
    monkeypatch.setenv("DOC2ROADMAP_ANCHOR_BATCH_MODE", "single")
    assert Settings(_env_file=None).upstream_chain == "gop"
    assert Settings(_env_file=None).anchor_batch_mode == "single"
    monkeypatch.setenv("DOC2ROADMAP_UPSTREAM_CHAIN", "wrong")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
