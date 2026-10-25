"""Shared fakes for the SA-64 `lecture-3` tests: a small book, a streaming model, a page-picture port and a clock."""
from __future__ import annotations

import threading
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from doc2roadmap.domain.learning_graph import LearningGraph

DEFINITION = "Tập hợp là một nhóm đối tượng được xác định rõ ràng."


def chunk(index, role, chapter, section, page, text):
    return SimpleNamespace(
        chunk_id=f"c{index}", doc_id="d1", order_index=index, split_index=0, page=page, char_start=0,
        char_end=len(text), parent_section_id="s", section_path=[chapter, *section], heading_level=1,
        block_types=["paragraph"], text=text, context_prefix=None, image_refs=[], token_count=10,
        tokenizer_id="test", table_refs=[], formula_refs=[], role=role)


def book_chunks(*, filler_size=1500, formula_pages=(), pile=0):
    """c2 is the definition; c10 sits far away under a heading that names the concept; c11 is another chapter."""
    rows = [
        chunk(0, "de_cuong", "Giới thiệu", ["Đề cương"], 1, "Tập hợp. " * 40),
        chunk(1, "hanh_chinh", "Giới thiệu", ["Hành chính"], 1, "Tập hợp tập hợp nộp bài."),
        chunk(2, "noi_dung", "Toán", ["Mở đầu"], 2, DEFINITION + " Mỗi đối tượng gọi là một phần tử của tập hợp."),
        chunk(3, "noi_dung", "Toán", ["Mở đầu"], 2, "Ví dụ 1. Nhóm A gồm các số 1, 2, 3 thì 2 thuộc A."),
    ]
    for index in range(4, 10):
        rows.append(chunk(index, "noi_dung", "Toán", ["Véc tơ"], 3 + index, f"Véc tơ số {index}. " + "x " * (filler_size // 2)))
    rows.append(chunk(10, "noi_dung", "Toán", ["Tập hợp nâng cao"], 30,
                      "Ví dụ xa. Hợp của hai nhóm có công thức [formula] ở cuối đoạn."))
    rows.append(chunk(11, "noi_dung", "Phụ lục", ["Ôn tập"], 40, "Tập hợp và tập hợp con. Tập hợp rỗng cũng là tập hợp."))
    for offset, page in enumerate(formula_pages):
        rows.append(chunk(20 + offset, "noi_dung", "Phụ lục", ["Công thức"], page,
                          f"Tập hợp tập hợp tập hợp ở trang {page} [formula]."))
    for offset in range(pile):
        rows.append(chunk(100 + offset, "noi_dung", "Phụ lục", ["Chồng"], 50 + offset,
                          "Tập hợp " + "y " * 400))
    return rows


def make_graph(**options):
    chunks = book_chunks(**options)
    nodes = [
        {"node_id": "a", "name": "Tập hợp", "display_name": "Tập hợp", "aliases": [{"name": "Set"}],
         "learnable": True, "module_id": "m1", "teaching_chunk_ids": ["c2"], "defining_chunk_ids": [],
         "anchor": {"chunk_id": "c2", "sentence": DEFINITION}},
        {"node_id": "b", "name": "Phép hợp", "display_name": "Phép hợp", "learnable": True, "module_id": "m2",
         "teaching_chunk_ids": ["c10"], "defining_chunk_ids": [], "anchor": {"chunk_id": "c10", "sentence": "Ví dụ xa."}},
        {"node_id": "z", "name": "Khái niệm lạ", "display_name": "Khái niệm lạ", "learnable": True, "module_id": "m1",
         "teaching_chunk_ids": [], "defining_chunk_ids": [], "anchor": {}},
    ]
    modules = [{"module_id": "m1", "index": 0, "title": "Cơ sở", "node_ids": ["a", "z"]},
               {"module_id": "m2", "index": 1, "title": "Phép toán", "node_ids": ["b"]}]
    edges = [{"source": "a", "target": "b", "edge_type": "requires", "quote": DEFINITION, "chunk_ids": ["c2"]}]
    graph = LearningGraph({"doc_id": "d1", "graph_version": "g1", "nodes": nodes, "modules": modules,
                           "requires_edges": edges, "open_edges": []}, chunks)
    graph.parse_version = 3
    return graph


GOOD_LESSON = (
    "Tập hợp cho ta cách gom các đối tượng lại thành một nhóm để nói về chúng cùng lúc.\n\n"
    "Theo sách, tập hợp là một nhóm đối tượng được xác định rõ ràng. [S1]\n\n"
    "Ví dụ: A gồm 1, 2, 3 thì 2 thuộc A. [S2]\n\n"
    "### Tự kiểm tra\n\n**Câu hỏi:** Số 5 có thuộc A không?\n\n**Đáp án:** Không, vì A chỉ gồm 1, 2, 3."
)


class FakeSession:
    def __init__(self, model, system):
        self.model, self.system = model, system
        self.last_usage, self.last_finish_reason, self.last_ttft_ms = {}, None, None

    def stream_text(self, prompt, *, images=(), temperature=None, transport_retries=None, timeout_seconds=None,
                    **extra):
        model = self.model
        index = len(model.calls)
        model.calls.append(SimpleNamespace(system=self.system, prompt=prompt, images=list(images),
                                           temperature=temperature, transport_retries=transport_retries,
                                           timeout_seconds=timeout_seconds, extra=extra, finished=False))
        script = model.scripts[min(index, len(model.scripts) - 1)]
        self.last_usage = {"promptTokenCount": 1000 + 100 * len(images), "candidatesTokenCount": 400}
        self.last_finish_reason = "STOP"
        call = model.calls[index]
        try:
            for piece in (script() if callable(script) else script):
                if isinstance(piece, BaseException):
                    raise piece
                yield piece
        finally:
            call.finished = True


class FakeModel:
    """Each script is a list of text pieces (an exception instance raises) or a generator function."""
    model_id = "gemini-3.1-flash-lite"

    def __init__(self, *scripts):
        self.scripts = scripts or (list_pieces(GOOD_LESSON),)
        self.calls = []

    def start_session(self, system, tools=()):
        return FakeSession(self, system)


def list_pieces(text, size=40):
    return [text[index:index + size] for index in range(0, len(text), size)]


class FakePages:
    def __init__(self, pages=None):
        self.pages, self.calls = pages or {}, []

    def get(self, doc_id, parse_version, page):
        self.calls.append((doc_id, parse_version, page))
        return self.pages.get(page)


class FakeClock:
    def __init__(self):
        self.value = datetime(2026, 10, 23, 8, 0, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def today(self, timezone_name):
        return date(2026, 10, 23)

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


def wait_for(condition, seconds=3.0):
    pause = threading.Event()
    for _ in range(int(seconds / 0.01)):
        if condition():
            return True
        pause.wait(0.01)
    return condition()
