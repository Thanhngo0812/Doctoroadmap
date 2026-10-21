"""Construct web use cases with their dependencies; never instantiate the CLI JSON runtime."""
from doc2roadmap.application.phase_b.budget import DailySpendGuard
from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.domain.phase_b_limits import BSettings


class WebLearningRuntime:
    def __init__(self, store, *, model=None, embedding=None, clock=None, settings=None):
        self.store, self.model, self.embedding = store, model, embedding
        self.clock = clock or SystemClock()
        self.settings = settings or BSettings()
        self.spend_guard = DailySpendGuard(store, settings=self.settings, clock=self.clock)

    def progress(self, graph):
        return ProgressUseCase(self.store, graph, clock=self.clock)

    def sessions(self, graph):
        return SessionUseCase(self.store, graph, settings=self.settings, clock=self.clock)
