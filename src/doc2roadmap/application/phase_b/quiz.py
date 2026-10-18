from __future__ import annotations

import hashlib
import json
import math
import random
import re
import secrets
import threading
import time
import unicodedata
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from doc2roadmap.application.prerequisite_prompt import PRICING_USD_PER_MILLION


QUIZ_SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "properties": {
            "concept": {"type": "string"}, "bloom": {"type": "string"},
            "stem": {"type": "string"},
            "correct": {"type": "object", "properties": {
                "text": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}},
                "quote": {"type": "string"}}, "required": ["text", "sources", "quote"],
                "additionalProperties": False},
            "distractors": {"type": "array", "items": {"type": "object", "properties": {
                "text": {"type": "string"}, "from": {"type": "string"}, "why_wrong": {"type": "string"},
                "sources": {"type": "array", "items": {"type": "string"}}, "quote": {"type": "string"}},
                "required": ["text", "from", "why_wrong", "sources", "quote"]},
                "minItems": 2, "maxItems": 2},
            "explanation": {"type": "string"},
            "formula_refs": {"type": "array", "items": {"type": "string"}},
        }, "required": ["concept", "bloom", "stem", "correct", "distractors", "explanation", "formula_refs"],
        "additionalProperties": False}},
        "gaps": {"type": "array", "items": {"type": "string"}}},
    "required": ["items", "gaps"], "additionalProperties": False,
}

VERIFIER_SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "properties": {
            "item_id": {"type": "string"}, "selected_option_id": {"type": "string"},
            "valid": {"type": "boolean"}, "quote": {"type": "string"},
            "distractor_verdicts": {"type": "array", "items": {"type": "object", "properties": {
                "option_id": {"type": "string"},
                "verdict": {"type": "string", "enum": ["sai theo nguồn", "đúng theo nguồn", "nguồn không nói"]}},
                "required": ["option_id", "verdict"], "additionalProperties": False}},
        }, "required": ["item_id", "selected_option_id", "valid", "quote", "distractor_verdicts"],
        "additionalProperties": False}},
    }, "required": ["items"], "additionalProperties": False,
}

VERIFIER_INSTRUCTIONS = (
    "Giải mù câu hỏi bằng cả hai nhóm chứng cứ: chunks là định nghĩa cho khái niệm đích; "
    "distractor_sources là các anchor định nghĩa cho những khái niệm nhiễu. Không chỉ tìm tên option "
    "trong chunks. Đối chiếu tên/alias của từng option với name/aliases trong distractor_sources; "
    "nếu khớp một candidate, hãy đọc anchor của candidate đó và so sánh với câu hỏi cùng chunks. "
    "Chỉ kết luận một option sai theo nguồn khi chứng cứ định nghĩa cho thấy rõ nó là khái niệm khác "
    "hoặc không thể thỏa mãn câu hỏi; việc tên không xuất hiện trong chunks không đủ để loại option. "
    "Nếu chứng cứ không phân biệt được thì ghi 'nguồn không nói'; nếu chứng cứ hỗ trợ option thì ghi "
    "'đúng theo nguồn'. Chọn đúng một option; nhiều đáp án đúng thì invalid. "
    "Phân loại từng nhiễu là sai theo nguồn, đúng theo nguồn, hoặc nguồn không nói. "
    "Trả items[{item_id,selected_option_id,valid,quote,distractor_verdicts}]."
)


class QuizUseCase:
    """Build, submit, and review self-check quizzes without tracking mastery."""

    def __init__(self, graph, store, model=None, *, verifier_model=None, settings=None,
                 source_registry=None, rng=None):
        self.graph = graph
        self.store = store
        self.model = model
        self.verifier_model = verifier_model or model
        self.settings = settings
        self.sources = source_registry or (graph.new_source_registry() if hasattr(graph, "new_source_registry") else None)
        self.rng = rng or random.Random()
        self._emit_lock = threading.Lock()

    def make_quiz(self, doc_id=None, module_id=None, owner=None, *, scope=None, graph=None,
                  graph_version=None, origin="module_button", n=None,
                  node_ids=None, concept_ids=None, level=None, allow_spend=False,
                  dry_run=False, on_event=None):
        if not doc_id or not owner:
            raise ValueError("doc_id và owner là bắt buộc")
        if origin not in {"module_button", "assistant"}:
            raise ValueError("origin không hợp lệ")
        if scope is not None:
            if module_id is not None or node_ids is not None or concept_ids is not None:
                raise ValueError("scope không thể đi cùng module_id hoặc node_ids")
            module_id, requested = self._resolve_scope(scope)
            if isinstance(scope, (list, tuple)):
                node_ids = requested
            elif requested is not None:
                node_ids = requested
        if node_ids is not None and concept_ids is not None:
            raise ValueError("chỉ truyền node_ids hoặc concept_ids")
        if n is not None and (type(n) is not int or not 1 <= n <= 10):
            raise ValueError("n phải từ 1 đến 10")
        if level and level not in {"nho", "hieu", "van_dung", "phan_tich", "danh_gia", "sang_tao"}:
            raise ValueError("level Bloom không hợp lệ")
        requested = node_ids if node_ids is not None else concept_ids
        concepts = self._concepts(module_id, requested)
        concepts = concepts[:n] if n is not None else concepts
        if dry_run:
            uncached = []
            estimated_input_tokens = estimated_output_tokens = estimated_calls = 0
            for concept in concepts:
                context = self._context(concept.get("module_id") or module_id, concept, level=level)
                key = self._bank_key(doc_id, concept.get("module_id") or module_id,
                                     concept, level, context=context)
                if self.store.get_cache(key) is not None:
                    continue
                uncached.append(concept)
                if self.model is None or self.verifier_model is None:
                    continue
                input_tokens, output_tokens = self._bank_estimate_tokens(context)
                estimated_input_tokens += input_tokens
                estimated_output_tokens += output_tokens
                estimated_calls += 4
            estimate = (estimated_input_tokens * PRICING_USD_PER_MILLION["input"]
                        + estimated_output_tokens * PRICING_USD_PER_MILLION["output"]) / 1_000_000
            return {"contract_version": "quiz-1", "status": "dry_run", "doc_id": doc_id,
                    "module_id": module_id, "total_concepts": len(concepts),
                    "estimated_usd": round(estimate, 6), "estimated_calls": estimated_calls,
                    "estimated_input_tokens": estimated_input_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                    "uncached_concepts": len(uncached),
                    "cost_basis": "upper bound: 4 calls per uncached concept, output caps from BSettings"}

        attempt_id = "qa_" + secrets.token_hex(12)
        started = time.perf_counter()
        completed = []
        failures = []
        usage = {"usd": 0.0, "ms": 0, "input_tokens": 0, "output_tokens": 0}

        def generate(concept):
            concept_module = concept.get("module_id") or module_id
            bank, cost = self._bank(doc_id, concept_module, concept, allow_spend, level)
            return concept, bank, cost

        with ThreadPoolExecutor(max_workers=max(1, min(8, len(concepts)))) as pool:
            futures = [pool.submit(generate, concept) for concept in concepts]
            for future in as_completed(futures):
                concept, bank, cost = future.result()
                for key in usage:
                    usage[key] += cost.get(key, 0)
                if not bank:
                    failures.append(concept["node_id"])
                    continue
                previous = [r for r in self.store.list_records("quiz_attempt", owner)
                            if r.get("doc_id") == doc_id and concept["node_id"] in r.get("concept_ids", [])]
                full = next((candidate for offset in range(len(bank))
                             for candidate in [bank[(len(previous) + offset) % len(bank)]]
                             if not any(self._duplicate(candidate, old[2]) for old in completed)), None)
                if full is None:
                    failures.append(concept["node_id"])
                    continue
                full = deepcopy(full)
                for index, option in enumerate(full["options"], 1):
                    option["option_id"] = f"o{index}"
                public = self._public_item(full)
                completed.append((concept.get("module_order", 0), public, full))
                if on_event:
                    with self._emit_lock:
                        on_event({"event": "item_ready", "attempt_id": attempt_id, "item": public})

        completed.sort(key=lambda row: row[0])
        fill_target = n if n is not None else 5 if module_id and len(concepts) in {3, 4} else 0
        if fill_target and len(completed) < fill_target:
            for order, public, full in list(completed):
                concept = next(c for c in concepts if c["node_id"] == public["concept_id"])
                concept_module = concept.get("module_id") or module_id
                bank, _ = self._bank(doc_id, concept_module, concept, allow_spend, level)
                alternate = next((candidate for candidate in bank if candidate["item_id"] != full["item_id"]
                                  and not any(self._duplicate(candidate, old[2]) for old in completed)), None)
                if alternate:
                    alternate = deepcopy(alternate)
                    for index, option in enumerate(alternate["options"], 1):
                        option["option_id"] = f"o{index}"
                    alternate_public = self._public_item(alternate)
                    completed.append((order, alternate_public, alternate))
                    if on_event:
                        on_event({"event": "item_ready", "attempt_id": attempt_id, "item": alternate_public})
                    if len(completed) == fill_target:
                        break
            completed.sort(key=lambda row: row[0])
        items = [public for _, public, _ in completed]
        private = {full["item_id"]: full for _, _, full in completed}
        usage["ms"] = round((time.perf_counter() - started) * 1000)
        attempt = {
            "contract_version": "quiz-1", "attempt_id": attempt_id, "owner": owner,
            "doc_id": doc_id, "module_id": module_id, "graph_version": graph_version, "origin": origin,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "ready" if items else "failed", "total_concepts": len(concepts),
            "ready_count": len(items), "concept_ids": [item["concept_id"] for item in items],
            "items": items, "_private": private, "answers": {}, "usage": usage,
            "failed_concepts": failures,
        }
        self.store.put_record("quiz_attempt", attempt_id, attempt)
        if on_event:
            on_event({"event": "done", "attempt_id": attempt_id, "status": attempt["status"],
                      "ready_count": len(items), "total_concepts": len(concepts)})
        return {key: value for key, value in attempt.items() if not key.startswith("_") and key != "answers"}

    def submit(self, attempt_id, owner, answers):
        attempt = self._owned_attempt(attempt_id, owner)
        if not isinstance(answers, dict):
            raise ValueError("answers phải là object")
        results, review, score = [], [], 0
        for public in attempt["items"]:
            item_id = public["item_id"]
            full = attempt["_private"][item_id]
            chosen_id = answers.get(item_id)
            answer = next(o for o in full["options"] if o.get("is_correct"))
            selected = next((o for o in full["options"] if o.get("option_id") == chosen_id), None)
            is_correct = bool(selected and selected.get("is_correct"))
            score += int(is_correct)
            result = {"item_id": item_id, "concept_id": public["concept_id"],
                      "selected_option_id": chosen_id, "is_correct": is_correct,
                      "correct_option": {"text": answer["text"], "evidence": answer.get("evidence", [])},
                      "stem": public["stem"], "evidence": full.get("evidence", []),
                      "explanation": full.get("explanation", "")}
            if not is_correct:
                result["why_wrong"] = selected.get("why_wrong", "") if selected else "Câu này chưa được trả lời."
                result["selected_evidence"] = selected.get("evidence", []) if selected else []
                review.append({"concept_id": public["concept_id"], "lecture_ref": {"node_id": public["concept_id"]}})
            results.append(result)
        submitted = {"submitted_at": datetime.now(timezone.utc).isoformat(), "answers": dict(answers),
                     "correct_count": score, "question_count": len(results), "results": results, "review": review}
        attempt["answers"] = dict(answers)
        attempt["submission"] = submitted
        self.store.put_record("quiz_attempt", attempt_id, attempt)
        return {"contract_version": "quiz-1", "attempt_id": attempt_id, "origin": attempt["origin"],
                "correct_count": score, "question_count": len(results), "results": results,
                "review": review, "submitted_at": submitted["submitted_at"]}

    def get_attempt(self, attempt_id, owner):
        """Return the saved answer-free quiz snapshot for a learner-owned attempt."""
        attempt = self._owned_attempt(attempt_id, owner)
        return {key: deepcopy(value) for key, value in attempt.items()
                if not key.startswith("_") and key not in {"answers", "submission"}}

    def history(self, owner, doc_id=None):
        attempts = []
        for row in self.store.list_records("quiz_attempt", owner):
            if doc_id is not None and row.get("doc_id") != doc_id:
                continue
            submission = row.get("submission")
            attempts.append({"attempt_id": row["attempt_id"], "doc_id": row["doc_id"],
                             "module_id": row["module_id"], "origin": row["origin"],
                             "created_at": row["created_at"],
                             "correct_count": submission.get("correct_count") if submission else None,
                             "question_count": submission.get("question_count", len(row["items"])) if submission else len(row["items"])})
        return {"contract_version": "quiz-1", "owner": owner, "attempts": attempts}

    def report_question(self, owner, attempt_id, item_id):
        attempt = self._owned_attempt(attempt_id, owner)
        if not any(item["item_id"] == item_id for item in attempt["items"]):
            raise KeyError(item_id)
        record = self.store.get_record("quiz_question_report", item_id) or {"reports": []}
        owners = {r["owner"] for r in record["reports"]}
        if owner not in owners:
            record["reports"].append({"owner": owner, "attempt_id": attempt_id, "item_id": item_id})
        self.store.put_record("quiz_question_report", item_id, record)
        threshold = self._setting("quiz_hide_report_threshold", 3)
        hidden = len({r["owner"] for r in record["reports"]}) >= threshold
        if hidden:
            self.store.put_record("quiz_hidden_question", item_id, {"item_id": item_id, "hidden": True})
        return {"contract_version": "quiz-1", "item_id": item_id,
                "report_count": len({r["owner"] for r in record["reports"]}), "hidden": hidden}

    def _resolve_scope(self, scope):
        if isinstance(scope, (list, tuple)):
            return None, list(scope)
        if scope in self.graph.modules:
            return scope, None
        normalized = self._norm(scope)
        for module_id, module in self.graph.modules.items():
            if normalized in {self._norm(module_id), self._norm(module.get("title", "")),
                              self._norm(str(module.get("index", "")))}:
                return module_id, None
        for node_id, node in self.graph.learnable_nodes.items() if hasattr(self.graph, "learnable_nodes") else self.graph.nodes.items():
            if normalized in {self._norm(node_id), *(self._norm(alias) for alias in self._aliases(node))}:
                return node.get("module_id"), [node_id]
        raise KeyError(scope)

    def _concepts(self, module_id, requested):
        module = self.graph.modules.get(module_id) if module_id is not None else None
        if module_id is not None and module is None:
            raise KeyError(module_id)
        ids = list(requested if requested is not None else module.get("node_ids", []))
        result = []
        for order, node_id in enumerate(ids):
            node = self.graph.nodes.get(node_id)
            if node and node.get("learnable", True):
                node_module = node.get("module_id")
                module_order = self.graph.modules.get(node_module, {}).get("index", order)
                result.append({**node, "node_id": node_id, "module_order": module_order})
        return result

    def _bank(self, doc_id, module_id, concept, allow_spend, level):
        context = self._context(module_id, concept, level=level)
        key = self._bank_key(doc_id, module_id, concept, level, context=context)
        cached = self.store.get_cache(key)
        if cached is not None:
            return [item for item in cached if not self._hidden(item["item_id"])], {}
        if self.model is None or not allow_spend:
            bank = self._cloze_bank(concept, context)
        else:
            try:
                generated = {}
                bank = self.store.single_flight(key, lambda: self._generate_bank(concept, context, generated, doc_id))
            except Exception:
                bank = []
            if not bank:
                bank = self._cloze_bank(concept, context)
        bank = [item for item in bank if not self._hidden(item["item_id"])]
        if bank:
            self.store.put_cache(key, bank)
        return bank, generated.get("usage", {}) if self.model is not None and allow_spend else {}

    def _bank_key(self, doc_id, module_id, concept, level, *, context=None):
        context = context or self._context(module_id, concept)
        config = {
            "model_id": getattr(self.model, "model_id", self._setting("model_id", "gemini-3.1-flash-lite")),
            "temperature": self._setting("quiz_temperature", 0.0),
            "generation_max_output_tokens": self._setting("quiz_generation_max_output_tokens", 1200),
            "verifier_max_output_tokens": self._setting("quiz_verifier_max_output_tokens", 400),
            "variant_count": self._setting("quiz_bank_variants", 2),
            "contract_version": "quiz-1",
        }
        value = {"doc_id": doc_id, "module_id": module_id, "node_id": concept["node_id"],
                 "context": self._prompt_context(context), "generation_prompt": "quiz-gen-v3", "verifier_prompt": "quiz-verify-v4",
                 "schema": "quiz-item-v1", "config": config, "level": level}
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

    def _context(self, module_id, concept, *, level=None):
        chunks = self._chunks_for(concept)
        node_type = str(concept.get("node_type", concept.get("kind", "concept"))).casefold()
        target_blooms = [level, level] if level else ["nho", "hieu"]
        if level is None and node_type in {"algorithm", "method", "metric"}:
            has_solved_example = any(
                "bai_tap" in str(self._get(chunk, "role", "")).casefold()
                and "loi_giai" in str(self._get(chunk, "text", "")).casefold()
                for chunk in chunks
            )
            target_blooms = ["hieu", "van_dung" if has_solved_example else "hieu"]
        source_registry = (self.graph.new_source_registry()
                           if hasattr(self.graph, "new_source_registry") else self.sources)
        source_chunks = []
        for index, chunk in enumerate(chunks, 1):
            chunk_id = self._get(chunk, "chunk_id", "")
            label = source_registry.label(chunk_id, "S") if source_registry else f"S{index}"
            source_chunks.append({"label": label, "chunk_id": chunk_id, "text": self._get(chunk, "text", ""),
                                  "page": self._get(chunk, "page"), "char_start": self._get(chunk, "char_start", 0),
                                  "char_end": self._get(chunk, "char_end", 0),
                                  "section_path": self._get(chunk, "section_path", [])})
        current_chunk_ids = {row["chunk_id"] for row in source_chunks}
        target_aliases = {self._norm(value) for value in [self._name(concept), *self._aliases(concept)]}
        eligible_distractors = []
        seen_distractor_chunks = set()
        for node in self._distractor_concepts(concept):
            anchor = node.get("anchor") or {}
            anchor_chunk = anchor.get("chunk_id")
            name_aliases = {self._norm(value) for value in [self._name(node), *self._aliases(node)]}
            if (not anchor_chunk or anchor_chunk not in self.graph.chunks or anchor_chunk in current_chunk_ids
                    or anchor_chunk in seen_distractor_chunks
                    or not anchor.get("sentence") or not name_aliases
                    or any(not value for value in name_aliases)
                    or any(a in b or b in a for a in target_aliases for b in name_aliases)):
                continue
            seen_distractor_chunks.add(anchor_chunk)
            eligible_distractors.append(node)
            if len(eligible_distractors) == 4:
                break
        distractor_candidates = []
        for index, node in enumerate(eligible_distractors, 1):
            anchor = node.get("anchor") or {}
            anchor_chunk = anchor.get("chunk_id")
            label = (source_registry.label(anchor_chunk, "D")
                     if source_registry and anchor_chunk in self.graph.chunks else f"D{index}")
            distractor_candidates.append({
                "label": label, "node_id": node.get("node_id"),
                "name": self._name(node), "aliases": node.get("aliases", []),
                "node_type": node.get("node_type"),
                "anchor": anchor.get("sentence", ""),
                "evidence_chunk_id": anchor.get("chunk_id"),
            })
        prerequisites = []
        if hasattr(self.graph, "traverse"):
            edges = self.graph.traverse(concept["node_id"], "requires", direction="in").get("edges", [])[:3]
            for edge in edges:
                row = dict(edge)
                chunk_id = next(iter(row.get("chunk_ids", [])), None)
                if source_registry and chunk_id in self.graph.chunks and row.get("quote"):
                    citation = source_registry.citation_for_chunk(chunk_id, "Q", row["quote"])
                    if citation:
                        row["source_label"], row["citation"] = citation
                prerequisites.append(row)
        exercises = []
        home = chunks[0] if chunks else None
        home_path = self._get(home, "section_path", []) if home else []
        for chunk in self.graph.chunks.values():
            if str(self._get(chunk, "role", "")).casefold() != "bai_tap":
                continue
            if home_path and self._get(chunk, "section_path", [])[:1] != home_path[:1]:
                continue
            if str(self._get(chunk, "text", "")).count("[formula]") >= 3:
                continue
            chunk_id = self._get(chunk, "chunk_id", "")
            label = source_registry.label(chunk_id, "B") if source_registry else f"B{len(exercises) + 1}"
            exercises.append({"label": label, "chunk_id": chunk_id, "text": self._get(chunk, "text", "")})
            if len(exercises) == 2:
                break
        module = self.graph.modules.get(module_id) if module_id else {"module_id": None, "title": "Conceptos"}
        return {"doc_id": self.graph.payload.get("doc_id", ""), "module": module,
                "concept": concept, "target_blooms": target_blooms, "chunks": source_chunks,
                "prerequisites": prerequisites, "distractor_candidates": distractor_candidates,
                "exercises": exercises, "_source_registry": source_registry,
                "limits": {"generation_output_tokens": self._setting("quiz_generation_max_output_tokens", 1200),
                           "verifier_output_tokens": self._setting("quiz_verifier_max_output_tokens", 400),
                           "explanation_chars": self._setting("quiz_explanation_max_chars", 300),
                           "why_wrong_chars": self._setting("quiz_why_wrong_max_chars", 150),
                           "bank_variants": self._setting("quiz_bank_variants", 2)}}

    def _generate_bank(self, concept, context, generated, doc_id):
        from doc2roadmap.application.phase_b.common import call_json

        base = self._generation_prompt(context)
        usage = {"usd": 0.0, "ms": 0, "input_tokens": 0, "output_tokens": 0}
        for repair in range(2):
            prompt = base if repair == 0 else base + "\nSinh lại các câu không qua luật. Câu lỗi trước: " + json.dumps(items, ensure_ascii=False)
            generated_call = call_json(self.model, prompt, response_schema=QUIZ_SCHEMA, store=self.store,
                                       purpose="quiz_gen", doc_id=doc_id,
                                       context_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                                       allow_spend=True, settings=self.settings)
            self._add_call_usage(usage, generated_call)
            candidates = generated_call.payload.get("items", []) if isinstance(generated_call.payload, dict) else []
            items = [self._normalize_item(concept, context, raw) for raw in candidates]
            items = [item for item in items if item and self._rules_pass(item, context)]
            for index, item in enumerate(items[:2]):
                item["bloom"] = context["target_blooms"][index]
            if len(items) > 1:
                first = items[0]
                answer = next(o["text"] for o in first["options"] if o["is_correct"])
                items = [first] + [item for item in items[1:]
                                    if not self._duplicate(first, item)
                                    and (first["bloom"] != item["bloom"]
                                         or answer != next(o["text"] for o in item["options"] if o["is_correct"]))]
            if not items:
                continue
            labels, choices = [], {}
            for item in items:
                options = list(item["options"])
                self.rng.shuffle(options)
                choices[item["item_id"]] = options
                labels.append({"item_id": item["item_id"], "stem": item["stem"],
                               "options": [{"option_id": str(i), "text": o["text"]} for i, o in enumerate(options)]})
            verifier_prompt = self._verifier_prompt(context, labels)
            verified = call_json(self.verifier_model, verifier_prompt, response_schema=VERIFIER_SCHEMA, store=self.store,
                                 purpose="quiz_verify", doc_id=doc_id,
                                 context_hash=hashlib.sha256(verifier_prompt.encode()).hexdigest(),
                                 allow_spend=True, settings=self.settings)
            self._add_call_usage(usage, verified)
            accepted = set()
            for result in verified.payload.get("items", []) if isinstance(verified.payload, dict) else []:
                item = next((it for it in items if it["item_id"] == result.get("item_id")), None)
                options = choices.get(result.get("item_id"), [])
                selected = next((o for i, o in enumerate(options) if str(i) == result.get("selected_option_id")), None)
                verdicts = result.get("distractor_verdicts", [])
                verdict_values = [v.get("verdict", "") for v in verdicts if isinstance(v, dict)]
                verdict_values.extend(v for v in verdicts if isinstance(v, str))
                verdict_by_option = {v.get("option_id"): v.get("verdict", "") for v in verdicts if isinstance(v, dict)}
                correct_position = next((str(i) for i, option in enumerate(options) if option.get("is_correct")), None)
                complete_distractor_verdicts = (
                    set(verdict_by_option) >= {str(i) for i in range(len(options)) if str(i) != correct_position}
                    and all("sai theo nguồn" in verdict_by_option[str(i)].casefold()
                            for i in range(len(options)) if str(i) != correct_position)
                )
                if (item and selected and selected.get("is_correct") and result.get("valid") is True
                        and self._quote_found(result.get("quote", ""), context, current_only=True)
                        and complete_distractor_verdicts
                        and not any("đúng theo nguồn" in v.casefold() or "nguồn không nói" in v.casefold()
                                    for v in verdict_values)):
                    item["checks"]["verifier"] = "pass"
                    accepted.add(item["item_id"])
            if accepted:
                generated["usage"] = usage
                return [item for item in items if item["item_id"] in accepted][:2]
        generated["usage"] = usage
        return []

    @staticmethod
    def _generation_prompt(context):
        context = QuizUseCase._prompt_context(context)
        limits = context["limits"]
        return ("Tạo tối đa 2 câu trắc nghiệm tiếng Việt cho một khái niệm, mỗi câu phải có đúng 3 phương án: "
                "một correct và đúng hai distractors. Chỉ dùng căn cứ trong chunks. "
                "Trong correct.sources và distractors[].sources, chỉ ghi nhãn nguồn ngắn (ví dụ S1, D1) "
                "đã có trong context; tuyệt đối không ghi chunk_id hay ID nội bộ. "
                "Mỗi correct.quote và distractor.quote phải là trích dẫn nguyên văn tối đa 200 ký tự "
                "từ chính nguồn được ghi. Mỗi why_wrong tối đa " + str(limits["why_wrong_chars"]) + " ký tự; "
                "explanation tối đa " + str(limits["explanation_chars"]) + " ký tự. "
                "Nếu option lấy từ distractor_candidates thì from phải đúng bằng D-label đó, sources phải chỉ chứa "
                "chính D-label ấy, và quote phải nằm trong anchor của candidate. Nếu không có candidate phù hợp "
                "hoặc option suy ra từ chunks của khái niệm hiện tại, dùng from='moi', sources chỉ chứa S-label, "
                "và quote phải nằm trong chunk S ấy. Không chọn option có tên trùng/bao chứa alias đáp án; "
                "không để text của một option chứa text option khác theo bất kỳ chiều nào. "
                "Độ dài đáp án không được vượt 1.3 lần trung bình độ dài hai nhiễu khi đáp án là option dài nhất. "
                "Gán bloom theo target_blooms. Không dùng công thức làm phương án. "
                "Trả JSON theo schema, dạng {items:[...],gaps:[...]}.\n"
                + json.dumps(context, ensure_ascii=False, default=str))

    @staticmethod
    def _prompt_context(context):
        return {key: value for key, value in context.items() if not key.startswith("_")}

    @staticmethod
    def _verifier_prompt(context, labels):
        return (VERIFIER_INSTRUCTIONS + "\n"
                + json.dumps({"chunks": context["chunks"],
                              "distractor_sources": context["distractor_candidates"],
                              "items": labels}, ensure_ascii=False))

    def _bank_estimate_tokens(self, context):
        """Bound two variants plus one repair and blind-verifier retry."""
        generation_cap = self._setting("quiz_generation_max_output_tokens", 1200)
        verifier_cap = self._setting("quiz_verifier_max_output_tokens", 400)
        schema_tokens = lambda schema: math.ceil(len(json.dumps(schema, ensure_ascii=False, sort_keys=True)) / 3)
        generation_tokens = math.ceil(len(self._generation_prompt(context)) / 3) + schema_tokens(QUIZ_SCHEMA)

        verifier_payload = {"chunks": context["chunks"],
                            "distractor_sources": context["distractor_candidates"], "items": []}
        verifier_prefix = VERIFIER_INSTRUCTIONS + "\n"
        verifier_tokens = (math.ceil((len(verifier_prefix) + len(json.dumps(verifier_payload, ensure_ascii=False))) / 3)
                           + generation_cap + schema_tokens(VERIFIER_SCHEMA))
        # Two generation attempts; the repair may include the entire preceding capped reply.
        # Each verifier call may also receive a max-sized generated reply.
        return (2 * generation_tokens + generation_cap + 2 * verifier_tokens,
                2 * generation_cap + 2 * verifier_cap)

    @staticmethod
    def _add_call_usage(total, result):
        total["usd"] += result.cost_usd
        total["ms"] += result.elapsed_ms
        total["input_tokens"] += result.usage.get("input_tokens", result.usage.get("promptTokenCount", 0))
        total["output_tokens"] += result.usage.get("output_tokens", result.usage.get("candidatesTokenCount", 0))

    def _normalize_item(self, concept, context, raw):
        try:
            if self._norm(raw["concept"]) not in {
                self._norm(value) for value in [self._name(concept), *self._aliases(concept)]
            }:
                return None
            correct = raw["correct"]
            correct_sources = correct.get("sources", [])
            correct_source = next((label for label in correct_sources
                                   if self._quote_for_label(correct.get("quote", ""), label, context,
                                                            correct=True)), None)
            if correct_source is None:
                return None
            correct_chunk = next(row["chunk_id"] for row in context["chunks"] if row["label"] == correct_source)
            options = [{"text": correct["text"].strip(), "is_correct": True, "why_wrong": ""}]
            options.extend({"text": d["text"].strip(), "is_correct": False,
                            "why_wrong": d.get("why_wrong", "")[:self._setting("quiz_why_wrong_max_chars", 150)],
                            "sources": d.get("sources", []), "quote": d.get("quote", ""), "from": d.get("from")}
                           for d in raw["distractors"])
            if len(options) != 3:
                return None
            if any(not option.get("sources") or not option.get("quote")
                   or not any(self._quote_for_label(option["quote"], label, context)
                              for label in option["sources"])
                   for option in options[1:]):
                return None
            evidence = [self._citation(context, correct_source, correct["quote"])]
            for option in options[1:]:
                source = next(label for label in option["sources"]
                              if self._quote_for_label(option["quote"], label, context))
                source_candidate = next((row for row in context.get("distractor_candidates", [])
                                         if row["label"] == source), None)
                declared_from = option.get("from")
                if declared_from in {row["label"] for row in context.get("distractor_candidates", [])}:
                    if declared_from != source or source_candidate is None:
                        return None
                    if source_candidate.get("evidence_chunk_id") == correct_chunk:
                        return None
                elif declared_from == "moi":
                    if source not in {row["label"] for row in context["chunks"]}:
                        return None
                else:
                    return None
                option["sources"] = [source]
                option["evidence"] = [self._citation(context, source, option["quote"])]
            stem = raw["stem"].strip()
            item_id = "qi_" + hashlib.sha256((concept["node_id"] + stem + "|".join(o["text"] for o in options)).encode()).hexdigest()[:24]
            return {"item_id": item_id, "concept_id": concept["node_id"], "module_id": context["module"]["module_id"],
                    "generator": "llm", "bloom": raw.get("bloom", "hieu"), "stem": stem, "options": options,
                    "explanation": raw.get("explanation", "")[:self._setting("quiz_explanation_max_chars", 300)], "evidence": evidence,
                    "formula_refs": raw.get("formula_refs", []),
                    "checks": {"rules_passed": [], "verifier": "pending", "flags": []}}
        except (KeyError, TypeError, IndexError):
            return None

    def _rules_pass(self, item, context):
        options = item["options"]
        texts = [self._norm(o["text"]) for o in options]
        correct = next((o for o in options if o["is_correct"]), None)
        if not correct or len(set(texts)) != 3:
            return False
        if any(a in b or b in a for i, a in enumerate(texts) for b in texts[i + 1:] if a and b):
            return False
        aliases = {self._norm(x) for x in [self._name(context["concept"]), *self._aliases(context["concept"])]}
        if any(self._norm(o["text"]) in aliases for o in options if not o["is_correct"]):
            return False
        answer_len = len(correct["text"])
        distractor_mean = sum(len(o["text"]) for o in options if not o["is_correct"]) / 2
        if answer_len > 1.3 * distractor_mean and answer_len == max(map(lambda o: len(o["text"]), options)):
            return False
        stem = item["stem"].casefold()
        if any(term in stem for term in ("tất cả đáp án", "không có đáp án", " ngoại trừ", "không phải")):
            return False
        if any(term in " ".join(texts) for term in ("luôn luôn", "không bao giờ")):
            return False
        content_stops = {"một", "những", "các", "là", "của", "và", "trong", "được", "gọi", "nào", "gì",
                         "theo", "với", "khi", "cho", "từ", "đến", "có", "không", "về", "mỗi", "này", "đó"}
        stem_words = set(re.findall(r"[^\W_]+", stem)) - content_stops
        answer_words = set(re.findall(r"[^\W_]+", self._norm(correct["text"]))) - content_stops
        distractor_words = set().union(*(set(re.findall(r"[^\W_]+", self._norm(o["text"]))) - content_stops
                                         for o in options if not o["is_correct"]))
        if (stem_words & answer_words) - distractor_words:
            return False
        text = stem + " " + " ".join(texts)
        if "```" in text or "**" in text or "__" in text or re.search(r"^\s*(?:câu hỏi:|[SDK]\d+:|K\d+:)", text, re.I | re.M):
            return False
        if re.search(r"\b(?:hình|bảng)\s+\d+\b|\bđồ thị\b|\bhình vẽ\b|\[formula\]|\[CT[^\]]+\]|\bCT\w+\b", text, re.I):
            return False
        if any(re.search(r"\[formula\]|\[CT[^\]]+\]|\bCT\w+\b|[=∑∫√^_×÷±≤≥<>]", option["text"], re.I)
               for option in options):
            return False
        if (len(item.get("explanation", "")) > self._setting("quiz_explanation_max_chars", 300)
                or any(len(o.get("why_wrong", "")) > self._setting("quiz_why_wrong_max_chars", 150)
                       for o in options)):
            return False
        if self._name(context["concept"]).casefold() in stem:
            return False
        source = " ".join(c["text"] for c in context["chunks"])
        if not self._math_from_source(text, source):
            return False
        minimum_vietnamese = min(0.25, self._vietnamese_ratio(source) * 0.5)
        language_texts = [item["stem"], item.get("explanation", ""),
                          *(option.get("why_wrong", "") for option in options if not option["is_correct"])]
        return all(self._vietnamese_ratio(value) >= minimum_vietnamese for value in language_texts if value.strip())

    def _duplicate(self, first, second):
        def grams(item):
            text = self._norm(item["stem"] + " " + next(o["text"] for o in item["options"] if o["is_correct"]))
            words = text.split()
            return {" ".join(words[i:i + 3]) for i in range(max(1, len(words) - 2))}
        left, right = grams(first), grams(second)
        return bool(left and right and len(left & right) / len(left | right) >= 0.6)

    def _cloze_bank(self, concept, context):
        name = self._name(concept)
        if not name:
            return []
        anchor = concept.get("anchor") or {}
        anchor_chunk_id = anchor.get("chunk_id")
        anchor_sentence = anchor.get("sentence", "")
        match = next(((chunk, chunk["text"]) for chunk in context["chunks"]
                      if chunk["chunk_id"] == anchor_chunk_id
                      and anchor_sentence and re.search(re.escape(name), anchor_sentence, re.I)
                      and self._quote_found(anchor_sentence, {"chunks": [chunk]}, current_only=True)), None)
        if not match:
            return []
        chunk, text = match
        aliases = [name, *self._aliases(concept)]
        target_aliases = {self._norm(a) for a in aliases}
        distractors = []
        for candidate in self._distractor_concepts(concept):
            candidate_aliases = [self._name(candidate), *self._aliases(candidate)]
            if {self._norm(a) for a in candidate_aliases} & target_aliases:
                continue
            candidate_name = self._name(candidate)
            if candidate_name and self._norm(candidate_name) not in {self._norm(a) for a in distractors}:
                distractors.append(candidate_name)
        if len(distractors) < 2:
            for candidate in self.graph.nodes.values():
                candidate_name = self._name(candidate)
                if (candidate.get("module_id") == concept.get("module_id") and candidate_name
                        and candidate.get("node_id") != concept["node_id"]
                        and self._norm(candidate_name) not in target_aliases
                        and self._norm(candidate_name) not in {self._norm(a) for a in distractors}):
                    distractors.append(candidate_name)
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
        result = []
        for quote in sentences:
            stem_quote = self._blank_concept_aliases(quote, aliases, name)
            if stem_quote == quote:
                continue
            if len(stem_quote) < 25:
                continue
            choices = self._balanced_distractors(name, distractors)
            if not choices:
                continue
            evidence = self._raw_citation(chunk, quote)
            item_id = "qi_" + hashlib.sha256((concept["node_id"] + quote).encode()).hexdigest()[:24]
            options = [{"text": name, "is_correct": True, "why_wrong": "", "evidence": [evidence]}]
            options.extend({"text": value, "is_correct": False,
                            "why_wrong": f"Tài liệu không xác định {value} trong câu trích này.", "evidence": []}
                           for value in choices)
            result.append({"item_id": item_id, "concept_id": concept["node_id"], "module_id": context["module"]["module_id"],
                           "generator": "cloze", "bloom": "nho",
                           "stem": "Câu sau trích từ tài liệu nói về khái niệm nào?\n\n" + stem_quote,
                           "options": options, "explanation": "Câu trích nêu trực tiếp tên khái niệm.",
                           "evidence": [evidence], "formula_refs": [],
                           "checks": {"rules_passed": ["Q1", "Q2", "Q3", "Q5", "Q6", "Q8"],
                                      "verifier": "not_required", "flags": []}})
            if len(result) == 2:
                break
        return result

    def _blank_concept_aliases(self, text, aliases, name):
        occurrences = []
        for alias in set(aliases):
            if not alias:
                continue
            pattern = re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.I)
            occurrences.extend((match.start(), match.end(), match.group()) for match in pattern.finditer(text))
        selected = []
        for start, end, value in sorted(occurrences, key=lambda row: (-(row[1] - row[0]), row[0])):
            if any(start < prior_end and end > prior_start for prior_start, prior_end, _ in selected):
                continue
            # "Hiệu" is a homonym in the Vietnamese compound "kí/ký hiệu".
            # A quiz must not teach that notation phrase as the concept "Hiệu".
            if (self._norm(name) == "hiệu"
                    and re.search(r"(?:kí|ký)\s+$", text[max(0, start - 12):start], re.I)):
                continue
            selected.append((start, end, value))
        if not selected:
            return text
        result, offset = [], 0
        for start, end, _ in sorted(selected):
            result.extend((text[offset:start], "___"))
            offset = end
        result.append(text[offset:])
        return "".join(result)

    @staticmethod
    def _balanced_distractors(answer, candidates):
        for index, first in enumerate(candidates):
            for second in candidates[index + 1:]:
                wrong_mean = (len(first) + len(second)) / 2
                if not (len(answer) > 1.3 * wrong_mean and len(answer) == max(len(answer), len(first), len(second))):
                    return [first, second]
        return []

    def _distractor_concepts(self, concept):
        candidates = []
        for edge in self.graph.payload.get("open_edges", []) + self.graph.payload.get("recommended_edges", []):
            if (edge.get("edge_type") in {"contrasts_with", "subtype_of", "component_of"}
                    and not edge.get("soft_reason")):
                other = edge.get("target") if edge.get("source") == concept["node_id"] else edge.get("source") if edge.get("target") == concept["node_id"] else None
                target = self.graph.nodes.get(other)
                if target and target.get("learnable", True):
                    candidates.append(target)
        for node_id in self.graph.modules.get(concept.get("module_id"), {}).get("node_ids", []):
            if node_id != concept["node_id"] and node_id in self.graph.nodes:
                candidates.append(self.graph.nodes[node_id])
        cluster = concept.get("cluster_id", concept.get("cluster"))
        if cluster is not None:
            for node in self.graph.learnable_nodes.values() if hasattr(self.graph, "learnable_nodes") else self.graph.nodes.values():
                if node.get("node_id") != concept["node_id"] and node.get("cluster_id", node.get("cluster")) == cluster:
                    candidates.append(node)
        module_index = self.graph.modules.get(concept.get("module_id"), {}).get("index", 0)
        for module in sorted(self.graph.modules.values(), key=lambda row: row.get("index", 0)):
            if module.get("index", 0) >= module_index:
                continue
            for node_id in module.get("node_ids", []):
                node = self.graph.nodes.get(node_id)
                if node and node.get("learnable", True):
                    candidates.append(node)
        out, seen = [], set()
        for node in candidates:
            if node.get("node_id") not in seen:
                seen.add(node.get("node_id")); out.append(node)
        return out

    def _chunks_for(self, concept):
        ids = concept.get("teaching_chunk_ids") or concept.get("defining_chunk_ids") or []
        chunks = [self.graph.chunks[i] for i in ids if i in self.graph.chunks]
        anchor_chunk = (concept.get("anchor") or {}).get("chunk_id")
        if anchor_chunk in self.graph.chunks and all(self._get(chunk, "chunk_id") != anchor_chunk for chunk in chunks):
            chunks.append(self.graph.chunks[anchor_chunk])
        if not chunks:
            module_id = concept.get("module_id")
            mapping = getattr(self.graph, "_chunk_modules", {})
            if not mapping:
                mapping = {}
                for chunk_id, row in self.graph.payload.get("chunk_module_map", {}).items():
                    module_ids = row.get("all_module_ids") or ([row.get("module_id")] if row.get("module_id") else []) if isinstance(row, dict) else [row]
                    mapping[chunk_id] = module_ids
            allowed = {chunk_id for chunk_id, module_ids in mapping.items()
                       if module_id in (module_ids if isinstance(module_ids, list) else [module_ids])}
            names = [self._name(concept), *self._aliases(concept)]
            chunks = [chunk for chunk_id, chunk in self.graph.chunks.items() if chunk_id in allowed
                      if any(n and re.search(re.escape(n), self._get(chunk, "text", ""), re.I) for n in names)]
        return chunks[:8]

    def _citation(self, context, label, quote):
        sources = context.get("_source_registry") or self.sources
        if sources and label:
            try:
                return sources.citation(label, quote)
            except (KeyError, ValueError):
                pass
        chunk = next((c for c in context["chunks"] if c["chunk_id"] == label or c["label"] == label), None)
        if chunk is None:
            candidate = next((row for row in context.get("distractor_candidates", []) if row["label"] == label), None)
            if candidate:
                chunk = self.graph.chunks.get(candidate.get("evidence_chunk_id"))
                if chunk:
                    citation = self._raw_citation(chunk, quote)
                    citation["label"] = label
                    return citation
        return self._raw_citation(chunk, quote) if chunk else {"label": label, "quote": quote}

    def _quote_for_label(self, quote, label, context, *, correct=False):
        from doc2roadmap.application.phase_b.common import quote_is_verbatim

        label = str(label)
        source = next((row["text"] for row in context["chunks"] if row["label"] == label), None)
        if source is None and not correct:
            source = next((row["anchor"] for row in context.get("distractor_candidates", [])
                           if row["label"] == label), None)
        if source is None and not correct:
            source = next((row["text"] for row in context.get("exercises", []) + context.get("prerequisites", [])
                           if row.get("label") == label), None)
        return bool(source and quote_is_verbatim(quote, source, max_chars=200))

    def _raw_citation(self, chunk, quote):
        text = self._get(chunk, "text", "")
        start = text.find(quote) if quote else -1
        return {"label": self._get(chunk, "label", "S"), "chunk_id": self._get(chunk, "chunk_id", ""),
                "page": self._get(chunk, "page"), "section_path": self._get(chunk, "section_path", []),
                "char_start": self._get(chunk, "char_start", 0) + max(start, 0),
                "char_end": self._get(chunk, "char_start", 0) + max(start, 0) + len(quote), "quote": quote}

    @staticmethod
    def _quote_found(quote, context, *, current_only=False):
        q = " ".join(unicodedata.normalize("NFC", quote or "").split())
        sources = [c["text"] for c in context["chunks"]]
        if not current_only:
            sources.extend(item.get("anchor", "") for item in context.get("distractor_candidates", []))
            sources.extend(item.get("quote", "") for item in context.get("prerequisites", []))
            sources.extend(item.get("text", "") for item in context.get("exercises", []))
        return bool(q and any(q in " ".join(unicodedata.normalize("NFC", text).split()) for text in sources))

    def _public_item(self, item):
        public = {k: v for k, v in item.items() if k not in {"explanation", "evidence", "formula_refs", "checks"} and not k.startswith("_")}
        options = deepcopy(item["options"])
        self.rng.shuffle(options)
        public["options"] = []
        for option in options:
            public["options"].append({"option_id": option["option_id"], "text": option["text"]})
        return public

    def _owned_attempt(self, attempt_id, owner):
        attempt = self.store.get_record("quiz_attempt", attempt_id)
        if attempt is None or attempt.get("owner") != owner:
            raise KeyError(attempt_id)
        return attempt

    def _hidden(self, item_id):
        return bool(self.store.get_record("quiz_hidden_question", item_id))

    def _setting(self, name, default):
        return self.settings.get(name, default) if isinstance(self.settings, dict) else getattr(self.settings, name, default) if self.settings else default

    def _name(self, node):
        return node.get("display_name") or node.get("name") or node.get("raw_name") or ""

    @staticmethod
    def _aliases(node):
        raw = list(node.get("aliases", []) or []) + list(node.get("identity_aliases", []) or [])
        aliases = []
        for item in raw:
            if isinstance(item, dict):
                for key in ("display_name", "name", "raw_name", "alias"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        aliases.append(value.strip())
            elif isinstance(item, str) and item.strip():
                aliases.append(item.strip())
        return list(dict.fromkeys(aliases))

    @staticmethod
    def _get(obj, key, default=None):
        return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

    @staticmethod
    def _norm(text):
        return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())

    @staticmethod
    def _math_from_source(text, source):
        pattern = r"[α-ωΑ-Ω∑∏√∞≤≥≠≈∈∉⊂⊆→⇒×÷±^_=<>+*/-]|\b\d+(?:\.\d+)?\b"
        return set(re.findall(pattern, text)) <= set(re.findall(pattern, source))

    @staticmethod
    def _vietnamese_ratio(text):
        tokens = re.findall(r"[^\W_]+", unicodedata.normalize("NFC", str(text)))
        if not tokens:
            return 0.0
        marks = set("\u0300\u0301\u0303\u0309\u0323\u0302\u0306\u031b")
        return sum(any(char in marks for char in unicodedata.normalize("NFD", token))
                   for token in tokens) / len(tokens)
