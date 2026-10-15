import json
from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError

from doc2roadmap.composition import build_region_roles
from doc2roadmap.presentation.cli.main import main


def test_a2_retries_429_using_shared_policy(monkeypatch):
    monkeypatch.setenv("DOC2ROADMAP_LLM_TRANSPORT", "developer_api")
    monkeypatch.setenv("DOC2ROADMAP_GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("DOC2ROADMAP_GEMINI_MAX_RETRIES", "2")
    calls, waits = [], []

    class Response(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    def request(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise HTTPError("https://example.invalid", 429, "busy", {"Retry-After": "3"}, None)
        return Response(json.dumps({"candidates": [{"content": {"parts": [{"text": '{"labels": []}'}]}}]}).encode())

    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", request)
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.sleep", waits.append)
    model = build_region_roles(allow_spend=True).model
    reply = model.start_session("system").ask_json("roles", response_schema={"type": "object"})
    assert reply.payload == {"labels": []}
    assert len(calls) == 2
    assert waits and waits[0] >= 3


def test_a3_incomplete_exits_nonzero_and_names_failed_sections(monkeypatch, capsys):
    result = SimpleNamespace(doc_id="broken", stats={"metrics": {
        "learnable_entities": 0, "total_entities": 0, "learnable_per_1000_tokens": 0}},
        warnings=["coverage_incomplete: Chương 2"], failed_sections=["section-2"], coverage_incomplete=True)
    extraction = SimpleNamespace(execute=lambda *args, **kwargs: SimpleNamespace(
        result=result, reused=False, artifact_path=None))
    index = SimpleNamespace(execute=lambda *args: SimpleNamespace(payload={"documents": []}))
    settings = SimpleNamespace(extraction_concurrency=1)
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_a3", lambda **kwargs: (extraction, index, settings))
    assert main(["a3", "--doc-id", "broken"]) != 0
    output = capsys.readouterr()
    assert "section-2" in output.err
    assert "coverage_incomplete" in output.err
