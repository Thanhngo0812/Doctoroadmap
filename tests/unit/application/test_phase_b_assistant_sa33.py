from copy import deepcopy
from types import SimpleNamespace as NS

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def make_graph():
    chunks = [NS(chunk_id="c1", text="Ma trận là bảng các số.", page=1, char_start=0, char_end=23,
                 section_path=[], order_index=0, role="noi_dung"),
              NS(chunk_id="c2", text="Định thức dùng ma trận vuông.", page=2, char_start=24, char_end=53,
                 section_path=[], order_index=1, role="noi_dung")]
    payload = {"doc_id": "book", "nodes": [
        {"node_id": "a", "name": "Ma trận", "learnable": True, "module_id": "m1", "teaching_chunk_ids": ["c1"]},
        {"node_id": "b", "name": "Định thức", "learnable": True, "module_id": "m2", "teaching_chunk_ids": ["c2"]}],
        "modules": [{"module_id": "m1", "index": 0, "title": "Ma trận", "node_ids": ["a"]},
                    {"module_id": "m2", "index": 1, "title": "Định thức", "node_ids": ["b"]}],
        "requires_edges": [], "chunk_module_map": {"c1": {"module_id": "m1"}, "c2": {"module_id": "m2"}}}
    return LearningGraph(payload, chunks)


class Replay:
    model_id = "gemini-3.1-flash-lite"
    is_replay = True

    def start_session(self, prompt, tools):
        return self

    def stream(self, messages, *, mode):
        yield Delta("Định thức dùng ma trận vuông. [S1]")
        yield Done({})


def test_stale_module_full_ask_becomes_roadmap_and_shows_out_of_scope_module_card():
    graph = make_graph()
    store = InMemoryPhaseBStore()
    store.put_record("session", "s", {"contract_version": "session-1", "session_id": "s",
        "owner": "alice", "doc_id": "book", "scope": {"kind": "module", "node_ids": ["a"],
        "module_id_at_creation": "m1", "graph_version_at_creation": 1},
        "title": "Session", "title_source": "rule", "created_at": "2026-10-18T00:00:00+00:00",
        "updated_at": "2026-10-18T00:00:00+00:00", "turn_count": 0, "artifact_refs": [],
        "state": {"reminded_node_ids": [], "linked_node_ids": [], "reminders_enabled": True}})
    graph.payload["modules"] = [deepcopy(graph.payload["modules"][1])]
    result = AssistantUseCase(graph, store, Replay()).ask("book", 2, "s", "Định thức",
                                                           owner="alice", allow_spend=True)
    assert result["status"] == "answered"
    assert result["graph_cards"]["scope_note"] == "module này đã đổi"
    assert result["graph_cards"]["roadmap"][0]["title"] == "Định thức"
    assert result["graph_cards"]["module_cards"] == [{"node_id": "b", "module_id": "m2",
        "module_index": 2, "module_title": "Định thức", "label": "nằm ở module"}]
