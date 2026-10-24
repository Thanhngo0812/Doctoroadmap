"""Run the existing SA-47/48 assertions with a PostgreSQL store fixture."""
from threading import Event, Lock

import pytest

from tests.unit.application.test_phase_b_progress_sa47 import (
    test_learner_choice_wins_in_either_order_across_use_cases,
    test_learner_not_learned_choice_wins_if_quiz_completion_races,
    test_racing_progress_write_preserves_other_owner_document_and_node,
)
from tests.unit.application.test_phase_b_budget_sa48 import (
    test_reservations_share_learner_and_system_pools_across_guard_instances,
    test_failed_calls_release_reservations_and_record_billed_usage_once,
    test_call_uses_admission_day_and_releases_unused_estimate,
    test_replay_remains_free_when_learner_budget_is_exhausted,
    test_two_lecture_nodes_share_the_system_reservation_and_cached_result_stays_available,
    test_assistant_sessions_share_learner_reservation_before_streaming,
    test_lecture_replay_is_available_when_system_spend_is_exhausted,
)
from wayfinder.infrastructure.database import create_database_engine
from wayfinder.infrastructure.phase_b_store import PostgresPhaseBStore


pytestmark = pytest.mark.postgres


@pytest.fixture
def store(postgres_phase_b_store):
    return postgres_phase_b_store


def test_existing_assistant_concurrency_sequence_on_postgres(monkeypatch, postgres_phase_b_store):
    from tests.unit.application import test_phase_b_assistant_concurrency as existing

    class Observed(PostgresPhaseBStore):
        def __init__(self):
            super().__init__(create_database_engine(postgres_phase_b_store.engine.url))
            self.turn_requests = 0
            self.turn_lock = Lock()
            self.follower_waiting = Event()

        def single_flight(self, key, generate, **options):
            if key.startswith("assistant-turn:"):
                with self.turn_lock:
                    self.turn_requests += 1
                    if self.turn_requests == 2:
                        self.follower_waiting.set()
            return super().single_flight(key, generate, **options)

    observed = Observed()
    monkeypatch.setattr(existing, "_ObservedStore", lambda: observed)
    try:
        existing.test_same_client_turn_runs_one_model_sequence_and_artifact_then_replays_final_to_both()
    finally:
        observed.close()


def test_late_provider_retains_postgres_reservation(store):
    from dataclasses import replace
    from time import monotonic, sleep
    from doc2roadmap.application.phase_b.lectures import LectureUseCase
    from doc2roadmap.domain.phase_b_limits import BSettings
    from test_phase_b_lecture_b2 import _Model, _payload
    from test_phase_b_lecture_sa26 import _graph

    # The original 30ms memory/JSON regression remains unchanged. Allow local
    # PostgreSQL I/O to start the provider, then exercise the same late-response race.
    settings = replace(BSettings(), system_daily_max_usd=.20, lecture_max_output_tokens=80_000,
                       lecture_click_timeout_seconds=.3)
    released = Event()
    original_delete = store.delete_record

    def observe_release(kind, record_id):
        original_delete(kind, record_id)
        if kind == "spend_reservation":
            released.set()

    store.delete_record = observe_release

    class Model(_Model):
        model_id = settings.model_id

        def start_session(self, system_prompt):
            session = super().start_session(system_prompt)
            session.last_usage = {"candidatesTokenCount": 80_000}
            return session

    model = Model([_payload()[0]])
    model.block = True
    graph = _graph(with_later=True)
    try:
        result = LectureUseCase(model, store, settings=settings).make("d1", "g1", graph, "a", allow_spend=True)
        assert result["failure"]["reason_code"] == "het_thoi_gian"
        assert model.entered.is_set() and len(store.list_records("spend_reservation")) == 1
        blocked = LectureUseCase(model, store, settings=settings).make("d1", "g1", graph, "b", allow_spend=True)
        assert blocked["failure"]["reason_code"] == "tran_he_thong" and model.calls == 1
    finally:
        model.release.set()
    assert released.wait(2)
    assert store.list_records("spend_reservation") == []
    assert sum(row["cost_usd"] for row in store.usage_rows()) == .12
    assert store.usage_rows()[0]["created_at"]
    deadline = monotonic() + 5
    while store._flights and monotonic() < deadline:
        sleep(.01)
    assert not store._flights
