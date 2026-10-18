from datetime import datetime, timezone
from threading import Event, Thread
from types import SimpleNamespace

import pytest

from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.domain.phase_b_limits import context_hash
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore


@pytest.fixture(params=["memory", "json"])
def store(request, tmp_path):
    return InMemoryPhaseBStore() if request.param == "memory" else JsonPhaseBStore(tmp_path / "b.json")


def _graph(doc_id="synthetic", node_ids=("a", "b")):
    return SimpleNamespace(
        doc_id=doc_id,
        learnable_nodes={node_id: {"node_id": node_id} for node_id in node_ids},
        modules={"m": {"node_ids": list(node_ids)}},
    )


class _Clock:
    def now(self):
        return datetime(2026, 10, 19, tzinfo=timezone.utc)


@pytest.mark.parametrize("learner_first", [True, False], ids=["learner-before-quiz", "quiz-before-learner"])
def test_learner_choice_wins_in_either_order_across_use_cases(store, learner_first):
    graph = _graph()
    learner_progress = ProgressUseCase(store, graph, clock=_Clock())
    quiz_progress = ProgressUseCase(store, graph, clock=_Clock())

    if learner_first:
        learner_progress.set_progress("alice", "synthetic", "a", False)
        quiz_progress.mark_quiz_correct("alice", "synthetic", ["a"])
    else:
        quiz_progress.mark_quiz_correct("alice", "synthetic", ["a"])
        learner_progress.set_progress("alice", "synthetic", "a", False)

    progress = learner_progress.get_progress("alice", "synthetic")
    assert progress["nodes"]["a"]["state"] == "not_learned"
    assert progress["nodes"]["a"]["source"] == "learner"


def test_learner_not_learned_choice_wins_if_quiz_completion_races(store):
    graph = _graph()
    quiz_progress = ProgressUseCase(store, graph, clock=_Clock())
    learner_progress = ProgressUseCase(store, graph, clock=_Clock())
    quiz_read, resume_quiz = Event(), Event()
    original_get_record = store.get_record
    pause_next_progress_read = True

    def paused_get_record(kind, record_id):
        nonlocal pause_next_progress_read
        value = original_get_record(kind, record_id)
        if kind == "progress" and pause_next_progress_read:
            pause_next_progress_read = False
            quiz_read.set()
            assert resume_quiz.wait(timeout=2)
        return value

    store.get_record = paused_get_record
    quiz = Thread(target=quiz_progress.mark_quiz_correct, args=("alice", "synthetic", ["a"]))
    quiz.start()
    assert quiz_read.wait(timeout=2)

    manual_started, manual_done = Event(), Event()

    def mark_not_learned():
        manual_started.set()
        learner_progress.set_progress("alice", "synthetic", "a", False)
        manual_done.set()

    manual = Thread(target=mark_not_learned)
    manual.start()
    assert manual_started.wait(timeout=2)
    manual_done.wait(timeout=.25)
    resume_quiz.set()
    quiz.join(timeout=2)
    manual.join(timeout=2)

    assert not quiz.is_alive() and not manual.is_alive()
    assert manual_done.is_set()
    assert learner_progress.get_progress("alice", "synthetic")["nodes"]["a"]["state"] == "not_learned"
    if hasattr(store, 'path'):
        persisted = JsonPhaseBStore(store.path)
        saved = persisted.get_record('progress', context_hash(['alice', 'synthetic', 'a']))
        assert saved['state'] == 'not_learned' and saved['source'] == 'learner'


def test_racing_progress_write_preserves_other_owner_document_and_node(store):
    same_doc = ProgressUseCase(store, _graph(), clock=_Clock())
    other_doc = ProgressUseCase(store, _graph("other-doc", ("z",)), clock=_Clock())
    same_doc.set_progress("bob", "synthetic", "b", True)
    other_doc.set_progress("alice", "other-doc", "z", True)

    same_doc.mark_quiz_correct("alice", "synthetic", ["a"])
    same_doc.set_progress("alice", "synthetic", "a", False)

    assert same_doc.get_progress("alice", "synthetic")["nodes"]["a"]["state"] == "not_learned"
    assert same_doc.get_progress("alice", "synthetic")["nodes"]["b"]["state"] == "not_learned"
    assert same_doc.get_progress("bob", "synthetic")["nodes"]["b"]["state"] == "learned"
    assert other_doc.get_progress("alice", "other-doc")["nodes"]["z"]["state"] == "learned"

    if hasattr(store, "path"):
        persisted = JsonPhaseBStore(store.path)
        assert persisted.get_record("progress", context_hash(["alice", "synthetic", "a"]))["state"] == "not_learned"
        assert persisted.get_record("progress", context_hash(["bob", "synthetic", "b"]))["state"] == "learned"
        assert persisted.get_record("progress", context_hash(["alice", "other-doc", "z"]))["state"] == "learned"
