from datetime import datetime, timezone
from threading import Event, Lock, Thread

from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


class _ProgressRaceStore(InMemoryPhaseBStore):
    def __init__(self):
        super().__init__()
        self.read_quiz_value = Event()
        self.resume_quiz = Event()
        self.pause_next_progress_read = True

    def get_record(self, kind, record_id):
        value = super().get_record(kind, record_id)
        if kind == "progress" and self.pause_next_progress_read:
            self.pause_next_progress_read = False
            self.read_quiz_value.set()
            assert self.resume_quiz.wait(timeout=2)
        return value


class _Clock:
    def now(self):
        return datetime(2026, 10, 18, tzinfo=timezone.utc)


def test_learner_not_learned_choice_wins_if_quiz_completion_races():
    store = _ProgressRaceStore()
    graph = type("Graph", (), {"doc_id": "book", "learnable_nodes": {"n": {"node_id": "n"}},
                                "modules": {}})()
    progress = ProgressUseCase(store, graph, clock=_Clock())
    quiz = Thread(target=progress.mark_quiz_correct, args=("alice", "book", ["n"]))
    quiz.start()
    assert store.read_quiz_value.wait(timeout=2)

    manual_started, manual_done = Event(), Event()

    def mark_not_learned():
        manual_started.set()
        progress.set_progress("alice", "book", "n", False)
        manual_done.set()

    manual = Thread(target=mark_not_learned)
    manual.start()
    assert manual_started.wait(timeout=2)
    manual_done.wait(timeout=.25)
    store.resume_quiz.set()
    quiz.join(timeout=2)
    manual.join(timeout=2)

    assert not quiz.is_alive() and not manual.is_alive()
    assert manual_done.is_set()
    assert progress.get_progress("alice", "book")["nodes"]["n"]["state"] == "not_learned"


def test_assistant_never_reminds_more_than_three_unlearned_prerequisites(monkeypatch):
    from test_phase_b_assistant_sa36 import ask, prepare
    from doc2roadmap.domain.learning_graph import LearningGraph

    graph, store = prepare()
    prerequisites = [{"node_id": node_id, "quote": f"Source for {node_id}."}
                     for node_id in ("a", "b", "c", "extra")]
    monkeypatch.setattr(LearningGraph, "why_here", lambda *_args, **_kwargs: {"prerequisites": prerequisites})

    answer = ask(graph, store)

    assert [row["node_id"] for row in answer["graph_cards"]["reminders"]] == ["a", "b", "c"]


def test_concurrent_paid_calls_do_not_exceed_daily_cap():
    from dataclasses import replace

    from doc2roadmap.application.phase_b.budget import DailyLimitExceeded, DailySpendGuard
    from doc2roadmap.application.phase_b.common import call_json
    from doc2roadmap.domain.phase_b_limits import BSettings

    first_entered, release_first = Event(), Event()
    settings = replace(BSettings(), learner_daily_max_usd=.20, document_max_output_tokens=80_000)

    class _Reply:
        payload = {"ok": True}
        usage = {"promptTokenCount": 0, "candidatesTokenCount": 80_000}

    class NoNetworkFakeModel:
        model_id = settings.model_id

        def __init__(self):
            self.calls = 0
            self.lock = Lock()

        def ask_json(self, prompt, **_kwargs):
            with self.lock:
                self.calls += 1
                first = self.calls == 1
            if first:
                first_entered.set()
                assert release_first.wait(timeout=2)
            return _Reply()

    store = InMemoryPhaseBStore()
    guard = DailySpendGuard(store, settings=settings)
    model = NoNetworkFakeModel()
    errors = []

    def call(index):
        try:
            call_json(model, f"request {index}", response_schema={}, store=store,
                      purpose="document", doc_id="book", context_hash=f"request-{index}",
                      allow_spend=True, settings=settings, learner_id="alice", spend_guard=guard)
        except BaseException as error:
            errors.append(error)

    threads = [Thread(target=call, args=(index,)) for index in range(2)]
    threads[0].start()
    assert first_entered.wait(timeout=2)
    threads[1].start()
    threads[1].join(timeout=.25)
    release_first.set()
    for thread in threads:
        thread.join(timeout=2)

    assert not any(thread.is_alive() for thread in threads)
    assert all(isinstance(error, DailyLimitExceeded) for error in errors)
    rows = store.usage_rows()
    assert all(abs(row["cost_usd"] - .12) < 1e-12 for row in rows)
    assert sum(row["cost_usd"] for row in rows) <= settings.learner_daily_max_usd
    assert model.calls <= 1
