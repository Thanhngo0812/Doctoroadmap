"""SA-66: the context fetched before the first model call, on the real graphs (read only, BM25, 0 USD).

Skipped when the artifacts are absent. The model is scripted; only the message it receives is examined.
"""
import os
import re
from functools import partial
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

ARTIFACTS = Path(os.environ.get("SA66_REAL_ARTIFACTS", Path(__file__).resolve().parents[3] / "artifacts"))
pytestmark = pytest.mark.skipif(not (ARTIFACTS / "graph" / "doc-1").exists(), reason="no real artifacts here")


class Scripted:
    model_id = "gemini-3.1-flash-lite"

    def __init__(self):
        self.calls = []

    def start_session(self, prompt, tools):
        return self

    def stream(self, messages, *, mode):
        self.calls.append(list(messages))
        yield Delta("Trả lời thử. [S1]")
        yield Done({})


def first_message(doc_id, version, question):
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ARTIFACTS, _env_file=None), mode="offline",
                            store=InMemoryPhaseBStore())
    graph = runtime.graph(doc_id, version)
    session = runtime.sessions(graph).create_session("alice", doc_id, {"kind": "roadmap"})
    model = Scripted()
    use_case = AssistantUseCase(graph, runtime.store, model, search=partial(runtime.search, graph),
                                concept_lookup=partial(runtime.lookup, graph), page_images=runtime.page_images,
                                progress=runtime.progress(graph), settings=runtime.b_settings)
    result = use_case.ask(doc_id, graph.graph_version, session["session_id"], question, owner="alice", allow_spend=True)
    return model.calls[0][0], result, graph


def test_eigenvalue_prerequisite_question_gets_a_roadmap_in_app_module_numbers():
    message, result, graph = first_message(
        "doc-1", 8, "Muốn học trị riêng và véctơ riêng thì mình cần học những gì trước?")
    text = message["text"]
    assert len(result["tool_calls"]) == 0 and result["status"] == "answered"
    concept = next(line for line in text.splitlines() if line.startswith("Khái niệm liên quan:"))
    assert "lộ trình: module 1:" in concept and re.search(r"module \d+: [^;]+; module \d+:", concept)
    assert "tiên quyết: Trị riêng (module 33, chưa học)" in concept
    # the path is cut to 12 modules by the graph; the context still says where it ends
    assert "đích là module 33: Trị riêng và Véctơ riêng" in concept
    # the passage that defines the concept travels with the question and its page is stated
    assert re.search(r"\[S\d+\] \(trang 87,", text) and "véctơ x được gọi là véctơ riêng ứng với trị riêng" in text
    assert text.rstrip().endswith("Câu hỏi của người học: Muốn học trị riêng và véctơ riêng thì mình cần học những gì trước?")


def test_pair_sample_question_gets_the_passage_that_defines_joint_frequency():
    message, result, _ = first_message(
        "xstk-ch3-1", 68, "Trong bảng mẫu hai chiều, đại lượng tần số đồng thời có ý nghĩa là gì?")
    text = message["text"]
    assert len(result["tool_calls"]) == 0
    assert "Khái niệm liên quan: Tần số đồng thời (module 4: Mẫu hai chiều và tương quan cặp)" in text
    assert "lộ trình: module 1: Khái niệm tổng thể và mẫu" in text
    passage = text.split("Tư liệu từ sách:")[1]
    assert "nij là tần số đồng thời của xi và yj trong mẫu" in passage
    assert re.search(r"\[S\d+\] \(trang 10, mục .*Mẫu hai chiều\)", passage)
