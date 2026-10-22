from __future__ import annotations

import hashlib
import json
import math
import threading
import time
from collections import OrderedDict

from doc2roadmap.application.use_cases.ingest_document import validate_doc_id
from doc2roadmap.application.use_cases.index_document import retriever_from_payload
from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.retrieval import embedding_text
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.domain.phase_b_pricing import embedding_cost


def _hash(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def retrieval_inputs(chunks) -> list[dict]:
    return [
        {"chunk_id": chunk.chunk_id, "text": chunk.text,
         "section_path": list(chunk.section_path),
         "embedding_input": embedding_text(chunk.section_path, chunk.text)}
        for chunk in sorted(chunks, key=lambda row: (row.order_index, row.chunk_id))
    ]


def assert_retrieval_compatible(retrieval_payload: dict, chunks) -> str:
    """Reject stale chunk vectors based on actual inputs, not artifact version numbers."""
    expected = retrieval_inputs(chunks)
    documents = retrieval_payload.get("documents", [])
    if len(documents) != len(expected):
        raise ValueError("chỉ mục truy hồi lệch số lượng chunk của đồ thị")
    actual = {row.get("chunk_id"): row for row in documents}
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    if len(actual) != len(documents) or set(actual) != {row["chunk_id"] for row in expected}:
        raise ValueError("chỉ mục truy hồi lệch chunk_id của đồ thị")
    for row in expected:
        indexed = actual[row["chunk_id"]]
        if indexed.get("text") != row["text"]:
            raise ValueError(f"chỉ mục truy hồi lệch văn bản chunk {row['chunk_id']}")
        # New indexes retain full section input. Legacy indexes can still prove their section
        # identity through section_id; they remain readable when the source section is unchanged.
        if "section_path" in indexed and list(indexed["section_path"]) != row["section_path"]:
            raise ValueError(f"chỉ mục truy hồi lệch đường mục chunk {row['chunk_id']}")
        if "section_path" not in indexed and indexed.get("section_id") != chunks_by_id[row["chunk_id"]].parent_section_id:
            raise ValueError(f"chỉ mục truy hồi lệch mục chunk {row['chunk_id']}")
    return _hash(expected)


def build_module_assignments(graph_payload: dict, chunks) -> dict:
    """Build A12's metadata overlay without changing retrieval vectors or chunk IDs."""
    chunks = sorted(chunks, key=lambda chunk: (chunk.order_index, chunk.chunk_id))
    direct = graph_payload.get("chunk_module_map", {})
    module_order = {module["module_id"]: int(module.get("index", index))
                    for index, module in enumerate(graph_payload.get("modules", []))}
    assignments = {}
    previous = None
    for chunk in chunks:
        row = direct.get(chunk.chunk_id)
        if row:
            if isinstance(row, dict):
                module_id = row.get("module_id")
                all_ids = row.get("all_module_ids") or ([module_id] if module_id else [])
            else:
                module_id, all_ids = row, [row]
            all_ids = sorted(set(all_ids), key=lambda value: (module_order.get(value, 10**9), value))
            if not module_id and all_ids:
                module_id = all_ids[0]
            assignments[chunk.chunk_id] = {
                "module_id": module_id,
                "all_module_ids": all_ids,
                "module_source": "chunk_module_map",
            }
            if module_id:
                previous = assignments[chunk.chunk_id]
        elif previous:
            assignments[chunk.chunk_id] = {
                "module_id": previous["module_id"],
                "all_module_ids": list(previous["all_module_ids"]),
                "module_source": "hint",
            }
        else:
            assignments[chunk.chunk_id] = {"module_id": None, "all_module_ids": [], "module_source": "none"}
    counts = {name: sum(row["module_source"] == name for row in assignments.values())
              for name in ("chunk_module_map", "hint", "none")}
    return {
        "schema_version": 1,
        "graph_version": graph_payload.get("graph_version", graph_payload.get("version")),
        "index_fingerprint": _hash(retrieval_inputs(chunks)),
        "assignments": assignments,
        "counts": counts,
    }


def load_learning_graph(store, doc_id: str, graph_version: int | None = None) -> LearningGraph:
    validate_doc_id(doc_id)
    if graph_version is None:
        latest = store.load_latest_graph(doc_id)
        graph = latest if _is_complete_learning_graph(latest) else None
        if graph is None:
            for version in range(int(latest.version) - 1, 0, -1):
                try:
                    candidate = store.load_graph(doc_id, version)
                except FileNotFoundError:
                    continue
                if _is_complete_learning_graph(candidate):
                    graph = candidate
                    break
        if graph is None:
            raise ValueError(f"không có đồ thị A10 hoàn tất cho tài liệu {doc_id}")
    else:
        graph = store.load_graph(doc_id, graph_version)
        if not _is_complete_learning_graph(graph):
            raise ValueError(f"đồ thị v{graph_version} không phải lộ trình A10 hoàn tất có module")
    config = graph.manifest.get("config", {})
    chunks_version = config.get("chunks_version")
    if chunks_version is None:
        chunks_version = graph.manifest.get("chunks_version")
    chunks = store.load_chunks(doc_id, int(chunks_version)) if chunks_version else store.load_latest_chunks(doc_id)
    parse_version = chunks.manifest.get("parse_version")
    tree = store.load_parse(doc_id, int(parse_version)).tree if parse_version else None
    payload = {**graph.payload, "doc_id": doc_id, "graph_version": graph.version}
    learning_graph = LearningGraph(payload, chunks.result.chunks, tree)
    learning_graph.formula_images = _load_formula_images(store, doc_id, parse_version)
    return learning_graph


def _load_formula_images(store, doc_id: str, parse_version) -> dict[str, dict]:
    if not parse_version or not hasattr(store, "root"):
        return {}
    from pathlib import Path

    index_path = (Path(store.root) / "phase_b" / "formula_images" / doc_id
                  / f"parse-v{int(parse_version)}" / "index.json")
    if not index_path.is_file():
        return {}
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if payload.get("doc_id") != doc_id or int(payload.get("parse_version", 0)) != int(parse_version):
        return {}
    return {
        row["occurrence_id"]: dict(row)
        for row in payload.get("formula_refs", [])
        if isinstance(row, dict) and row.get("occurrence_id")
    }


def _is_complete_learning_graph(graph) -> bool:
    payload = graph.payload
    return (graph.manifest.get("stage") == "stages"
            and isinstance(payload.get("modules"), list) and bool(payload["modules"])
            and payload.get("main_complete") is not False)


class SearchContext:
    """A loaded graph and retrieval index plus values derived from them, computed at most once."""

    def __init__(self, graph, index) -> None:
        self.graph, self.index, self._derived = graph, index, {}

    def derived(self, name: str, factory):
        if name not in self._derived:
            self._derived[name] = factory()
        return self._derived[name]


class SearchContextCache:
    """Process-wide LRU of SearchContext keyed by (store, doc_id, graph_version, retrieval version).

    Graph and retrieval artifacts are immutable per version, so a key never goes stale; a new retrieval
    version changes the key. Stores that cannot name their root or latest retrieval version are not cached.
    """

    def __init__(self, max_entries: int = 8) -> None:
        self.max_entries, self._entries, self._lock = max_entries, OrderedDict(), threading.Lock()
        self.loads = 0

    def get(self, store, doc_id: str, graph_version: int | None) -> SearchContext:
        version_of = getattr(store, "latest_retrieval_version", None)
        root = getattr(store, "root", None)
        index_version = version_of(doc_id) if version_of and root is not None and graph_version is not None else None
        if index_version is None:
            return self._load(store, doc_id, graph_version)
        key = (str(root), doc_id, graph_version, index_version)
        with self._lock:
            if key in self._entries:
                self._entries.move_to_end(key)
                return self._entries[key]
        context = self._load(store, doc_id, graph_version)
        with self._lock:
            self._entries[key] = context
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
        return context

    def _load(self, store, doc_id: str, graph_version: int | None) -> SearchContext:
        self.loads += 1
        return SearchContext(load_learning_graph(store, doc_id, graph_version), store.load_latest_retrieval(doc_id))


SEARCH_CONTEXTS = SearchContextCache()


class SearchDocumentB:
    """Phase B search wrapper: pinned graph/index, module hints, no progress filtering."""

    def __init__(self, artifact_store, embedding, phase_b_store, contexts: SearchContextCache | None = None) -> None:
        self.artifacts = artifact_store
        self.embedding = embedding
        self.phase_b = phase_b_store
        self.contexts = SEARCH_CONTEXTS if contexts is None else contexts

    def search(self, query: str, *, doc_id: str, graph_version: int | None = None,
               current_module_id: str | None = None, scope: str = "all", k: int = 5,
               dry_run: bool = False, allow_spend: bool = False) -> list[dict] | dict:
        """Callable-friendly alias for application use cases; ``all`` searches the document."""
        if scope == "all":
            scope = "ca_tai_lieu"
        return self.execute(doc_id, query, graph_version,
                            current_module_id=current_module_id, scope=scope, k=k,
                            dry_run=dry_run, allow_spend=allow_spend)

    def execute(self, doc_id: str, query: str, graph_version: int | None = None, *,
                current_module_id: str | None = None, scope: str = "uu_tien_module", k: int = 6,
                dry_run: bool = False, allow_spend: bool = False) -> list[dict] | dict:
        validate_doc_id(doc_id)
        if not query.strip():
            raise ValueError("truy vấn không được rỗng")
        if not 1 <= k <= 6:
            raise ValueError("k phải nằm trong [1, 6]")
        if scope not in {"uu_tien_module", "ca_tai_lieu"} and not scope.startswith("module:"):
            raise ValueError("scope phải là uu_tien_module, ca_tai_lieu hoặc module:<index>")
        context = self.contexts.get(self.artifacts, doc_id, graph_version)
        graph, index = context.graph, context.index
        expected_model = index.manifest.get("embedding_model_id")
        if expected_model != self.embedding.embedding_model_id:
            raise ValueError("mô hình embedding truy vấn không khớp mô hình đã lập chỉ mục")
        fingerprint = context.derived(
            "fingerprint", lambda: assert_retrieval_compatible(index.payload, graph.chunks.values()))
        estimated_tokens = max(1, math.ceil(len(query) / 3))
        estimated_cost = embedding_cost(self.embedding.embedding_model_id, estimated_tokens)
        if dry_run:
            return {"dry_run": True, "doc_id": doc_id, "graph_version": graph.graph_version,
                    "scope": scope, "k": k, "estimated_input_tokens": estimated_tokens,
                    "estimated_cost_usd": estimated_cost, "index_fingerprint": fingerprint,
                    "cost_basis": "estimated at the configured input token rate"}
        if not allow_spend:
            raise PermissionError("embedding truy vấn cần allow_spend=True")
        started = time.perf_counter()
        vectors = self.embedding.embed([EmbeddingRequest(query, "RETRIEVAL_QUERY")])
        if len(vectors) != 1:
            raise ValueError("cổng embedding trả sai số lượng vector truy vấn")
        cached = bool(getattr(self.embedding, "last_cached", 0))
        if self.phase_b:
            self.phase_b.append_usage({
                "purpose": "embedding", "operation": "search_query",
                "model_id": self.embedding.embedding_model_id, "doc_id": doc_id,
                "input_tokens": 0 if cached else estimated_tokens, "cost_usd": 0.0 if cached else estimated_cost,
                "cost_basis": "query vector reused; no embedding call" if cached
                else "estimated at configured input token rate",
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "context_hash": _hash({"query": query, "graph_version": graph.graph_version}),
            })
        retriever = context.derived("retriever", lambda: retriever_from_payload(index.payload))
        hits = retriever.search(query, vectors[0], top_k=20)
        assignments = context.derived(
            "assignments", lambda: build_module_assignments(graph.payload, graph.chunks.values()))["assignments"]
        module_order = {module_id: int(module.get("index", position))
                        for position, (module_id, module) in enumerate(graph.modules.items())}
        if scope.startswith("module:"):
            wanted = int(scope.split(":", 1)[1])
            module_ids = {module_id for module_id, module in graph.modules.items()
                          if int(module.get("index", -1)) == wanted}
            hits = [hit for hit in hits if module_ids.intersection(
                assignments.get(hit.chunk_id, {}).get("all_module_ids", []))][:k]
        elif scope == "uu_tien_module" and current_module_id:
            from doc2roadmap.domain.retrieval import prefer_module_hits
            hits = prefer_module_hits(hits, assignments, module_order, current_module_id, top_k=k)
        else:
            hits = hits[:k]
        sources = graph.new_source_registry()
        result = []
        for hit in hits:
            chunk = graph.chunks[hit.chunk_id]
            assignment = assignments[hit.chunk_id]
            module_id = assignment["module_id"]
            result.append({
                "source_label": sources.label(hit.chunk_id, "S"),
                "chunk_id": hit.chunk_id,
                "page": chunk.page,
                "section_path": list(chunk.section_path),
                "module_id": module_id,
                "module_index": graph.modules.get(module_id, {}).get("index"),
                "module_source": assignment["module_source"],
                "relation": graph.relation(module_id, current_module_id),
                "score": hit.score,
                "text": chunk.text[:1200],
            })
        return result
