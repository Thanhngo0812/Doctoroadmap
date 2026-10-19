import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.phase_b.library import LibraryUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.application.ports.phase_b import ConversationEvent
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from wayfinder.composition import WebServices
from wayfinder.fakes.media import MemoryMediaStore


@dataclass
class FakeClock:
    instant: datetime = field(default_factory=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))

    def now(self) -> datetime:
        return self.instant

    def today(self, timezone_name: str):
        return self.instant.astimezone(ZoneInfo(timezone_name)).date()

    def advance(self, seconds: float) -> None:
        self.instant += timedelta(seconds=seconds)


@dataclass
class ScriptedModel:
    json_replies: list[dict[str, Any]] = field(default_factory=list)
    tool_turns: list[list[ConversationEvent]] = field(default_factory=list)
    model_id: str = "scripted-phase-b"
    json_calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    tool_calls: list[tuple[list[dict[str, Any]], str]] = field(default_factory=list)
    last_usage: dict[str, int] = field(default_factory=lambda: {"promptTokenCount": 0, "candidatesTokenCount": 0})

    def _next_json(self) -> dict[str, Any]:
        if not self.json_replies:
            raise AssertionError("scripted model has no JSON reply for this call")
        return self.json_replies.pop(0)

    def ask_json(self, prompt: str, *, response_schema: dict[str, Any], system_prompt: str = "") -> dict[str, Any]:
        self.json_calls.append((prompt, response_schema))
        return self._next_json()

    def stream_json(self, system: str, prompt: str, schema: dict[str, Any]):
        self.json_calls.append((prompt, schema))
        return iter([json.dumps(self._next_json(), ensure_ascii=False)])

    def start_session(self, system_prompt: str, tools=()):
        model = self

        class Session:
            def stream_json(self, prompt: str, *, response_schema: dict[str, Any], **_kwargs: Any):
                return model.stream_json(system_prompt, prompt, response_schema)

        return Session()

    def stream(self, messages: list[dict[str, Any]], *, mode: str = "AUTO"):
        self.tool_calls.append((messages, mode))
        if not self.tool_turns:
            raise AssertionError("scripted model has no tool turn for this call")
        yield from self.tool_turns.pop(0)


@dataclass
class FakeEmbedding:
    vectors: list[list[float]] = field(default_factory=list)
    identifier: str = "scripted-embedding"
    embedding_model_id: str = "scripted-embedding-v1"
    requests: list[list[EmbeddingRequest]] = field(default_factory=list)

    def embed(self, requests: list[EmbeddingRequest]) -> list[list[float]]:
        self.requests.append(list(requests))
        return [self.vectors[index] if index < len(self.vectors) else [1.0, 0.5, -0.25]
                for index in range(len(requests))]


@dataclass
class PhaseBTestRuntime:
    store: InMemoryPhaseBStore
    clock: FakeClock
    graph: LearningGraph
    model: ScriptedModel
    embedding: FakeEmbedding
    progress: ProgressUseCase
    sessions: SessionUseCase
    library: LibraryUseCase
    lecture: LectureUseCase
    quiz: QuizUseCase
    assistant: AssistantUseCase
    documents: DocumentUseCase


@dataclass
class TestApplication:
    services: WebServices
    phase_b: PhaseBTestRuntime
    media_store: MemoryMediaStore


def _sample_graph() -> LearningGraph:
    from types import SimpleNamespace

    quotes = [
        "Tập hợp là một nhóm đối tượng được xác định rõ ràng.",
        "Tập hợp gồm các phần tử có cùng một đặc điểm.",
        "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.",
    ]
    text = " ".join(quotes)
    chunk = SimpleNamespace(
        chunk_id="c1", doc_id="sample", order_index=0, split_index=0, page=1,
        char_start=0, char_end=len(text), parent_section_id="s1", section_path=["Toán"],
        heading_level=1, block_types=["paragraph"], text=text, context_prefix=None,
        image_refs=[], token_count=50, tokenizer_id="test", table_refs=[], formula_refs=[], role="noi_dung",
    )
    graph_payload = {
        "doc_id": "sample", "graph_version": "g1",
        "nodes": [{"node_id": "a", "name": "Tập hợp", "display_name": "Tập hợp", "learnable": True,
                   "module_id": "m1", "teaching_chunk_ids": ["c1"], "defining_chunk_ids": [],
                   "anchor": {"chunk_id": "c1", "sentence": quotes[0]}}],
        "modules": [{"module_id": "m1", "index": 1, "title": "Cơ sở", "node_ids": ["a"]}],
        "requires_edges": [], "open_edges": [], "chunk_module_map": {"c1": {"module_id": "m1"}},
    }
    return LearningGraph(graph_payload, [chunk])


def build_test_application() -> TestApplication:
    store, clock, graph = InMemoryPhaseBStore(), FakeClock(), _sample_graph()
    model, embedding, settings = ScriptedModel(), FakeEmbedding(), BSettings()
    progress = ProgressUseCase(store, graph, clock=clock)
    sessions = SessionUseCase(store, graph, settings=settings, clock=clock)
    library = LibraryUseCase(store, graph, settings=settings, clock=clock)
    lecture = LectureUseCase(model, store, settings=settings, clock=clock, progress=progress)
    quiz = QuizUseCase(graph, store, model, settings=settings, progress_use_case=progress, clock=clock)
    assistant = AssistantUseCase(graph, store, model, lecture=lecture.get, settings=settings,
                                 clock=clock, progress=progress)
    documents = DocumentUseCase(model, store, settings=settings, clock=clock)
    phase_b = PhaseBTestRuntime(store, clock, graph, model, embedding, progress, sessions, library,
                                lecture, quiz, assistant, documents)
    services = WebServices(health_check=lambda: "ok", model=model, embedding=embedding)
    return TestApplication(services, phase_b, MemoryMediaStore())
