from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from doc2roadmap.application.phase_b.common import call_json, quote_is_verbatim, stable_json
from doc2roadmap.application.phase_b.lectures import _assemble
from doc2roadmap.application.phase_b.postcheck import COMPOUND, best_matching_source_sentence, check_text
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.domain.phase_b_pricing import estimate_cost
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter


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

_SYSTEM = """Soạn tài liệu Markdown bằng tiếng Việt theo yêu cầu. Mỗi khẳng định về sách phải có nhãn nguồn trong văn bản và một cặp label/quote đúng nguyên văn trong citations. Không viết công thức, chỉ tham chiếu [CTk]. Nội dung ngoài sách chỉ được ở outside_document_blocks và không được gắn nhãn nguồn. Tuân theo các giới hạn được nêu trong yêu cầu."""


def _scope_nodes(graph: Any, scope: Any) -> tuple[list[str], list[str]]:
    if isinstance(scope, str):
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
        node_ids = list(scope.get("node_ids", []))
        module_ids = list(scope.get("module_ids", []))
        for module_id in module_ids:
            node_ids.extend(graph.modules.get(module_id, {}).get("node_ids", []))
        return list(dict.fromkeys(str(item) for item in node_ids)), [str(item) for item in module_ids]
    raise ValueError("scope must be a concept, node list, or module scope")


def _retrieval(graph: Any, request: str, excluded: set[str], registry: Any, limit: int = 5) -> list[dict[str, Any]]:
    terms = {term.casefold() for term in re.findall(r"\w+", request) if len(term) > 2}
    scored = []
    for chunk_id, chunk in graph.chunks.items():
        if chunk_id in excluded:
            continue
        text = str(chunk.text)
        score = sum(text.casefold().count(term) for term in terms)
        if score:
            scored.append((score, int(chunk.order_index), chunk_id, text))
    scored.sort(key=lambda row: (-row[0], row[1], row[2]))
    rows = []
    for _, _, chunk_id, text in scored[:limit]:
        label = registry.label(chunk_id, "S")
        rows.append({"label": label, "text": text, "chunk_id": chunk_id})
    return rows


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


def _render(title: str, markdown: str, outside_blocks: list[str]) -> str:
    body = markdown.strip()
    if not body:
        parts = []
    elif re.match(r'^\s*#\s+', body):
        parts = [body]
    else:
        parts = [f"# {title.strip()}", body]
    if outside_blocks:
        parts.append("## Ví dụ minh hoạ ngoài tài liệu\n" + "\n\n".join(f"> {block.strip()}" for block in outside_blocks))
    return "\n\n".join(part for part in parts if part)


def _statements_for_label(markdown: str, label: str) -> list[str]:
    statements = []
    sentence_splitter = UnicodeSentenceSplitter()
    for line in markdown.splitlines():
        line = COMPOUND.sub(lambda match: "".join(
            "[" + item.strip() + "]" for item in re.split(r"[,;]", match[1])), line)
        if f"[{label}]" not in line:
            continue
        plain = re.sub(r"^\s*#{1,6}\s+", "", line)
        plain = re.sub(r"\[[A-Z]+\d+\]", "", plain).strip()
        statements.extend(plain[span.start:span.end].strip()
                          for span in sentence_splitter.split(plain)
                          if plain[span.start:span.end].strip())
    return statements


def export_markdown(document: Mapping[str, Any]) -> str:
    markdown = str(document.get("markdown", ""))
    citations = document.get("citations", [])
    sources: dict[str, dict[str, Any]] = {}
    for citation in citations:
        if isinstance(citation, Mapping) and citation.get("label"):
            sources[str(citation["label"])] = dict(citation)
    for label in sorted(sources, key=lambda value: (-len(value), value)):
        markdown = re.sub(rf"\[{re.escape(label)}\]", f"[^{label}]", markdown)
    notes = []
    for label, citation in sorted(sources.items()):
        section = " › ".join(citation.get("section_path") or [])
        location = f"tr. {citation.get('page')}" if citation.get("page") is not None else "không rõ trang"
        if section:
            location += f", {section}"
        notes.append(f"[^{label}]: {location} (đoạn {citation.get('chunk_id')})")
    return markdown + ("\n\n" + "\n".join(notes) if notes else "") + "\n"


class DocumentUseCase:
    def __init__(self, model: Any, store: Any, *, settings: BSettings | None = None,
                 retriever: Any | None = None) -> None:
        self.model = model
        self.store = store
        self.settings = settings or BSettings()
        self.retriever = retriever

    def create(
        self, doc_id: str, graph_version: str, graph: Any, request: str, scope: Any, *, owner: str,
        dry_run: bool = False, allow_spend: bool = False,
    ) -> dict[str, Any]:
        node_ids, module_ids = _scope_nodes(graph, scope)
        if not node_ids or any(node_id not in graph.nodes for node_id in node_ids):
            raise ValueError("scope contains no known concepts")
        concepts = []
        source_map: dict[str, Any] = {}
        excluded_chunks: set[str] = set()
        registry = graph.new_source_registry() if hasattr(graph, "new_source_registry") else graph.sources
        for node_id in node_ids:
            assembled, _, _ = _assemble(graph, node_id, self.settings, registry)
            if len(node_ids) > 1:
                assembled["open_edges"] = []
                assembled["extra_definitions"] = []
                assembled["exercise"] = []
                assembled["used_later"] = []
            concepts.append({key: assembled.get(key) for key in (
                "concept", "definition", "teaching", "extra_definitions", "prerequisites", "open_edges", "exercise"
            )})
            source_map.update(assembled.get("sources", {}))
            excluded_chunks.update(row.get("chunk_id") for row in assembled.get("sources", {}).values())
        if not dry_run and not allow_spend:
            raise PermissionError("paid document generation requires allow_spend=True")
        retrieval_estimate = 0.0
        if self.retriever is not None:
            search = self.retriever.search(
                request, doc_id=doc_id, graph_version=graph_version,
                current_module_id=graph.nodes[node_ids[0]].get("module_id") if len(node_ids) == 1 else None,
                scope="all", k=5, dry_run=dry_run, allow_spend=allow_spend,
            )
            if dry_run:
                retrieval_estimate = float(search.get("estimated_cost_usd", 0)) if isinstance(search, Mapping) else 0.0
                retrieved = _retrieval(graph, request, excluded_chunks, registry)
            else:
                retrieved = []
                for row in search:
                    chunk_id = row.get("chunk_id")
                    if chunk_id not in graph.chunks or chunk_id in excluded_chunks:
                        continue
                    label = registry.label(chunk_id, "S")
                    retrieved.append({"label": label, "text": row.get("text", ""), "chunk_id": chunk_id})
        else:
            retrieved = _retrieval(graph, request, excluded_chunks, registry)
        for row in retrieved:
            label = row["label"]
            record = registry.resolve(label)
            source_map[label] = {"label": label, "chunk_id": row["chunk_id"],
                                 "page": record.get("page"), "section_path": record.get("section_path"),
                                 "text": row["text"]}
        context = {"request": request, "scope": {"node_ids": node_ids, "module_ids": module_ids},
                   "concepts": concepts, "sources": source_map, "retrieved": retrieved,
                   "limits": {"context_tokens": self.settings.document_context_tokens,
                              "output_tokens": self.settings.document_max_output_tokens,
                              "max_usd": self.settings.document_max_usd}}
        context, context_truncated = _cap_context(context, self.settings)
        prompt = stable_json(context) + "\nUse Markdown headings and cite each factual statement with [label]."
        ctx_hash = context_hash(context)
        if dry_run:
            estimate = estimate_cost(self.settings.model_id, len(_SYSTEM + prompt) // 3,
                                     self.settings.document_max_output_tokens) + retrieval_estimate
            return {"contract_version": "document-1", "doc_id": doc_id,
                    "scope": context["scope"], "request": request, "status": "generating",
                    "dry_run": True, "context_hash": ctx_hash, "estimate_usd": estimate}
        estimated_usd = estimate_cost(self.settings.model_id, len(_SYSTEM + prompt) // 3,
                                     self.settings.document_max_output_tokens)
        if estimated_usd > self.settings.document_max_usd:
            return {"contract_version": "document-1", "document_id": uuid4().hex,
                    "owner": owner, "doc_id": doc_id, "request": request,
                    "scope": context["scope"], "title": "", "markdown": "",
                    "citations": [], "outside_document_blocks": 0, "formula_refs": [],
                    "status": "failed", "reason": "estimated_cost_over_limit", "usage": {}}
        try:
            result = call_json(
                self.model, prompt, response_schema=DOCUMENT_SCHEMA, system_prompt=_SYSTEM, store=self.store,
                purpose="document", doc_id=doc_id, context_hash=ctx_hash, allow_spend=True,
                settings=self.settings, learner_id=owner,
            )
        except Exception as error:
            usage_row = next((row for row in reversed(self.store.usage_rows(doc_id))
                              if row.get("purpose") == "document" and row.get("context_hash") == ctx_hash), {})
            document_id = uuid4().hex
            failed = {
                "contract_version": "document-1", "document_id": document_id, "owner": owner,
                "doc_id": doc_id, "graph_version": graph_version, "request": request,
                "scope": context["scope"], "title": "", "markdown": "", "citations": [],
                "outside_document_blocks": 0, "formula_refs": [], "status": "failed",
                "reason": "invalid_model_response" if isinstance(error, json.JSONDecodeError) else "model_error",
                "warnings": [],
                "usage": {"model_id": getattr(self.model, "model_id", self.settings.model_id),
                          "cost_usd": usage_row.get("cost_usd", 0),
                          "elapsed_ms": usage_row.get("elapsed_ms", 0),
                          "input_tokens": usage_row.get("input_tokens", 0),
                          "output_tokens": usage_row.get("output_tokens", 0),
                          "thought_tokens": usage_row.get("thought_tokens", 0)},
            }
            self.store.put_record("documents", document_id, failed)
            return failed
        payload = result.payload
        title = str(payload.get("title") or "Tài liệu học tập")
        markdown = str(payload.get("markdown") or "")
        citations = []
        cited_labels = set()
        for item in payload.get("citations", []):
            if not isinstance(item, Mapping):
                continue
            label, quote = item.get("label"), item.get("quote")
            if not isinstance(label, str) or label in cited_labels:
                continue
            source = source_map.get(label)
            if not source:
                continue
            source_text = registry.raw_text(label) or str(source.get("text", ""))
            quote = str(quote or "")
            if not quote_is_verbatim(quote, source_text, max_chars=self.settings.quote_max_chars):
                statement = " ".join(_statements_for_label(markdown, label))
                quote = best_matching_source_sentence(statement, source_text, self.settings.quote_max_chars)
            if quote and quote_is_verbatim(quote, source_text, max_chars=self.settings.quote_max_chars):
                citation = registry.citation(label, quote)
                if citation:
                    citations.append(citation)
                    cited_labels.add(label)
        outside = [str(block).strip() for block in payload.get("outside_document_blocks", []) if str(block).strip()]
        max_chars = self.settings.document_max_output_tokens * 3
        warnings = ["context_truncated"] if context_truncated else []
        if len(markdown) > max_chars:
            markdown = markdown[:max_chars].rsplit("\n", 1)[0]
            warnings.append("output_truncated")
        checked = check_text(markdown, graph=graph, settings=self.settings,
            citations_by_label={str(row['label']): row for row in citations}, outside_blocks=outside)
        markdown, citations, outside = checked['text'], checked['citations'], checked['outside_blocks']
        warnings.extend(dict.fromkeys(row['kind'] for row in checked['warnings']))
        document_id = uuid4().hex
        status = "ready" if checked['counts']['sourced_sentences'] else "failed"
        markdown = _render(title, markdown, outside)
        document = {
            "contract_version": "document-1", "document_id": document_id, "owner": owner,
            "doc_id": doc_id, "graph_version": graph_version, "request": request,
            "scope": context["scope"], "title": title, "markdown": markdown,
            "citations": citations, "outside_document_blocks": len(outside),
            "formula_refs": [], "status": status,
            "reason": "no_valid_citations" if not citations else None,
            "warnings": warnings,
            "postcheck": checked['counts'],
            "usage": {"model_id": getattr(self.model, "model_id", self.settings.model_id),
                      "cost_usd": result.cost_usd, "elapsed_ms": result.elapsed_ms,
                      "ttft_ms": result.ttft_ms,
                      "input_tokens": result.usage.get("promptTokenCount", 0),
                      "output_tokens": result.usage.get("candidatesTokenCount", 0),
                      "thought_tokens": result.usage.get("thoughtsTokenCount", 0)},
        }
        self.store.put_record("documents", document_id, document)
        return document

    def get(self, document_id: str, *, owner: str) -> dict[str, Any] | None:
        record = self.store.get_record("documents", document_id)
        return record if record and record.get("owner") == owner else None

    def export(self, document_id: str, *, owner: str) -> str:
        document = self.get(document_id, owner=owner)
        if not document:
            raise KeyError(document_id)
        return export_markdown(document)
