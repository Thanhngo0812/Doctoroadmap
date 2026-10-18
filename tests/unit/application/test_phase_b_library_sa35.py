from types import SimpleNamespace as NS

from doc2roadmap.application.phase_b.library import LibraryUseCase
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.scope import module_scope
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def graph():
    result = LearningGraph({"doc_id": "book", "nodes": [
        {"node_id": "a", "name": "A", "learnable": True, "module_id": "m1"},
        {"node_id": "b", "name": "B", "learnable": True, "module_id": "m2"}],
        "modules": [{"module_id": "m1", "index": 0, "title": "Phần A", "node_ids": ["a"]},
                    {"module_id": "m2", "index": 1, "title": "Phần B", "node_ids": ["b"]}],
        "requires_edges": []}, [NS(chunk_id="c", text="A", page=1, char_start=0, char_end=1,
                                     section_path=[], order_index=0)])
    result.graph_version = 2
    return result


def test_library_lists_here_and_elsewhere_and_keeps_artifacts_after_session_delete():
    g, store = graph(), InMemoryPhaseBStore()
    sessions = store
    scope_a, scope_b = module_scope(g, "m1"), module_scope(g, "m2")
    sessions.put_record("session", "gone", {"owner": "alice", "doc_id": "book"})
    store.put_record("documents", "doc-1", {"document_id": "doc-1", "owner": "alice", "doc_id": "book",
        "title": "Notes on B", "home_scope": scope_a, "session_id": "gone", "origin": "assistant",
        "node_ids": ["b"], "created_at": "2026-10-18T00:00:00+00:00", "status": "ready"})
    store.put_record("quiz_attempt", "quiz-1", {"attempt_id": "quiz-1", "owner": "alice", "doc_id": "book",
        "title": "Quiz A", "home_scope": scope_a, "session_id": None, "origin": "button",
        "node_ids": ["a"], "submission": {"correct_count": 3, "question_count": 4},
        "created_at": "2026-10-18T00:00:01+00:00"})
    store.put_record("documents", "road-1", {"document_id": "road-1", "owner": "alice", "doc_id": "book",
        "title": "Roadmap guide", "home_scope": {"kind": "roadmap"}, "session_id": None,
        "origin": "button", "node_ids": ["a", "b"], "created_at": "2026-10-18T00:00:02+00:00"})
    store.delete_record("session", "gone")

    library = LibraryUseCase(store, g)
    in_a = library.list_library("alice", "book", "module:m1")["items"]
    in_b = library.list_library("alice", "book", "module:m2")["items"]
    assert {(row["id"], row["group"]) for row in in_a} == {
        ("doc-1", "here"), ("quiz-1", "here"), ("road-1", "elsewhere")}
    assert {(row["id"], row["group"]) for row in in_b} == {
        ("doc-1", "elsewhere"), ("road-1", "elsewhere")}
    doc_item = next(row for row in in_b if row["id"] == "doc-1")
    assert doc_item["label"] == "tạo ở nơi khác" and doc_item["session_deleted"]
    assert doc_item["module_labels"] == ["Phần B"]
    quiz_item = next(row for row in in_a if row["id"] == "quiz-1")
    assert quiz_item["score"] == {"correct": 3, "total": 4}
    assert library.list_library("alice", "book", "roadmap")["items"][0]["id"] == "road-1"
    assert {row["id"] for row in library.list_library("alice", "book", "all")["items"]} == {
        "doc-1", "quiz-1", "road-1"}
    assert library.list_library("bob", "book", "all")["items"] == []


def test_library_resolves_home_scope_by_current_node_overlap_not_saved_module_id():
    g, store = graph(), InMemoryPhaseBStore()
    g.modules = {"new": {"module_id": "new", "index": 0, "title": "Đã tách", "node_ids": ["a"]},
                 "other": {"module_id": "other", "index": 1, "title": "B", "node_ids": ["b"]}}
    store.put_record("documents", "doc-2", {"document_id": "doc-2", "owner": "alice", "doc_id": "book",
        "home_scope": {"kind": "module", "node_ids": ["a"], "module_id_at_creation": "m1",
                       "graph_version_at_creation": 1},
        "node_ids": ["a"], "origin": "button", "created_at": "2026-10-18T00:00:00+00:00"})
    items = LibraryUseCase(store, g).list_library("alice", "book", "module:new")["items"]
    assert len(items) == 1 and items[0]["group"] == "here"
