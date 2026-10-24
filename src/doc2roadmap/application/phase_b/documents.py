from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from time import perf_counter
from typing import Any
from uuid import uuid4

from doc2roadmap.application.phase_b.budget import DailyLimitExceeded, DailySpendGuard, spending_call
from doc2roadmap.application.phase_b.clock import SystemClock
from doc2roadmap.application.phase_b.common import stable_json
from doc2roadmap.application.phase_b.document_context3 import (
    DEFAULT_REQUEST, build_validation, gather, split_group_labels, system_prompt, title_of,
)
from doc2roadmap.application.phase_b.lecture3 import IMAGE_TOKEN_ESTIMATE, _Attempt
from doc2roadmap.application.phase_b.lecture_context3 import source_rows
from doc2roadmap.application.phase_b.lectures import _aggregate_usage
from doc2roadmap.application.ports.page_images import PageImages
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash, usage_row
from doc2roadmap.domain.phase_b_pricing import estimate_cost, token_cost


DOCUMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "markdown": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "object", "properties": {
            "label": {"type": "string"}, "quote": {"type": "string"}},
            "required": ["label", "quote"]}},
        "outside_document_blocks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "markdown", "citations", "outside_document_blocks"],
}


def _scope_nodes(graph: Any, scope: Any, *, min_jaccard: float = 0.5) -> tuple[list[str], list[str]]:
    if isinstance(scope, str):
        if scope.strip().casefold() == "roadmap":
            module_ids = list(graph.modules)
            node_ids = [node_id for module_id in module_ids
                        for node_id in graph.modules[module_id].get("node_ids", [])]
            return list(dict.fromkeys(node_ids)), module_ids
        if scope in graph.modules:
            module_ids = [scope]
            return list(graph.modules[scope].get("node_ids", [])), module_ids
        if scope not in graph.nodes:
            matches = graph.lookup_concept(scope).get("matches", [])
            if len(matches) == 1:
                return [matches[0]["node_id"]], []
        return [scope], []
    if isinstance(scope, (list, tuple)):
        return [str(item) for item in scope], []
    if isinstance(scope, Mapping):
        if scope.get("kind") == "roadmap":
            module_ids = list(graph.modules)
            node_ids = [node_id for module_id in module_ids
                        for node_id in graph.modules[module_id].get("node_ids", [])]
            return list(dict.fromkeys(node_ids)), module_ids
        if scope.get("kind") == "module":
            from doc2roadmap.domain.scope import resolve_scope
            resolved = resolve_scope(scope, graph, min_jaccard)
            if resolved["stale"] or resolved["module_id"] is None:
                module_ids = list(graph.modules)
            else:
                module_ids = [resolved["module_id"]]
            node_ids = [node_id for module_id in module_ids
                        for node_id in graph.modules[module_id].get("node_ids", [])]
            return list(dict.fromkeys(node_ids)), module_ids
        if scope.get("module_ids"):
            module_ids = [str(module_id) for module_id in scope["module_ids"]
                          if module_id in graph.modules]
            node_ids = list(scope.get("node_ids", []))
            node_ids.extend(node_id for module_id in module_ids
                            for node_id in graph.modules[module_id].get("node_ids", []))
            return list(dict.fromkeys(str(item) for item in node_ids)), module_ids
        node_ids = list(scope.get("node_ids", []))
        module_ids = list(scope.get("module_ids", []))
        for module_id in module_ids:
            node_ids.extend(graph.modules.get(module_id, {}).get("node_ids", []))
        return list(dict.fromkeys(str(item) for item in node_ids)), [str(item) for item in module_ids]
    raise ValueError("scope must be a concept, node list, or module scope")


def _cap_context(context: dict[str, Any], settings: BSettings) -> tuple[dict[str, Any], bool]:
    truncated = False
    while len(stable_json(context)) // 3 > settings.document_context_tokens:
        retrieval = context.get("retrieved", [])
        if retrieval:
            retrieval.pop()
            truncated = True
            continue
        concepts = context.get("concepts", [])
        if concepts:
            row = concepts[-1]
            if row.get("open_edges"):
                row["open_edges"].pop()
            elif row.get("extra_definitions"):
                row["extra_definitions"].pop()
            elif row.get("exercise"):
                row["exercise"].clear()
            elif len(concepts) > 1:
                concepts.pop()
                context["scope"]["node_ids"] = [item["concept"]["node_id"] for item in concepts]
            else:
                break
            truncated = True
            continue
        break
    # Keep the complete source registry for quote validation in the caller, but send
    # only bounded excerpts for sources that remain in the prompt.
    context["sources"] = {label: dict(row) for label, row in context.get("sources", {}).items()}
    while len(stable_json(context)) // 3 > settings.document_context_tokens:
        rows = [row for row in context["sources"].values() if len(str(row.get("text", ""))) > 40]
        if not rows:
            break
        row = max(rows, key=lambda value: len(str(value.get("text", ""))))
        excess_chars = max(1, (len(stable_json(context)) // 3 - settings.document_context_tokens) * 3)
        text = str(row["text"])
        row["text"] = text[:max(40, len(text) - excess_chars)]
        truncated = True
    labels: set[str] = set()
    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {"label", "source", "N", "Q"} and isinstance(child, str):
                    labels.add(child)
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect({key: value for key, value in context.items() if key not in {"sources", "retrieved"}})
    labels.update(row.get("label") for row in context.get("retrieved", []) if row.get("label"))
    context["sources"] = {label: source for label, source in context.get("sources", {}).items() if label in labels}
    context["retrieved"] = [row for row in context.get("retrieved", []) if row.get("label") in labels]
    return context, truncated


def export_markdown(document: Mapping[str, Any]) -> str:
    """Markdown with each cited `[Sx]` turned into a footnote naming its page, section and passage."""
    markdown = split_group_labels(str(document.get("markdown", "")))
    sources = {str(row["label"]): row for row in document.get("sources", []) if isinstance(row, Mapping)}
    used = [label for label in dict.fromkeys(re.findall(r"\[(S\d+)\]", markdown)) if label in sources]
    markdown = re.sub(r"\[(S\d+)\]", lambda m: f"[^{m[1]}]" if m[1] in sources else m[0], markdown)
    notes = []
    for label in sorted(used, key=lambda value: int(value[1:])):
        row = sources[label]
        section = " › ".join(row.get("section_path") or [])
        location = f"tr. {row.get('page')}" if row.get("page") is not None else "không rõ trang"
        if section:
            location += f", {section}"
        notes.append(f"[^{label}]: {location} (đoạn {row.get('chunk_id')})")
    return markdown.rstrip("\n") + ("\n\n" + "\n".join(notes) if notes else "") + "\n"


_MESSAGES = {
    "scope_too_large": "Bạn chọn quá nhiều module cho một tài liệu. Hãy chọn tối đa {limit} module hoặc thu hẹp phạm vi.",
    "daily_limit": "Hôm nay bạn đã dùng hết hạn mức tạo tài liệu. Bạn thử lại vào ngày mai.",
    "estimated_cost_over_limit": "Yêu cầu này quá lớn để tạo một tài liệu. Hãy thu hẹp phạm vi hoặc yêu cầu.",
    "loi_mang": "Chưa kết nối được tới mô hình để viết tài liệu. Bạn thử lại sau ít phút.",
    "het_thoi_gian": "Mô hình trả lời quá lâu nên tài liệu chưa viết xong. Bạn thử lại sau ít phút.",
    "khong_dung_duoc": "Mô hình chưa viết được tài liệu dùng được. Bạn thử lại.",
    "khong_co_mo_hinh": "Chưa có mô hình để viết tài liệu ở chế độ này.",
}
_RETRYABLE = {"scope_too_large": False, "estimated_cost_over_limit": False}


class DocumentUseCase:
    def __init__(self, model: Any, store: Any, *, settings: BSettings | None = None,
                 search: Any | None = None, page_images: PageImages | None = None, spend_guard: Any | None = None,
                 clock: Any | None = None) -> None:
        self.model = model
        self.store = store
        self.settings = settings or BSettings()
        self.search = search
        self.page_images = page_images
        self.clock = clock or SystemClock()
        self.spend_guard = spend_guard or DailySpendGuard(store, settings=self.settings, clock=self.clock)

    def create(
        self, doc_id: str, graph_version: str, graph: Any, request: str, scope: Any, *, owner: str,
        dry_run: bool = False, allow_spend: bool = False, home_scope: Any | None = None,
        session_id: str | None = None, origin: str = "button",
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        emit = on_event or (lambda event: None)
        settings = self.settings
        if not owner:
            raise PermissionError('owner is required')
        if graph.doc_id and doc_id != graph.doc_id:
            raise ValueError('doc_id does not match graph')
        node_ids, module_ids = _scope_nodes(graph, scope, min_jaccard=settings.scope_remap_min_jaccard)
        module_ids = list(dict.fromkeys(
            graph.nodes[node_id].get("module_id") for node_id in node_ids
            if node_id in graph.nodes and graph.nodes[node_id].get("module_id") in graph.modules))
        if origin not in {"button", "assistant"}:
            raise ValueError("origin không hợp lệ")
        if origin == 'button':
            session_id = None
        if home_scope is None:
            if isinstance(scope, Mapping) and scope.get("kind") in {"roadmap", "module"}:
                home_scope = dict(scope)
            elif isinstance(scope, str) and scope in graph.modules:
                home_scope = {"kind": "module",
                              "node_ids": list(graph.modules[scope].get("node_ids", [])),
                              "module_id_at_creation": scope,
                              "graph_version_at_creation": getattr(graph, "graph_version", graph_version)}
            else:
                home_scope = {"kind": "roadmap"}
        request = str(request or "").strip() or DEFAULT_REQUEST
        document_id = uuid4().hex
        base = {
            "contract_version": settings.document_contract_version, "document_id": document_id, "owner": owner,
            "doc_id": doc_id, "graph_version": graph_version, "request": request,
            "scope": {"node_ids": node_ids, "module_ids": module_ids}, "title": "", "markdown": "", "sources": [],
            "status": "failed", "failure": None, "warnings": [], "usage": {}, "home_scope": home_scope,
            "session_id": session_id, "origin": origin, "node_ids": node_ids,
            "created_at": self.clock.now().isoformat(),
        }

        def failed(reason: str, attempts: list[_Attempt] | None = None, *, keep: bool = True) -> dict[str, Any]:
            result = {**base, "failure": {
                "reason_code": reason, "message": _MESSAGES[reason].format(limit=settings.document_max_modules),
                "retryable": _RETRYABLE.get(reason, True)}, "usage": self._usage(attempts) if attempts else {}}
            if keep:
                self.store.put_record("documents", document_id, result)
            emit({"event": "failure", "document": result})
            return result

        # Gates first: nothing below this line costs money until the model is called.
        if len(set(module_ids)) > settings.document_max_modules:
            return failed("scope_too_large", keep=False)
        if not node_ids or any(node_id not in graph.nodes for node_id in node_ids):
            raise ValueError("scope contains no known concepts")
        if not dry_run and not allow_spend:
            raise PermissionError("paid document generation requires allow_spend=True")
        material = gather(graph, node_ids, request, settings, self.search)
        images = self._load_images(doc_id, graph, material.pages)
        system = system_prompt(bool(images))
        estimate = estimate_cost(settings.model_id,
                                 (len(system) + len(material.user)) // 3 + IMAGE_TOKEN_ESTIMATE * len(images),
                                 settings.document_max_output_tokens)
        if dry_run:
            return {"contract_version": settings.document_contract_version, "doc_id": doc_id, "scope": base["scope"],
                    "request": request, "status": "generating", "dry_run": True,
                    "context_hash": context_hash({"user": material.user, "pages": [page for page, _ in images]}),
                    "estimate_usd": estimate}
        if estimate > settings.document_max_usd:
            return failed("estimated_cost_over_limit", keep=False)
        if self.model is None:
            return failed("khong_co_mo_hinh", keep=False)

        sources = source_rows(material.chunks)
        material_hash = context_hash({"user": material.user, "images": [page for page, _ in images]})
        emit({"event": "skeleton", "document_id": document_id, "title": None})
        deadline = started + settings.document_timeout_seconds
        attempts: list[_Attempt] = []
        for index in range(2):
            try:
                attempts.append(self._attempt(system, material.user, images, doc_id, owner, material_hash, index,
                                              deadline, estimate, emit))
            except DailyLimitExceeded:
                return failed("daily_limit", attempts)
            last = attempts[-1]
            if last.usable or last.error is not None or last.timed_out:
                break
        last = attempts[-1]
        if not last.usable:
            reason = ("het_thoi_gian" if last.timed_out or isinstance(last.error, TimeoutError)
                      else "loi_mang" if last.error is not None else "khong_dung_duoc")
            return failed(reason, attempts)
        cut = last.error is not None or last.timed_out or last.finish_reason in {"MAX_TOKENS", "LENGTH"}
        usage = self._usage(attempts)
        validation = build_validation(
            last.text, [row["label"] for row in sources], finish_reason=last.finish_reason, images_sent=len(images),
            pages_wanted=material.pages_wanted, search_error=material.search_error,
            seconds_to_first_text=None if last.ttft_ms is None else round(last.ttft_ms / 1000, 3),
            seconds_total=round(perf_counter() - started, 3), cost_usd=usage["cost_usd"])
        self.store.put_record("document_validation", document_id, {
            **validation, "document_id": document_id, "doc_id": doc_id, "owner": owner,
            "prompt_version": settings.document_prompt_version, "context_version": settings.document_context_version})
        self.store.append_usage({
            "purpose": "document_validation", "model_id": usage["model_id"], "doc_id": doc_id, "learner_id": owner,
            "context_hash": material_hash, "input_tokens": 0, "output_tokens": 0, "thought_tokens": 0, "cost_usd": 0.0,
            "ttft_ms": None, "elapsed_ms": 0, "generation_index": len(attempts) - 1, "validation": validation,
            "created_at": self.clock.now().isoformat()})
        document = {**base, "title": title_of(last.text), "markdown": last.text, "sources": sources, "status": "ready",
                    "warnings": ["cat_ngan"] if cut else [], "usage": usage}
        self.store.put_record("documents", document_id, document)
        emit({"event": "final", "document": document})
        return document

    def _load_images(self, doc_id: str, graph: Any, pages: list[int]) -> list[tuple[int, bytes]]:
        parse_version = getattr(graph, "parse_version", None)
        if not pages or self.page_images is None or parse_version is None:
            return []
        found = ((page, self.page_images.get(doc_id, int(parse_version), page)) for page in pages)
        return [(page, data) for page, data in found if data]

    def _usage(self, attempts: list[_Attempt]) -> dict[str, Any]:
        total = _aggregate_usage([{**attempt.usage, "cost_usd": attempt.cost_usd} for attempt in attempts])
        first = next((attempt.ttft_ms for attempt in attempts if attempt.ttft_ms is not None), None)
        return {"model_id": getattr(self.model, "model_id", self.settings.model_id),
                "elapsed_ms": sum(attempt.elapsed_ms for attempt in attempts), "ttft_ms": first,
                "input_tokens": total["promptTokenCount"], "output_tokens": total["candidatesTokenCount"],
                "thought_tokens": total["thoughtsTokenCount"], "cost_usd": total["cost_usd"]}

    def _attempt(self, system: str, user: str, images: list[tuple[int, bytes]], doc_id: str, owner: str, material: str,
                 index: int, deadline: float, estimate: float, emit: Callable[[dict[str, Any]], None]) -> _Attempt:
        model_id = getattr(self.model, "model_id", self.settings.model_id)
        replayed = bool(getattr(self.model, "is_replay", False))
        attempt = _Attempt()
        with spending_call(self.spend_guard, "document", estimate, owner, replayed=replayed, clock=self.clock) as admitted_at:
            began = perf_counter()
            session = stream = None
            try:
                session = self.model.start_session(system)
                stream = iter(session.stream_text(
                    user, images=images, temperature=self.settings.document_temperature,
                    transport_retries=self.settings.lecture_click_transport_retries,
                    timeout_seconds=max(0.1, deadline - perf_counter())))
            except Exception as error:  # noqa: BLE001
                attempt.error = error
            try:
                while stream is not None:
                    try:
                        piece = next(stream)
                    except StopIteration:
                        break
                    except Exception as error:  # noqa: BLE001
                        attempt.error = error
                        break
                    if piece:
                        if not attempt.text:
                            attempt.ttft_ms = round((perf_counter() - began) * 1000)
                        attempt.text += piece
                        emit({"event": "delta", "text": piece})
                    if perf_counter() >= deadline:
                        attempt.timed_out = True
                        break
            finally:
                close = getattr(stream, "close", None)
                if close:
                    close()
                attempt.usage = dict(getattr(session, "last_usage", None) or {})
                attempt.finish_reason = getattr(session, "last_finish_reason", None)
                attempt.elapsed_ms = round((perf_counter() - began) * 1000)
                attempt.cost_usd = 0.0 if replayed else token_cost(model_id, attempt.usage)
                ledger = usage_row(purpose="document", model_id=model_id, doc_id=doc_id, context_hash=material,
                                   usage=attempt.usage, elapsed_ms=attempt.elapsed_ms, ttft_ms=attempt.ttft_ms,
                                   learner_id=owner, cost_usd=attempt.cost_usd)
                ledger.update(generation_index=index, created_at=admitted_at, replayed=replayed)
                self.store.append_usage(ledger)
        return attempt

    def get(self, document_id: str, *, owner: str) -> dict[str, Any] | None:
        record = self.store.get_record("documents", document_id)
        return record if record and record.get("owner") == owner else None

    def export(self, document_id: str, *, owner: str) -> str:
        document = self.get(document_id, owner=owner)
        if not document:
            raise KeyError(document_id)
        return export_markdown(document)
