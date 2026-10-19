"""W-13 boundary: workers provide configuration and persist the final result."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Protocol


BUILD_STEPS = ("doc_reading", "concepts", "graph", "learning_prep")


@dataclass
class BuildResult:
    doc_id: str
    status: str
    pipeline_version: str
    graph_version: int | None = None
    completed_steps: list[str] = field(default_factory=list)
    step_details: dict = field(default_factory=dict)
    spent_usd: float = 0.0
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    usage_complete: bool = True
    elapsed_seconds: float = 0.0
    error: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class BuildRejected(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


Progress = Callable[[str, dict], None]
Cancellation = Callable[[], bool]
BuildRecorder = Callable[[BuildResult], None]


class BuildRunner(Protocol):
    def execute(self, file_path: Path, doc_id: str, *, language: str = "vi",
                progress: Progress | None = None, cancelled: Cancellation | None = None,
                dry_run: bool = False) -> BuildResult: ...


class BuildPipeline(Protocol):
    """All stage outputs are small metadata dictionaries, never model estimates.

    read returns page_texts (including empty pages), chunks_version and parse_version.
    It enforces require_text_quality and raises BuildRejected('chu_loi', ...) on failure.
    roadmap returns graph_version. usage returns cumulative counters for this pipeline
    instance; the orchestrator takes a before/after delta for each execution.
    inspect is read-only: report cached/unknown dependencies without model calls.
    """

    def read(self, file_path: Path, doc_id: str) -> dict: ...
    def label_roles(self, doc_id: str) -> dict: ...
    def a3(self, doc_id: str) -> dict: ...
    def canonical(self, doc_id: str, language: str) -> dict: ...
    def roadmap(self, doc_id: str) -> dict: ...
    def learning_prep(self, file_path: Path, doc_id: str, graph_version: int) -> dict: ...
    def inspect(self, doc_id: str) -> dict: ...
    def usage(self) -> dict: ...
