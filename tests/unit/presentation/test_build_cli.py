import json
from types import SimpleNamespace

from doc2roadmap.presentation.cli.main import _parser, main


def test_build_command_emits_result_and_passes_options(monkeypatch, capsys):
    called = {}

    class Runner:
        def execute(self, path, doc_id, **kwargs):
            called.update(path=path, doc_id=doc_id, **kwargs)
            return SimpleNamespace(to_dict=lambda: {"doc_id": doc_id, "status": "succeeded"})

    import doc2roadmap.presentation.cli.build as build_cli
    monkeypatch.setattr(build_cli, "build_document_runner", lambda **kwargs: Runner())
    assert main(["build", "--file", "book.pdf", "--doc-id", "book", "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out) == {"doc_id": "book", "status": "succeeded"}
    assert called["doc_id"] == "book"
    assert called["language"] == "vi"
    assert called["dry_run"] is True


def test_build_command_fails_non_success(monkeypatch, capsys):
    class Runner:
        def execute(self, *args, **kwargs):
            return SimpleNamespace(to_dict=lambda: {"status": "rejected"})

    import doc2roadmap.presentation.cli.build as build_cli
    monkeypatch.setattr(build_cli, "build_document_runner", lambda **kwargs: Runner())
    assert main(["build", "--file", "book.pdf", "--doc-id", "book"]) != 0
    assert json.loads(capsys.readouterr().out)["status"] == "rejected"


def test_build_parser_requires_explicit_file_and_id():
    try:
        _parser().parse_args(["build"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("build must require --file and --doc-id")


def test_build_parser_does_not_expose_language_override():
    try:
        _parser().parse_args(["build", "--file", "book.pdf", "--doc-id", "book", "--language", "en"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("build language is fixed to Vietnamese")
