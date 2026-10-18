from datetime import datetime, timezone
from datetime import timedelta
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def graph():
    return LearningGraph({
        "doc_id": "book", "nodes": [
            {"node_id": "a", "name": "A", "display_name": "Khái niệm A", "learnable": True, "module_id": "m1"},
            {"node_id": "b", "name": "B", "display_name": "Khái niệm B", "learnable": True, "module_id": "m2"},
        ],
        "modules": [
            {"module_id": "m1", "index": 0, "title": "Phần A", "node_ids": ["a"]},
            {"module_id": "m2", "index": 1, "title": "Phần B", "node_ids": ["b"]},
        ], "requires_edges": [],
    }, [NS(chunk_id="c1", text="A", page=1, char_start=0, char_end=1, section_path=[], order_index=0)])


class Clock:
    def __init__(self):
        self.tick = 0

    def now(self):
        value = datetime(2026, 10, 18, tzinfo=timezone.utc) + timedelta(seconds=self.tick)
        self.tick += 1
        return value


def test_session_persists_full_turns_and_scopes_owner_and_delete():
    store, g = InMemoryPhaseBStore(), graph()
    sessions = SessionUseCase(store, g, clock=Clock())
    created = sessions.create_session("alice", "book", {"kind": "module", "node_ids": ["a"],
                                                           "module_id_at_creation": "m1",
                                                           "graph_version_at_creation": 1})
    sid = created["session_id"]
    assert created["scope"]["node_ids"] == ["a"]
    assert sessions.get("bob", sid) is None
    for n in range(5):
        sessions.append_turn("alice", sid, f"q{n}", {
            "contract_version": "answer-2", "answer_id": f"a{n}", "answer": f"answer {n}"
        }, client_turn_id=f"client-{n}", linked_node_ids=["a"])
        if n == 0:
            assert sessions.get("alice", sid)["title"] == "Khái niệm A"
            assert sessions.get("alice", sid)["title_source"] == "rule"
    turns = sessions.list_turns("alice", sid)
    assert len(turns) == 5
    assert turns[0]["question"] == "q0" and turns[-1]["answer"]["answer"] == "answer 4"
    assert turns[-1]["created_at"].endswith("+00:00")
    with pytest.raises(KeyError):
        sessions.list_turns("bob", sid)
    assert sessions.list_sessions("alice", "book", "module:m1")[0]["session_id"] == sid
    assert sessions.list_sessions("bob", "book", "all") == []
    sessions.rename_session("alice", sid, "Tên của tôi")
    sessions.append_turn("alice", sid, "q6", {"contract_version": "answer-2"}, linked_node_ids=["a"])
    assert sessions.get("alice", sid)["title"] == "Tên của tôi"
    assert sessions.get("alice", sid)["title_source"] == "learner"
    sessions.delete_session("alice", sid)
    assert sessions.get("alice", sid) is None
    assert sessions.list_turns("alice", sid) == []


def test_roadmap_page_is_all_roadmap_and_five_recent_module_sessions():
    store, g = InMemoryPhaseBStore(), graph()
    sessions = SessionUseCase(store, g, clock=Clock())
    roadmap = sessions.create_session("alice", "book", {"kind": "roadmap"})
    ids = []
    for i in range(7):
        item = sessions.create_session("alice", "book", {"kind": "module", "node_ids": ["a"],
                                                             "module_id_at_creation": "m1",
                                                             "graph_version_at_creation": 1})
        ids.append(item["session_id"])
    page = sessions.list_sessions("alice", "book", "roadmap_page")
    assert {row["session_id"] for row in page} == {roadmap["session_id"], *ids[-5:]}
    assert [row["session_id"] for row in page if row["scope"]["kind"] == "module"] == ids[-5:][::-1]


def test_session_owner_cannot_rename_or_delete_another_users_record():
    sessions = SessionUseCase(InMemoryPhaseBStore(), graph(), clock=Clock())
    sid = sessions.create_session("alice", "book", {"kind": "roadmap"})["session_id"]
    with pytest.raises(KeyError):
        sessions.rename_session("bob", sid, "stolen")
    with pytest.raises(KeyError):
        sessions.delete_session("bob", sid)
    assert sessions.get("alice", sid)["title_source"] == "rule"


def test_old_module_session_is_stale_on_roadmap_and_not_module_filter():
    old_graph = graph()
    old_graph.graph_version = 1
    store = InMemoryPhaseBStore()
    old_sessions = SessionUseCase(store, old_graph, clock=Clock())
    sid = old_sessions.create_session("alice", "book", {"kind": "module", "node_ids": ["a"],
        "module_id_at_creation": "m1", "graph_version_at_creation": 1})["session_id"]

    current = graph()
    current.graph_version = 2
    current.modules = {"m2": {"module_id": "m2", "index": 0, "title": "Phần B", "node_ids": ["b"]}}
    sessions = SessionUseCase(store, current, clock=Clock())
    assert sessions.list_sessions("alice", "book", "module:m2") == []
    page = sessions.list_sessions("alice", "book", "roadmap_page")
    assert len(page) == 1 and page[0]["session_id"] == sid
    assert page[0]["scope_note"] == "module này đã đổi"
    assert page[0]["scope"]["module_id_at_creation"] == "m1"
