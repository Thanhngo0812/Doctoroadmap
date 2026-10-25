"""Construct web use cases with their dependencies; never instantiate the CLI JSON runtime."""
from dataclasses import replace
from doc2roadmap.application.phase_b.budget import DailySpendGuard
from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.domain.phase_b_limits import BSettings


class WebLearningRuntime:
    def __init__(self, store, *, model=None, embedding=None, clock=None, settings=None, page_images=None, artifacts=None, model_for=None):
        self.store, self.model, self.embedding = store, model, embedding
        self.page_images = page_images
        self.artifacts, self.model_for = artifacts, model_for or (lambda purpose: self.model)
        self.clock = clock or SystemClock()
        self.settings = settings or replace(BSettings(), learner_daily_max_usd=1.0)
        self.spend_guard = DailySpendGuard(store, settings=self.settings, clock=self.clock)

    def progress(self, graph):
        return ProgressUseCase(self.store, graph, clock=self.clock)

    def sessions(self, graph):
        return SessionUseCase(self.store, graph, settings=self.settings, clock=self.clock)

    def lecture(self, graph):
        from doc2roadmap.application.phase_b.lecture3 import Lecture3UseCase
        return Lecture3UseCase(self.model, self.store, settings=self.settings, clock=self.clock,
                              progress=self.progress(graph), spend_guard=self.spend_guard,
                              page_images=self.page_images)

    def search(self, graph, query, **kwargs):
        from doc2roadmap.application.phase_b.retrieval import SearchDocumentB
        return SearchDocumentB(self.artifacts, self.embedding, self.store).search(query,
            doc_id=graph.doc_id, graph_version=graph.graph_version, allow_spend=True, **kwargs)

    def quiz(self, graph):
        from doc2roadmap.application.phase_b.quiz import QuizUseCase
        return QuizUseCase(graph, self.store, self.model_for('quiz_gen'), verifier_model=self.model_for('quiz_verify'),
            settings=self.settings, progress_use_case=self.progress(graph), spend_guard=self.spend_guard,
            clock=self.clock, page_images=self.page_images)

    def document(self, graph):
        from doc2roadmap.application.phase_b.documents import DocumentUseCase
        return DocumentUseCase(self.model_for('document'), self.store, settings=self.settings,
            search=(lambda query, **kw: self.search(graph, query, **kw)) if self.artifacts is not None else None,
            clock=self.clock, spend_guard=self.spend_guard, page_images=self.page_images)

    def assistant(self, graph, *, on_tool_start=None):
        from doc2roadmap.application.phase_b.assistant import AssistantUseCase
        from wayfinder.infrastructure.assistant_model import ActorBoundAssistantModel
        def starting(name):
            if on_tool_start:
                on_tool_start(name)
        def get_lecture(concept, **kwargs):
            starting('get_lecture')
            return self.lecture(graph).make(graph.doc_id, graph.graph_version, graph, concept,
                owner=kwargs.get('owner'), cache_only=True)
        def make_quiz(scope, n=None, level=None, *, owner, **kwargs):
            starting('make_quiz')
            return self.quiz(graph).make_quiz(graph.doc_id, None, owner, scope=scope, n=n, level=level,
                origin='assistant', allow_spend=True, home_scope=kwargs.get('home_scope'), session_id=kwargs.get('session_id'))
        def make_document(request, scope, *, owner, **kwargs):
            starting('make_document')
            return self.document(graph).create(graph.doc_id, graph.graph_version, graph, request, scope,
                owner=owner, origin='assistant', allow_spend=True,
                home_scope=kwargs.get('home_scope'), session_id=kwargs.get('session_id'))
        def search(query, **kwargs):
            starting('search_document')
            return self.search(graph, query, **kwargs)
        return AssistantUseCase(graph, self.store, ActorBoundAssistantModel(self.model_for('assistant')), settings=self.settings,
            search=search if self.artifacts is not None else None,
            lecture=get_lecture, quiz=make_quiz, document=make_document, clock=self.clock,
            progress=self.progress(graph), spend_guard=self.spend_guard, page_images=self.page_images)
