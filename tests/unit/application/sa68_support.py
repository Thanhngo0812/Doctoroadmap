"""Shared fakes for the SA-68 `quiz-3` tests: a small book, a scripted generator, a scripted blind solver."""
from __future__ import annotations

import json
import threading
import time
from types import SimpleNamespace

from doc2roadmap.domain.learning_graph import LearningGraph

from sa64_support import chunk

MARKER = "Các câu trắc nghiệm (phương án đánh số từ 0):\n"
SOLVER_REASON = "LY-DO-RIENG-CUA-NGUOI-GIAI"
EXPLANATION = "GIAI-THICH-RIENG-CUA-CAU"
WHY_WRONG = "VI-SAO-SAI-RIENG"


def make_book(*, plain=4, formula=True):
    """Module `m`: `plain` concepts with a cloze-friendly definition, and (with `formula`) one whose passages lost formulas."""
    chunks, nodes = [], []
    for number in range(1, plain + 1):
        name = f"Khái niệm {number}"
        text = (f"{name} là đối tượng được xác định rõ ràng trong sách học. "
                f"{name} còn được dùng ở nhiều chương khác của giáo trình.")
        chunks.append(chunk(len(chunks), "noi_dung", f"Chương {number}", ["Mục"], 2 + number, text))
        nodes.append({"node_id": f"n{number}", "name": name, "display_name": name, "learnable": True,
                      "module_id": "m", "teaching_chunk_ids": [f"c{len(chunks) - 1}"], "defining_chunk_ids": [],
                      "anchor": {"chunk_id": f"c{len(chunks) - 1}", "sentence": text.split(". ")[0] + "."}})
    tree = None
    if formula:
        first = chunk(len(chunks), "noi_dung", "Tương quan", ["Hệ số"], 7,
                      "Hệ số tương quan được tính bằng [formula] và cho ví dụ r = [formula].")
        first.formula_refs = [SimpleNamespace(formula_id="f1"), SimpleNamespace(formula_id="f2")]
        second = chunk(len(chunks) + 1, "noi_dung", "Tương quan", ["Hệ số"], 9,
                       "Hệ số tương quan lớn khi [formula] gần 1.")
        second.formula_refs = [SimpleNamespace(formula_id="f3")]
        chunks += [first, second]
        nodes.append({"node_id": "nf", "name": "Hệ số tương quan", "display_name": "Hệ số tương quan",
                      "learnable": True, "module_id": "m", "teaching_chunk_ids": [first.chunk_id], "defining_chunk_ids": [],
                      "anchor": {"chunk_id": first.chunk_id, "sentence": "Hệ số tương quan được tính bằng [formula]"}})
        tree = SimpleNamespace(nodes=[SimpleNamespace(formula_id=f"f{k}", raw_text=raw) for k, raw in
                                      enumerate(["r = 0,8165", "S xy / S x S y", "r → 1"], 1)])
    modules = [{"module_id": "m", "index": 0, "title": "Tương quan", "node_ids": [node["node_id"] for node in nodes]}]
    graph = LearningGraph({"doc_id": "d", "graph_version": "g1", "nodes": nodes, "modules": modules,
                           "requires_edges": [], "open_edges": []}, chunks, tree=tree)
    graph.parse_version = 3
    return graph


def raw_item(stem, *, correct=0, bloom="nho", labels=("S1",), texts=None):
    texts = texts or [f"{stem} / phương án {k}" for k in range(4)]
    return {"bloom": bloom, "stem": stem, "correct_index": correct, "explanation": f"{EXPLANATION} {stem}",
            "options": [{"text": text, "why_wrong": "" if k == correct else f"{WHY_WRONG} {text}"}
                        for k, text in enumerate(texts)],
            "source_labels": list(labels)}


class Reply:
    def __init__(self, payload):
        self.payload = payload
        self.usage = {"promptTokenCount": 1000, "candidatesTokenCount": 300}


class Session:
    def __init__(self, model, system):
        self.model, self.system = model, system

    def ask_json(self, prompt, *, response_schema, images=(), temperature=None, thinking_level=None):
        return self.model.answer(self.system, prompt, response_schema, list(images), temperature, thinking_level)


class Scripted:
    """Records each call; subclasses fill `reply`."""

    def __init__(self, model_id="gemini-3.1-flash-lite", delay=0.0):
        self.model_id, self.delay = model_id, delay
        self.calls, self.lock = [], threading.Lock()
        self.in_flight = self.peak = 0

    def start_session(self, system, tools=()):
        return Session(self, system)

    def answer(self, system, prompt, schema, images, temperature, thinking_level):
        call = SimpleNamespace(system=system, prompt=prompt, schema=schema, images=images, temperature=temperature,
                               thinking_level=thinking_level)
        with self.lock:
            self.calls.append(call)
            self.in_flight += 1
            self.peak = max(self.peak, self.in_flight)
        try:
            if self.delay:
                time.sleep(self.delay)
            return Reply(self.reply(call))
        finally:
            with self.lock:
                self.in_flight -= 1


class Generator(Scripted):
    """`script(concept_name, lap) -> list of raw items`; remembers each stem's correct text for the solver."""

    def __init__(self, script, **kwargs):
        super().__init__(**kwargs)
        self.script, self.correct = script, {}

    def reply(self, call):
        concept = call.prompt.split("\n", 1)[0].removeprefix("Khái niệm: ")
        with self.lock:
            lap = sum(1 for other in self.calls if other.prompt.startswith(f"Khái niệm: {concept}\n")) - 1
        items = self.script(concept, lap)
        for item in items:
            try:
                self.correct[item["stem"]] = item["options"][item["correct_index"]]["text"]
            except (IndexError, TypeError):
                pass          # a malformed question: the use case must drop it, the solver never sees it
        return {"items": items}


class Solver(Scripted):
    """`mode(stem) -> "right" | "wrong" | "ambiguous" | "missing" | "badchoice"`; answers from the generator's record."""

    def __init__(self, generator, mode=lambda stem: "right", **kwargs):
        super().__init__(**kwargs)
        self.generator, self.mode = generator, mode

    def reply(self, call):
        questions = json.loads(call.prompt.split(MARKER, 1)[1])
        answers = []
        for question in questions:
            how = self.mode(question["stem"])
            options = question["options"]
            right = options.index(self.generator.correct[question["stem"]])
            other = next(k for k in range(len(options)) if k != right)
            if how == "missing":
                continue
            answers.append({"q": question["q"], "chosen": 9 if how == "badchoice" else other if how == "wrong" else right,
                            "ambiguous": how == "ambiguous", "reason": SOLVER_REASON})
        return {"answers": answers}


class Reverse:
    """An rng whose shuffle is not the identity: options reach the solver in the opposite order."""

    def shuffle(self, rows):
        rows.reverse()
