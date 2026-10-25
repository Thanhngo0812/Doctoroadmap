from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    label: str | None = None
    chunk_id: str | None = None
    page: int | None = None
    section_path: list[str] = Field(default_factory=list)
    quote: str | None = None
    char_start: int | None = None
    char_end: int | None = None


class Formula(BaseModel):
    label: str | None = None
    formula_id: str | None = None
    occurrence_id: str | None = None
    page: int | None = None
    asset_key: str | None = None
    url: str | None = None


class Definition(BaseModel):
    quote: str = ''
    chunk_id: str | None = None
    page: int | None = None
    citation: Citation | None = None
    formula_refs: list[Formula] = Field(default_factory=list)


class Recall(BaseModel):
    node_id: str
    name: str
    module_id: str | None = None
    module_number: int | None = None
    module_index: int | None = None
    module_title: str | None = None
    order_note: str | None = None
    definition: Definition


class Prerequisite(BaseModel):
    recall: Recall
    learner_status: Literal['learned', 'not_learned', 'unknown']


class NextLesson(BaseModel):
    node_id: str
    name: str
    module_id: str | None = None
    module_number: int | None = None
    module_index: int | None = None
    module_title: str | None = None
    quote: str | None = None
    citation: Citation | None = None
    learner_status: Literal['learned', 'not_learned', 'unknown']


class Position(BaseModel):
    module_id: str
    module_index: int | None = None
    index_in_module: int | None = None
    count_in_module: int
    previous_node_id: str | None = None
    next_node_id: str | None = None


class ReadPage(BaseModel):
    page: int | None = None
    chunk_id: str | None = None


class Failure(BaseModel):
    reason_code: str
    message: str = Field(min_length=1)
    retryable: Literal[True] = True
    read_page: ReadPage | None = None
    ask_assistant: bool = True


class Source(BaseModel):
    label: str
    chunk_id: str
    page: int | None = None
    section_path: list[str] = Field(default_factory=list)


class SelfCheck(BaseModel):
    question_md: str
    answer_md: str


class Media(BaseModel):
    asset_key: str
    caption: str = ''
    url: str


class SourceDocument(BaseModel):
    kind: Literal['pdf', 'docx']
    page_count: int | None = None


class LectureView(BaseModel):
    contract_version: Literal['lecture-3']
    course_id: str
    doc_id: str
    graph_version: int
    node_id: str
    lecture_key: str | None = None
    status: Literal['generating', 'ready', 'failed', 'no_source']
    position: Position
    definition: Definition
    prerequisites: list[Prerequisite] = Field(default_factory=list)
    next_up: list[NextLesson] = Field(default_factory=list)
    body_md: str = ''
    self_check: SelfCheck | None = None
    sources: list[Source] = Field(default_factory=list)
    failure: Failure | None = None
    warnings: list[str] = Field(default_factory=list)
    usage: dict[str, int | float] = Field(default_factory=dict)
    media: list[Media] = Field(default_factory=list)
    source_document: SourceDocument | None = None
