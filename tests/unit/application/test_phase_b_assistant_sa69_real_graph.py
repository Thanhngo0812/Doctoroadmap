"""SA-69: the two real cases of the 2026-10-24 live run, replayed on the real graphs (read only, 0 USD).

The scripted model sends exactly the arguments the real model sent. Skipped when the artifacts are absent.
"""
import os
from functools import partial
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.scope import module_scope
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

ARTIFACTS = Path(os.environ.get("SA66_REAL_ARTIFACTS", Path(__file__).resolve().parents[3] / "artifacts"))
pytestmark = pytest.mark.skipif(not (ARTIFACTS / "graph" / "nhap-mon-ml").exists()
                                or not (ARTIFACTS / "graph" / "doc-6").exists(), reason="no real artifacts here")


class Scripted:
    model_id = "gemini-3.1-flash-lite"

    def __init__(self, call):
        self.turns = iter([[ToolCall(*call, "1"), Done({})], [Delta("Xong."), Done({})]])

    def start_session(self, prompt, tools):
        return self

    def stream(self, messages, *, mode):
        yield from next(self.turns)


class DocModel:
    model_id = "fake-doc"

    def ask_json(self, prompt, *, response_schema):
        return NS(payload={"title": "Tài liệu thử", "markdown": "Nội dung. [S1]", "citations": [],
                           "outside_document_blocks": []}, usage={})


def replay(doc_id, version, module_no, tool, args):
    store = InMemoryPhaseBStore()
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ARTIFACTS, _env_file=None), mode="offline", store=store)
    graph = runtime.graph(doc_id, version)
    module_id = next(mid for mid, module in graph.modules.items() if (module.get("index", 0) or 0) + 1 == module_no)
    session = runtime.sessions(graph).create_session("alice", doc_id, module_scope(graph, module_id))
    made = []

    def make_quiz(scope, n=None, level=None, *, owner, **kwargs):
        made.append(runtime.quiz(graph).make_quiz(
            graph.doc_id, None, owner, n=n, scope=scope, level=level, origin="assistant", allow_spend=True,
            home_scope=kwargs.get("home_scope"), session_id=kwargs.get("session_id")))
        return made[-1]

    def make_document(request, scope, *, owner, **kwargs):
        made.append(DocumentUseCase(DocModel(), store, settings=runtime.b_settings).create(
            graph.doc_id, graph.graph_version, graph, request, scope, owner=owner, origin="assistant",
            allow_spend=True, home_scope=kwargs.get("home_scope"), session_id=kwargs.get("session_id")))
        return made[-1]
    use_case = AssistantUseCase(graph, store, Scripted((tool, args)), search=partial(runtime.search, graph),
                                concept_lookup=partial(runtime.lookup, graph), quiz=make_quiz, document=make_document,
                                settings=runtime.b_settings, progress=runtime.progress(graph))
    result = use_case.ask(doc_id, graph.graph_version, session["session_id"], "Tạo giúp mình", owner="alice",
                          allow_spend=True)
    return graph, module_id, made, result["tool_calls"][0]["result_summary"]


def test_nhap_mon_ml_v50_module_4_quiz_of_three_questions():
    graph, module_id, made, summary = replay("nhap-mon-ml", 50, 4, "make_quiz", {"n": 3, "scope": ["module 4"]})
    quiz = made[0]
    assert "error" not in summary and quiz["status"] == "ready"
    assert quiz["module_id"] == module_id and 1 <= len(quiz["items"]) <= 3
    assert set(quiz["node_ids"]) <= set(graph.modules[module_id]["node_ids"])
    assert summary["artifact"] == {"kind": "quiz", "id": quiz["attempt_id"]}


def test_doc_6_v29_module_1_document_is_made_for_that_module():
    graph, module_id, made, summary = replay(
        "doc-6", 29, 1, "make_document",
        {"request": "Tóm tắt module này", "scope": ["module 1: Giảm trùng lắp thông tin"]})
    document = made[0]
    assert document["scope"]["module_ids"] == [module_id]
    assert document["scope"]["node_ids"] == graph.modules[module_id]["node_ids"]
    assert summary.get("error", {}).get("code") != "tool_error"
