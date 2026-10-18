from types import SimpleNamespace as NS

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.scope import module_scope
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def graph():
    text = "Target d is defined. A prerequisite for target d. B prerequisite for target d. C prerequisite for target d."
    chunks = [NS(chunk_id="c1", text=text, page=1, char_start=0, char_end=len(text),
                 section_path=["Target"], order_index=0, role="noi_dung")]
    parents = [("a", "A", "A prerequisite for target d."),
               ("b", "B", "B prerequisite for target d."),
               ("c", "C", "C prerequisite for target d.")]
    nodes = [{"node_id": node_id, "name": name, "learnable": True, "module_id": "m1",
              "teaching_chunk_ids": ["c1"]} for node_id, name, _ in parents]
    nodes.append({"node_id": "d", "name": "Target d", "learnable": True, "module_id": "m2",
                  "display_prerequisites": ["a", "b", "c"], "teaching_chunk_ids": ["c1"]})
    edges = [{"source": node_id, "target": "d", "edge_type": "requires", "quote": quote,
              "chunk_ids": ["c1"], "quote_chunk_id": "c1"} for node_id, _, quote in parents]
    payload = {"doc_id": "book", "nodes": nodes,
        "modules": [{"module_id": "m1", "index": 0, "title": "Basics", "node_ids": ["a", "b", "c"]},
                    {"module_id": "m2", "index": 1, "title": "Target", "node_ids": ["d"]}],
        "requires_edges": edges, "chunk_module_map": {"c1": {"module_id": "m2"}}}
    return LearningGraph(payload, chunks)


class Replay:
    model_id = "gemini-3.1-flash-lite"
    is_replay = True

    def __init__(self, text="Target d is defined. [S1]"):
        self.text = text

    def start_session(self, prompt, tools):
        return self

    def stream(self, messages, *, mode):
        yield Delta(self.text)
        yield Done({})


def prepare(scope="module"):
    g, store = graph(), InMemoryPhaseBStore()
    saved_scope = module_scope(g, "m2") if scope == "module" else {"kind": "roadmap"}
    store.put_record("session", "s", {"contract_version": "session-1", "session_id": "s",
        "owner": "alice", "doc_id": "book", "scope": saved_scope, "title": "Session",
        "title_source": "rule", "created_at": "2026-10-18T00:00:00+00:00",
        "updated_at": "2026-10-18T00:00:00+00:00", "turn_count": 0,
        "artifact_refs": [], "state": {"reminded_node_ids": [], "linked_node_ids": [],
        "reminders_enabled": True}})
    return g, store


def ask(g, store, *, question="Target d", reminders_enabled=None, model=None):
    return AssistantUseCase(g, store, model or Replay()).ask("book", 1, "s", question,
        owner="alice", allow_spend=True, reminders_enabled=reminders_enabled)


def test_reminder_uses_only_unlearned_hasse_prerequisites_and_is_once_per_session():
    g, store = prepare()
    progress = ProgressUseCase(store, g)
    progress.set_progress("alice", "book", "a", True)
    progress.set_progress("alice", "book", "b", True)
    first = ask(g, store)
    assert [row["node_id"] for row in first["graph_cards"]["reminders"]] == ["c"]
    assert first["graph_cards"]["reminders"][0]["quote"] == "C prerequisite for target d."
    second = ask(g, store)
    assert second["graph_cards"]["reminders"] == []


def test_all_learned_prerequisites_produce_no_reminder():
    g, store = prepare()
    progress = ProgressUseCase(store, g)
    for node_id in ("a", "b", "c"):
        progress.set_progress("alice", "book", node_id, True)
    assert ask(g, store)["graph_cards"]["reminders"] == []


def test_roadmap_refusal_and_disabled_reminders_produce_no_reminder():
    g, store = prepare(scope="roadmap")
    assert ask(g, store)["graph_cards"]["reminders"] == []

    g, store = prepare()
    refused = ask(g, store, question="Unknown unrelated question")
    assert refused["status"] in {"not_in_document", "insufficient_context"}
    assert refused["graph_cards"]["reminders"] == []

    g, store = prepare()
    disabled = ask(g, store, reminders_enabled=False)
    assert disabled["graph_cards"]["reminders"] == []
