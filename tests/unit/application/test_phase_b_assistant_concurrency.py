from threading import Barrier, Event, Lock, Thread

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done, ToolCall
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from types import SimpleNamespace as NS


def _graph():
    chunk = NS(chunk_id="c1", text="Ma trận là bảng các số.", page=1, char_start=0,
               char_end=23, section_path=["Ma trận"], order_index=0, role="noi_dung")
    payload = {
        "doc_id": "book",
        "nodes": [{"node_id": "a", "name": "Ma trận", "learnable": True,
                   "module_id": "m1", "teaching_chunk_ids": ["c1"]}],
        "modules": [{"module_id": "m1", "index": 0, "title": "Ma trận", "node_ids": ["a"]}],
        "requires_edges": [],
    }
    return LearningGraph(payload, [chunk])


class _ObservedStore(InMemoryPhaseBStore):
    def __init__(self):
        super().__init__()
        self.turn_requests = 0
        self.turn_lock = Lock()
        self.follower_waiting = Event()

    def single_flight(self, key, generate):
        if key.startswith("assistant-turn:"):
            with self.turn_lock:
                self.turn_requests += 1
                if self.turn_requests == 2:
                    self.follower_waiting.set()
        return super().single_flight(key, generate)


class _BlockingModel:
    model_id = "scripted-blocking"

    def __init__(self):
        self.release_first_rounds = Event()
        self.two_first_rounds = Event()
        self.lock = Lock()
        self.sessions = 0
        self.model_calls = 0
        self.first_rounds = 0

    def start_session(self, system_prompt, tools):
        with self.lock:
            self.sessions += 1
            session_id = self.sessions
        return _BlockingSession(self, session_id)


class _BlockingSession:
    def __init__(self, model, session_id):
        self.model, self.session_id, self.round = model, session_id, 0

    def stream(self, messages, *, mode):
        with self.model.lock:
            self.model.model_calls += 1
        if self.round == 0:
            with self.model.lock:
                self.model.first_rounds += 1
                if self.model.first_rounds >= 2:
                    self.model.two_first_rounds.set()
            self.model.release_first_rounds.wait(timeout=3)
            self.round += 1
            yield ToolCall("get_lecture", {"concept": "Ma trận"}, f"lecture-{self.session_id}")
            yield Done({"promptTokenCount": 10, "candidatesTokenCount": 2})
            return
        self.round += 1
        yield Delta("Ma trận là bảng các số. [S1]")
        yield Done({"promptTokenCount": 10, "candidatesTokenCount": 2})


def _run_pair(*, bypass_guard=False):
    model, store = _BlockingModel(), _ObservedStore()
    artifact_calls = []
    artifact_lock = Lock()

    def get_lecture(concept, *, owner, doc_id, graph_version, graph, allow_spend):
        with artifact_lock:
            artifact_calls.append(concept)
            number = len(artifact_calls)
        return {"lecture_key": f"lecture-{number}", "node_id": concept,
                "sections": [], "status": "ready"}

    store.put_record('session', 'session', {'contract_version': 'session-1', 'session_id': 'session',
        'owner': 'alice', 'doc_id': 'book', 'scope': {'kind': 'module', 'node_ids': ['a'],
        'module_id_at_creation': 'm1', 'graph_version_at_creation': 1}, 'title': 'Phiên học mới',
        'title_source': 'rule', 'created_at': '2026-10-18T00:00:00+00:00',
        'updated_at': '2026-10-18T00:00:00+00:00', 'turn_count': 0,
        'last_question_preview': '', 'artifact_refs': [],
        'state': {'reminded_node_ids': [], 'linked_node_ids': [], 'reminders_enabled': True}})
    use_case = AssistantUseCase(_graph(), store, model, lecture=get_lecture)
    if bypass_guard:
        # Mutation check: calling the underlying implementation bypasses public ask's guard.
        use_case.ask = use_case._ask

    events = [[], []]
    results, errors = [None, None], []
    barrier = Barrier(3)

    def ask(index):
        try:
            barrier.wait(timeout=2)
            results[index] = use_case.ask("book", 1, "session", "Ma trận là gì?",
                                          owner="alice", client_turn_id="same-turn",
                                          allow_spend=True, on_event=events[index].append)
        except BaseException as error:
            errors.append(error)

    threads = [Thread(target=ask, args=(index,), daemon=True) for index in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait(timeout=2)

    if bypass_guard:
        assert model.two_first_rounds.wait(timeout=2)
    else:
        assert store.follower_waiting.wait(timeout=2)
    model.release_first_rounds.set()
    for thread in threads:
        thread.join(timeout=3)

    assert not any(thread.is_alive() for thread in threads)
    assert not errors
    return model, artifact_calls, results, events, store


def test_same_client_turn_runs_one_model_sequence_and_artifact_then_replays_final_to_both():
    model, artifact_calls, results, events, store = _run_pair()

    assert model.sessions == 1
    assert model.model_calls == 2
    assert artifact_calls == ["a"]
    assert results[0]["answer_id"] == results[1]["answer_id"]
    assert [sum(event.get("event") == "final" for event in request_events) for request_events in events] == [1, 1]
    assert sum(event.get("event") == "artifact" for request_events in events
               for event in request_events) == 1
    assert len(store.usage_rows("book")) == 2


def test_mutation_bypassing_public_guard_duplicates_model_and_artifact_work():
    model, artifact_calls, results, events, _ = _run_pair(bypass_guard=True)

    assert model.sessions == 2
    assert model.model_calls == 4
    assert artifact_calls == ["a", "a"]
    assert results[0]["answer_id"] != results[1]["answer_id"]
    assert [sum(event.get("event") == "final" for event in request_events) for request_events in events] == [1, 1]
