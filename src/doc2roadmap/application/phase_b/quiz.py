from __future__ import annotations

import hashlib
import json
import random
import re
import secrets
import threading
import time
import unicodedata
from copy import deepcopy
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from doc2roadmap.application.phase_b.common import call_json
from doc2roadmap.application.phase_b.lecture3 import IMAGE_TOKEN_ESTIMATE
from doc2roadmap.application.phase_b.quiz_context3 import (
    GENERATION_SCHEMA, GENERATION_TEMPERATURE, SOLVER_SCHEMA, SOLVER_TEMPERATURE, SYSTEM_SOLVER,
    build_item, build_material, generation_system, solver_message, verdicts,
)
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.phase_b_pricing import estimate_cost


CLOZE_VISUAL_OR_FORMULA_REFERENCE = re.compile(
    r"\[formula\]|\[CT[^\]]+\]|\bCT\w+\b|\b(?:hình|bảng)\s+(?:số\s+)?\d+\b|"
    r"\b(?:hình|bảng)\s+(?:sau|dưới|trên)(?:\s+đây)?\b|\bhình vẽ\b|"
    r"\bđồ thị\s+(?:sau|dưới|trên)(?:\s+đây)?\b",
    re.I,
)
INCOMPLETE_CLOZE_LEAD_IN = re.compile(
    r"\b(?:điều kiện|tính chất|quy tắc|các bước|công thức|tiêu chí|định nghĩa|yếu tố|nguyên tắc)\s+"
    r"(?:sau đây|dưới đây|như sau)\s*[:.!?…]*\s*$|"
    r"\b(?:là\s+)?(?:tập hợp|biểu thức|công thức)\s+sau đây\s*[:.!?…]*\s*$",
    re.I,
)
# Q6: options are never formulas or notation.
CLOZE_NOTATION = re.compile(r"[×=∪∩∈∉∑∫√≤≥≠±→⊂⊃⊆^]")
# A cloze sentence with maths in it cannot be read without the formula: any of these symbols, or a digit next to a letter.
CLOZE_MATH = re.compile(r"[=<>+*/^_\|{}\[\]×÷±∑∏∫√∞≤≥≠≈∈∉⊂⊃⊆∪∩→⇒α-ωΑ-Ω]|\d[^\W\d_]|[^\W\d_]\d")


class QuizUseCase:
    """Build, submit, and review self-check quizzes without tracking mastery."""

    LOCAL_RULES_VERSION = "quiz-local-rules-v5"

    def __init__(self, graph, store, model=None, *, verifier_model=None, settings=None,
                 source_registry=None, rng=None, progress_use_case=None, spend_guard=None, clock=None,
                 page_images=None):
        self.graph = graph
        self.store = store
        self.model = model
        self.verifier_model = verifier_model or model
        self.settings = settings
        self.sources = source_registry or (graph.new_source_registry() if hasattr(graph, "new_source_registry") else None)
        self.rng = rng or random.Random()
        self.progress_use_case = progress_use_case
        self.spend_guard = spend_guard
        self.clock = clock
        self.page_images = page_images
        self._emit_lock = threading.Lock()
        self._rng_lock = threading.Lock()
        self.diagnostics = []
        self._diagnostics_lock = threading.Lock()

    def _record_rejection(self, stage, reason, concept, raw=None, item=None):
        raw = raw or {}
        correct = raw.get("correct", {}) if isinstance(raw, dict) else {}
        distractors = raw.get("distractors", []) if isinstance(raw, dict) else []
        if item and not correct:
            correct = next((option for option in item.get("options", []) if option.get("is_correct")), {})
        if item and not distractors:
            distractors = [option for option in item.get("options", []) if not option.get("is_correct")]
        row = {
            "stage": stage,
            "reason": reason,
            "concept_id": concept.get("node_id"),
            "concept_name": self._name(concept),
            "item_id": (item or {}).get("item_id") or raw.get("item_id"),
            "candidate": {
                "stem": str((item or raw).get("stem", ""))[:500],
                "correct": str(correct.get("text", ""))[:120],
                "correct_sources": list(correct.get("sources", []))[:4],
                "distractors": [{
                    "text": str(option.get("text", ""))[:120],
                    "from": option.get("from"),
                    "sources": list(option.get("sources", []))[:4],
                    "quote": str(option.get("quote", ""))[:200],
                } for option in distractors[:3] if isinstance(option, dict)],
            },
        }
        with self._diagnostics_lock:
            self.diagnostics.append(row)

    def make_quiz(self, doc_id=None, module_id=None, owner=None, *, scope=None, graph=None,
                  graph_version=None, origin="button", n=None,
                  node_ids=None, concept_ids=None, level=None, allow_spend=False,
                  dry_run=False, on_event=None, home_scope=None, session_id=None, seed=None):
        if not doc_id or not owner:
            raise ValueError("doc_id và owner là bắt buộc")
        if getattr(self.graph, 'doc_id', None) and self.graph.doc_id != doc_id:
            raise ValueError('doc_id does not match graph')
        if origin not in {"button", "assistant"}:
            raise ValueError("origin không hợp lệ")
        if origin == 'button':
            session_id = None
        roadmap_scope = (isinstance(scope, dict) and scope.get("kind") == "roadmap"
                         or isinstance(scope, str) and self._norm(scope) == "roadmap")
        saved_scope = home_scope or (scope if isinstance(scope, dict) and scope.get("kind") in {"roadmap", "module"}
                                     else None)
        if scope is not None:
            if module_id is not None or node_ids is not None or concept_ids is not None:
                raise ValueError("scope không thể đi cùng module_id hoặc node_ids")
            if roadmap_scope:
                module_id, requested = None, None
            elif isinstance(scope, dict) and scope.get("kind") == "module":
                from doc2roadmap.domain.scope import resolve_scope
                resolved = resolve_scope(scope, self.graph, self._setting("scope_remap_min_jaccard", 0.5))
                module_id = resolved["module_id"]
                requested = list(scope.get("node_ids", [])) if resolved["stale"] else None
            else:
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
        roadmap_cap = None
        if roadmap_scope:
            roadmap_cap = min(n if n is not None else self._setting("quiz_roadmap_max_items", 10),
                              self._setting("quiz_roadmap_max_items", 10), 10)
            selected_seed = str(seed if seed is not None else secrets.token_hex(8))
            concepts = self._roadmap_sample(concepts, owner, doc_id, roadmap_cap, selected_seed)
        else:
            selected_seed = str(seed if seed is not None else "")
            concepts = concepts[:n] if n is not None else concepts
        if dry_run:
            uncached = []
            estimated_input_tokens = estimated_output_tokens = estimated_calls = 0
            generation_input_tokens = generation_output_tokens = 0
            verifier_input_tokens = verifier_output_tokens = 0
            for concept in concepts:
                material = self._material(concept)
                key = self._bank_key(doc_id, concept.get("module_id") or module_id, concept, level, material=material)
                if self.store.get_cache(key) is not None:
                    continue
                uncached.append(concept)
                if self.model is None or self.verifier_model is None or not material.chunks:
                    continue
                gen_input, gen_output, verify_input, verify_output = self._bank_estimate_token_breakdown(material)
                generation_input_tokens += gen_input
                generation_output_tokens += gen_output
                verifier_input_tokens += verify_input
                verifier_output_tokens += verify_output
                estimated_input_tokens += gen_input + verify_input
                estimated_output_tokens += gen_output + verify_output
                estimated_calls += 4
            settings_model_id = self._setting("model_id", "gemini-3.1-flash-lite")
            generator_id = getattr(self.model, "model_id", settings_model_id)
            verifier_id = getattr(self.verifier_model, "model_id", settings_model_id)
            estimate = (estimate_cost(generator_id, generation_input_tokens, generation_output_tokens)
                        + estimate_cost(verifier_id, verifier_input_tokens, verifier_output_tokens))
            return {"contract_version": self._setting("quiz_contract_version", "quiz-3"), "status": "dry_run", "doc_id": doc_id,
                    "module_id": module_id, "total_concepts": len(concepts),
                    "estimated_usd": round(estimate, 6), "estimated_calls": estimated_calls,
                    "estimated_input_tokens": estimated_input_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                    "uncached_concepts": len(uncached),
                    "cost_basis": "upper bound: 4 calls per uncached concept (two laps), output caps from BSettings"}

        attempt_id = "qa_" + secrets.token_hex(12)
        started = time.perf_counter()
        completed = []
        failures = []
        usage = {"usd": 0.0, "ms": 0, "input_tokens": 0, "output_tokens": 0}

        def generate(concept):
            concept_module = concept.get("module_id") or module_id
            bank, cost = self._bank(doc_id, concept_module, concept, allow_spend, level, owner=owner)
            return concept, bank, cost

        with ThreadPoolExecutor(max_workers=max(1, min(self._settings().quiz_parallel_concepts, len(concepts)))) as pool:
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
        fill_target = (0 if roadmap_scope else
                       n if n is not None else 5 if module_id and len(concepts) in {3, 4} else 0)
        if fill_target and len(completed) < fill_target:
            for order, public, full in list(completed):
                concept = next(c for c in concepts if c["node_id"] == public["concept_id"])
                concept_module = concept.get("module_id") or module_id
                bank, _ = self._bank(doc_id, concept_module, concept, allow_spend, level, owner=owner)
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
        node_ids = list(dict.fromkeys(item[1]["concept_id"] for item in completed))
        if saved_scope is None:
            if module_id is None:
                saved_scope = {"kind": "roadmap"}
            else:
                saved_scope = {"kind": "module",
                               "node_ids": list(self.graph.modules[module_id].get("node_ids", [])),
                               "module_id_at_creation": module_id,
                               "graph_version_at_creation": getattr(self.graph, "graph_version", graph_version)}
        attempt = {
            "contract_version": self._setting("quiz_contract_version", "quiz-3"), "attempt_id": attempt_id, "owner": owner,
            "doc_id": doc_id, "module_id": module_id, "graph_version": graph_version, "origin": origin,
            "home_scope": saved_scope, "session_id": session_id, "node_ids": node_ids,
            "seed": selected_seed or None,
            "created_at": self.clock.now().isoformat() if self.clock else datetime.now(timezone.utc).isoformat(),
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
        if self.progress_use_case is not None:
            correct_node_ids = [result["concept_id"] for result in results if result["is_correct"]]
            if correct_node_ids:
                self.progress_use_case.mark_quiz_correct(owner, attempt["doc_id"], correct_node_ids)
        return {"contract_version": self._setting("quiz_contract_version", "quiz-3"), "attempt_id": attempt_id, "origin": attempt["origin"],
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
        return {"contract_version": self._setting("quiz_contract_version", "quiz-3"), "owner": owner, "attempts": attempts}

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
        return {"contract_version": self._setting("quiz_contract_version", "quiz-3"), "item_id": item_id,
                "report_count": len({r["owner"] for r in record["reports"]}), "hidden": hidden}

    def _resolve_scope(self, scope):
        if isinstance(scope, (list, tuple)):
            return None, list(scope)
        if isinstance(scope, str) and self._norm(scope) == "roadmap":
            return None, None
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
        if requested is not None:
            ids = list(requested)
        elif module is not None:
            ids = list(module.get("node_ids", []))
        elif module_id is None:
            ids = list(self.graph.payload.get("sequence", self.graph.learnable_nodes if hasattr(self.graph, "learnable_nodes") else self.graph.nodes))
        else:
            ids = []
        result = []
        for order, node_id in enumerate(ids):
            node = self.graph.nodes.get(node_id)
            if node and node.get("learnable", True):
                node_module = node.get("module_id")
                module_order = self.graph.modules.get(node_module, {}).get("index", order)
                result.append({**node, "node_id": node_id, "module_order": module_order})
        return result

    def _roadmap_sample(self, concepts, owner, doc_id, limit, seed):
        progress = self.progress_use_case.get_progress(owner, doc_id) if self.progress_use_case else {}
        progress_nodes = progress.get("nodes", {}) if isinstance(progress, dict) else {}
        learned = {node_id for node_id, value in progress_nodes.items()
                   if isinstance(value, dict) and value.get("state") == "learned"}
        rng = random.Random(str(seed))
        modules = {}
        for concept in concepts:
            modules.setdefault(concept.get("module_id"), []).append(concept)
        module_ids = sorted(modules, key=lambda module_id: (
            self.graph.modules.get(module_id, {}).get("index", 0), str(module_id)))
        for rows in modules.values():
            rows.sort(key=lambda concept: (concept.get("module_order", 0), concept["node_id"]))
        def round_robin(pool):
            groups = {module_id: [row for row in modules[module_id] if row["node_id"] in pool]
                      for module_id in module_ids}
            for rows in groups.values():
                rng.shuffle(rows)
            chosen = []
            while len(chosen) < limit and any(groups.values()):
                for module_id in module_ids:
                    if groups[module_id] and len(chosen) < limit:
                        chosen.append(groups[module_id].pop(0))
            return chosen

        selected = round_robin(learned)
        if len(selected) < limit:
            selected.extend(round_robin({row["node_id"] for row in concepts
                                         if row["node_id"] not in learned})[:limit - len(selected)])
        return selected

    def _material(self, concept):
        return build_material(self.graph, concept, self._settings())

    def _settings(self):
        """The limits as `BSettings`; a dict (as some callers pass) overrides the defaults, None gives the defaults."""
        if isinstance(self.settings, BSettings):
            return self.settings
        overrides = self.settings if isinstance(self.settings, dict) else {}
        return replace(BSettings(), **{key: value for key, value in overrides.items() if key in BSettings.__dataclass_fields__})

    def _bank(self, doc_id, module_id, concept, allow_spend, level, *, owner=None):
        material = self._material(concept)
        key = self._bank_key(doc_id, module_id, concept, level, material=material)
        generated = {}
        cached = self.store.get_cache(key)
        if cached is not None:
            bank = [item for item in cached if not self._hidden(item["item_id"])]
        elif self.model is None or not allow_spend or not material.chunks:
            bank = []
        else:
            try:
                bank = self.store.single_flight(
                    key, lambda: self._generate_bank(concept, material, generated, doc_id, owner=owner))
            except Exception:  # noqa: BLE001 - no model answer (network, cap, quota) leaves the learner the cloze question
                bank = []
            bank = [item for item in bank if not self._hidden(item["item_id"])]
        # The cloze question is cheap and never stored: a bank stored here would hide the model's questions later.
        if not bank:
            bank = [item for item in self._cloze_bank(concept, self._context(module_id, concept))
                    if not self._hidden(item["item_id"])]
        return bank, generated.get("usage", {})

    def _bank_key(self, doc_id, module_id, concept, level, *, material=None):
        material = material or self._material(concept)
        settings = self._settings()
        value = {
            "doc_id": doc_id, "module_id": module_id, "node_id": concept["node_id"], "level": level,
            "material": material.fingerprint(),
            "generation_prompt": settings.quiz_generation_prompt_version,
            "verifier_prompt": settings.quiz_verifier_prompt_version,
            "thinking_level": settings.quiz_verifier_thinking_level,
            "generator_model": getattr(self.model, "model_id", settings.model_id),
            "verifier_model": getattr(self.verifier_model, "model_id", settings.model_id),
            "config": {"generation_max_output_tokens": settings.quiz_generation_max_output_tokens,
                       "verifier_max_output_tokens": settings.quiz_verifier_max_output_tokens,
                       "items_per_concept": settings.quiz_items_per_concept,
                       "contract_version": settings.quiz_contract_version,
                       "local_rules_version": self.LOCAL_RULES_VERSION},
        }
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

    def _context(self, module_id, concept):
        """The concept's passages for the cloze question."""
        chunks = self._chunks_for(concept)
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
        module = self.graph.modules.get(module_id) if module_id else {"module_id": None, "title": "Conceptos"}
        return {"module": module, "chunks": source_chunks}

    def _load_images(self, doc_id, material):
        parse_version = getattr(self.graph, "parse_version", None)
        if not material.pages or self.page_images is None or parse_version is None:
            return []
        found = ((page, self.page_images.get(doc_id, int(parse_version), page)) for page in material.pages)
        return [(page, data) for page, data in found if data]

    def _generate_bank(self, concept, material, generated, doc_id, *, owner=None):
        """Ask for questions, keep those a blind solver answers the same way; once more if fewer than two were kept."""
        settings = self._settings()
        usage = generated["usage"] = {"usd": 0.0, "ms": 0, "input_tokens": 0, "output_tokens": 0}
        images = self._load_images(doc_id, material)
        picture_tokens = IMAGE_TOKEN_ESTIMATE * len(images)
        bank = []
        for lap in (1, 2):
            try:
                result = call_json(
                    self.model, material.user, response_schema=GENERATION_SCHEMA,
                    system_prompt=generation_system(bool(images)), store=self.store, purpose="quiz_gen", doc_id=doc_id,
                    context_hash=hashlib.sha256(material.user.encode()).hexdigest(), allow_spend=True, settings=settings,
                    spend_guard=self.spend_guard, clock=self.clock, images=images, temperature=GENERATION_TEMPERATURE,
                    extra_input_tokens=picture_tokens)
                self._add_call_usage(usage, result)
                candidates, known = [], {kept["item_id"] for kept in bank}
                for raw in (result.payload.get("items") or [])[:settings.quiz_items_per_concept]:
                    item, reason = build_item(concept, material, raw)
                    if reason:
                        self._reject(concept, lap, "local", reason, raw=raw)
                    elif item["item_id"] in known:
                        self._reject(concept, lap, "local", "local.repeated_question", item=item)
                    else:
                        candidates.append(item)
                if candidates:
                    bank += self._blind_solve(concept, material, candidates, images, picture_tokens, usage, doc_id, lap)
            except Exception:  # noqa: BLE001 - what an earlier lap kept is still worth storing
                if not bank:
                    raise
                break
            if len(bank) >= 2:
                break
        return bank[:settings.quiz_items_per_concept]

    def _blind_solve(self, concept, material, items, images, picture_tokens, usage, doc_id, lap):
        """Keep the questions the solver answers like the generator. The solver sees shuffled options and no answer."""
        settings = self._settings()
        shown = []
        for number, item in enumerate(items):
            order = list(range(len(item["options"])))
            with self._rng_lock:
                self.rng.shuffle(order)
            shown.append({"q": number, "stem": item["stem"], "order": order,
                          "options": [item["options"][k]["text"] for k in order]})
        message = solver_message(material, shown)
        judged = {}

        def counts(payload):
            judged["rows"] = verdicts(payload, shown, items)
            kept = sum(row[0] for row in judged["rows"])
            return {"kept": kept, "rejected": len(items) - kept}

        result = call_json(
            self.verifier_model, message, response_schema=SOLVER_SCHEMA, system_prompt=SYSTEM_SOLVER, store=self.store,
            purpose="quiz_verify", doc_id=doc_id, context_hash=hashlib.sha256(message.encode()).hexdigest(),
            allow_spend=True, settings=settings, spend_guard=self.spend_guard, clock=self.clock, images=images,
            temperature=SOLVER_TEMPERATURE, thinking_level=settings.quiz_verifier_thinking_level or None,
            extra_input_tokens=picture_tokens, usage_extra=counts)
        self._add_call_usage(usage, result)
        kept = []
        for item, (keep, reason, detail) in zip(items, judged["rows"]):
            if keep:
                kept.append(item)
            else:
                self._reject(concept, lap, "solver", reason, item=item, detail=detail)
        return kept

    def _reject(self, concept, lap, stage, reason, *, raw=None, item=None, detail=None):
        """Admin log of a question that was not kept: the concept, the lap, and the local rule or the solver's reason."""
        self._record_rejection(stage, reason, concept, raw, item)
        source = item or raw or {}
        options = [{"text": str(option.get("text", "")), "is_correct": bool(option.get("is_correct"))}
                   for option in (item or {}).get("options", [])]
        self.store.put_record("quiz_rejection", secrets.token_hex(12), {
            "doc_id": self.graph.payload.get("doc_id") if isinstance(getattr(self.graph, "payload", None), dict) else None,
            "concept_id": concept.get("node_id"), "concept_name": self._name(concept), "lap": lap, "stage": stage,
            "reason": reason, "solver_reason": detail, "item_id": (item or {}).get("item_id"),
            "stem": str(source.get("stem", ""))[:500], "options": options,
            "created_at": self.clock.now().isoformat() if self.clock else datetime.now(timezone.utc).isoformat()})

    def _bank_estimate_token_breakdown(self, material):
        """Upper bound for two laps: text divided by three, plus a picture's tokens, plus the output cap.

        The solver also reads what the generator wrote, so the generation cap counts as its input.
        """
        settings = self._settings()
        schema_tokens = lambda schema: len(json.dumps(schema, ensure_ascii=False, sort_keys=True)) // 3
        pictures = IMAGE_TOKEN_ESTIMATE * len(material.pages)
        generation = ((len(generation_system(bool(material.pages))) + len(material.user)) // 3
                      + schema_tokens(GENERATION_SCHEMA) + pictures)
        solver = ((len(SYSTEM_SOLVER) + len(material.user)) // 3 + schema_tokens(SOLVER_SCHEMA) + pictures
                  + settings.quiz_generation_max_output_tokens)
        return (2 * generation, 2 * settings.quiz_generation_max_output_tokens,
                2 * solver, 2 * settings.quiz_verifier_max_output_tokens)

    @staticmethod
    def _add_call_usage(total, result):
        total["usd"] += result.cost_usd
        total["ms"] += result.elapsed_ms
        total["input_tokens"] += result.usage.get("input_tokens", result.usage.get("promptTokenCount", 0))
        total["output_tokens"] += result.usage.get("output_tokens", result.usage.get("candidatesTokenCount", 0))

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
            self._record_rejection("cloze", "cloze.anchor_not_found", concept)
            return []
        chunk, text = match
        if CLOZE_NOTATION.search(name):
            self._record_rejection("cloze", "cloze.notation_option", concept)
            return []
        aliases = [name, *self._aliases(concept)]
        target_aliases = {self._norm(a) for a in aliases}
        distractors = []
        distractor_terms = {}
        for candidate in self._distractor_concepts(concept):
            candidate_aliases = [self._name(candidate), *self._aliases(candidate)]
            if {self._norm(a) for a in candidate_aliases} & target_aliases:
                continue
            candidate_name = self._name(candidate)
            if candidate_name and self._norm(candidate_name) not in {self._norm(a) for a in distractors}:
                distractors.append(candidate_name)
                distractor_terms[candidate_name] = candidate_aliases
        if len(distractors) < 2:
            for candidate in self.graph.nodes.values():
                candidate_name = self._name(candidate)
                if (candidate.get("module_id") == concept.get("module_id") and candidate_name
                        and candidate.get("node_id") != concept["node_id"]
                        and self._norm(candidate_name) not in target_aliases
                        and self._norm(candidate_name) not in {self._norm(a) for a in distractors}):
                    distractors.append(candidate_name)
                    distractor_terms[candidate_name] = [candidate_name, *self._aliases(candidate)]
        distractors = [value for value in distractors if not CLOZE_NOTATION.search(value)]
        longer_terms = self._longer_concept_terms(concept, target_aliases)
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
        result = []
        for quote in sentences:
            stem_quote = self._blank_concept_aliases(quote, aliases, name)
            if stem_quote == quote:
                continue
            if self._cloze_visual_or_formula_reference(quote):
                self._record_rejection("cloze", "local.visual_or_formula_reference", concept,
                                       {"stem": quote})
                continue
            if CLOZE_MATH.search(quote):
                self._record_rejection("cloze", "cloze.math_notation", concept, {"stem": quote})
                continue
            # A sentence ending in a colon leads into a list or formula that the stem does not show.
            if INCOMPLETE_CLOZE_LEAD_IN.search(quote) or quote.endswith(":"):
                self._record_rejection("cloze", "cloze.incomplete_lead_in", concept,
                                       {"stem": quote})
                continue
            if any(self._term_in(quote, term) for term in longer_terms):
                self._record_rejection("cloze", "cloze.blank_inside_longer_term", concept, {"stem": quote})
                continue
            if len(stem_quote) < 25:
                self._record_rejection("cloze", "cloze.stem_too_short", concept, {"stem": quote})
                continue
            # A distractor already named in the sentence is ruled out by reading the stem.
            unseen = [value for value in distractors
                      if not any(self._term_in(quote, term) for term in distractor_terms.get(value, [value]))]
            choices = self._balanced_distractors(name, unseen, aliases)
            if not choices:
                reason = ("cloze.distractor_in_stem" if self._balanced_distractors(name, distractors, aliases)
                          else "cloze.no_safe_distractors")
                self._record_rejection("cloze", reason, concept, {"stem": quote})
                continue
            evidence = self._raw_citation(chunk, quote)
            item_id = "qi_" + hashlib.sha256((concept["node_id"] + quote).encode()).hexdigest()[:24]
            options = [{"text": name, "is_correct": True, "why_wrong": "", "evidence": [evidence]}]
            options.extend({"text": value, "is_correct": False,
                            "why_wrong": f"Tài liệu không xác định {value} trong câu trích này.", "evidence": []}
                           for value in choices)
            if self._option_substring_overlap(options):
                self._record_rejection("cloze", "local.option_substring_overlap", concept,
                                       {"stem": quote}, {"options": options})
                continue
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
    def _term_in(text, term):
        return bool(term) and re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.I) is not None

    def _longer_concept_terms(self, concept, target_aliases):
        """Names of other concepts that contain an alias of the answer, e.g. "kết hợp" for "hợp"."""
        terms = []
        for node_id, node in self.graph.nodes.items():
            if node_id == concept["node_id"]:
                continue
            for value in [self._name(node), *self._aliases(node)]:
                normalized = self._norm(value)
                if normalized and normalized not in target_aliases and any(
                        alias and self._term_in(normalized, alias) for alias in target_aliases):
                    terms.append(value)
        return terms

    @staticmethod
    def _option_substring_overlap(options):
        texts = [QuizUseCase._norm(option.get("text", "")) for option in options]
        return any(a and b and (a in b or b in a)
                   for index, a in enumerate(texts) for b in texts[index + 1:])

    @staticmethod
    def _cloze_visual_or_formula_reference(text):
        return bool(CLOZE_VISUAL_OR_FORMULA_REFERENCE.search(str(text or "")))

    @staticmethod
    def _balanced_distractors(answer, candidates, aliases=()):
        excluded = {QuizUseCase._norm(value) for value in [answer, *aliases] if value}
        candidates = list(dict.fromkeys(
            candidate for candidate in candidates if candidate
            and not any(value in QuizUseCase._norm(candidate) or QuizUseCase._norm(candidate) in value
                        for value in excluded if value)
        ))
        for index, first in enumerate(candidates):
            for second in candidates[index + 1:]:
                first_norm, second_norm = QuizUseCase._norm(first), QuizUseCase._norm(second)
                if first_norm in second_norm or second_norm in first_norm:
                    continue
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
