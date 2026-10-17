import importlib
import json


cli = importlib.import_module("doc2roadmap.presentation.cli.main")


def test_merge_review_rejects_other_document_before_building_paid_models(tmp_path, monkeypatch, capsys):
    review = tmp_path / "review.json"
    review.write_text(json.dumps({"doc_id": "other", "decisions": []}), encoding="utf-8")
    monkeypatch.setattr(cli, "build_artifact_store", object)
    monkeypatch.setattr(cli, "build_canonical", lambda **kwargs: (_ for _ in ()).throw(AssertionError("paid build")))
    assert cli.main(["a4", "--doc-id", "book", "--merge-review", str(review)]) == 2
    assert "không phải 'book'" in capsys.readouterr().err
