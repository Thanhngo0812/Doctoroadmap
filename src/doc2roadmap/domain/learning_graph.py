from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any

from .source_labels import SourceRegistry


def _norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value)).casefold().split())


def _names(node: dict[str, Any]) -> list[str]:
    result = [node.get("display_name"), node.get("name")]
    for alias in node.get("aliases", []):
        result.append(alias.get("name") if isinstance(alias, dict) else alias)
    return [str(value).strip() for value in result if isinstance(value, str) and value.strip()]


_NAME_QUERY_FILLER = {"là", "gì", "nào", "khái", "niệm", "giải", "thích", "về", "cho", "biết", "theo", "nghĩa"}


def _is_name_query(query: str, name: str) -> bool:
    remainder = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", " ", query).strip(" ?!.,:;\t\r\n")
    return not remainder or set(remainder.split()) <= _NAME_QUERY_FILLER


class LearningGraph:
    """Pure read model over one graph artifact and its pinned source chunks."""

    def __init__(self, payload: dict[str, Any], chunks: list[Any], tree=None) -> None:
        self.payload = payload
        all_nodes = [*payload.get("nodes", []), *payload.get("excluded_nodes", []),
                     *payload.get("mentioned_nodes", []), *payload.get("non_learnable_nodes", [])]
        self.nodes = {row["node_id"]: dict(row) for row in all_nodes}
        self.learnable_nodes = {row["node_id"]: dict(row) for row in payload.get("nodes", [])
                                if row.get("learnable")}
        self.modules = {row["module_id"]: dict(row) for row in payload.get("modules", [])}
        self.chunks = {str(_get(row, "chunk_id")): row for row in chunks}
        self.tree = tree
        self.doc_id = payload.get("doc_id")
        self.graph_version = payload.get("graph_version", payload.get("version"))
        self.sources = SourceRegistry(chunks)
        self._module_order = {module_id: int(module.get("index", position))
                              for position, (module_id, module) in enumerate(self.modules.items())}
        self._node_module = {node_id: node.get("module_id") for node_id, node in self.nodes.items()}
        self._chunk_modules = self._make_chunk_modules(payload.get("chunk_module_map", {}))

    def new_source_registry(self) -> SourceRegistry:
        """Create context-local labels so one response cannot affect another's numbering."""
        return SourceRegistry(self.chunks.values())

    def _make_chunk_modules(self, mapping: dict[str, Any]) -> dict[str, list[str]]:
        result = {}
        for chunk_id, row in mapping.items():
            if isinstance(row, dict):
                ids = row.get("all_module_ids") or ([row["module_id"]] if row.get("module_id") else [])
            else:
                ids = [row] if row else []
            result[chunk_id] = [module_id for module_id in ids if module_id in self.modules]
        return result

    def relation(self, module_id: str | None, current_module_id: str | None) -> str:
        if not module_id or module_id not in self._module_order or not current_module_id:
            return "khong_ro"
        if current_module_id not in self._module_order:
            return "khong_ro"
        order = self._module_order[module_id]
        current = self._module_order[current_module_id]
        return "dang_mo" if order == current else "truoc" if order < current else "sau"

    def lookup_concept(self, name: str, *, common_chunk_ratio: float = 0.25) -> dict[str, Any]:
        query = _norm(name)
        if not query:
            return {"matches": []}
        candidates = []
        for node_id, node in self.learnable_nodes.items():
            for label in _names(node):
                normalized = _norm(label)
                # Prefer complete names and long names, with word boundaries around the phrase.
                if query == normalized or re.search(rf"(?<!\w){re.escape(normalized)}(?!\w)", query):
                    candidates.append((len(normalized), node_id, label))
        if not candidates:
            return {"matches": []}
        longest = max(row[0] for row in candidates)
        best = [row for row in candidates if row[0] == longest]
        common_ids = set()
        for _, node_id, label in best:
            chunks_with_name = sum(
                label.casefold() in str(_get(chunk, "text", "")).casefold()
                for chunk in self.chunks.values()
            )
            if (self.chunks and chunks_with_name >= max(3, int(len(self.chunks) * common_chunk_ratio) + 1)
                    and chunks_with_name / len(self.chunks) > common_chunk_ratio):
                common_ids.add(node_id)
        # A common word is accepted only when the query is essentially just that name.
        if common_ids:
            best = [row for row in best if row[1] not in common_ids
                    or _is_name_query(query, row[2].casefold())]
        matches = []
        for _, node_id, matched_name in sorted(set(best), key=lambda row: row[1]):
            node = self.nodes[node_id]
            matches.append({
                "node_id": node_id,
                "name": node.get("display_name") or node.get("name"),
                "module_id": self._node_module.get(node_id),
                "match": "ten",
                "matched_name": matched_name,
            })
        return {"matches": matches[:3]}

    def get_module_info(self, module_id: str, current_module_id: str | None = None) -> dict[str, Any]:
        module = self.modules.get(module_id)
        if module is None:
            return {"module_id": module_id, "found": False}
        return {
            "module_id": module_id,
            "found": True,
            "index": module.get("index"),
            "title": module.get("display_name") or module.get("title"),
            "description": (module.get("description") or "")[:320],
            "node_ids": list(module.get("node_ids", []))[:8],
            "more_node_count": max(0, len(module.get("node_ids", [])) - 8),
            "relation": self.relation(module_id, current_module_id),
        }

    def why_here(self, node_id: str, current_module_id: str | None = None, *, source_registry=None) -> dict[str, Any]:
        node = self.nodes.get(node_id)
        if node is None:
            return {"node_id": node_id, "found": False, "prerequisites": []}
        sources = source_registry or self.sources
        direct_ids = node.get("display_prerequisites")
        if direct_ids is None:
            from .sequence import transitive_reduction
            candidates = [edge for edge in self.payload.get("requires_edges", [])
                          if edge.get("edge_type", "requires") == "requires" and not edge.get("soft")]
            direct_pairs = transitive_reduction(candidates)
            direct_ids = [source for source, target in direct_pairs if target == node_id]
        edges = []
        for parent_id in direct_ids:
            edge = next((candidate for candidate in self.payload.get("requires_edges", [])
                         if candidate.get("source") == parent_id and candidate.get("target") == node_id
                         and candidate.get("edge_type", "requires") == "requires"), None)
            if edge is not None:
                edges.append(edge)
        edges.sort(key=lambda edge: (bool(edge.get("soft")), edge.get("source", "")))
        prerequisites = []
        for edge in edges[:3]:
            parent = self.nodes.get(edge.get("source"), {})
            child = self.nodes.get(edge.get("target"), {})
            cited = _edge_citation(edge, parent, child, self.chunks, sources)
            label, citation, citation_kind = cited if cited else (None, None, None)
            if not citation:
                continue
            quote = citation["quote"]
            legacy_excerpt = citation_kind == "legacy_excerpt"
            source_chunk = citation["chunk_id"]
            parent_anchor = parent.get("anchor") or {}
            anchor_chunk = parent_anchor.get("chunk_id")
            anchor = sources.citation_for_chunk(anchor_chunk, "N", _bounded_quote(parent_anchor.get("sentence", ""))) \
                if anchor_chunk in self.chunks else None
            anchor_label, anchor_citation = anchor if anchor else (None, None)
            prerequisites.append({
                "node_id": edge.get("source"),
                "name": parent.get("display_name") or parent.get("name"),
                "module_id": parent.get("module_id"),
                "quote": quote,
                "source_label": label,
                "citation": citation,
                "citation_source": "legacy_excerpt" if legacy_excerpt else "quoted_evidence",
                "warning": "missing_edge_quote" if legacy_excerpt else None,
                "anchor_label": anchor_label,
                "anchor_citation": anchor_citation,
                "page": _get(self.chunks.get(source_chunk), "page"),
                "soft_reason": edge.get("soft_reason"),
                "order_relation": ("sach_trinh_bay_o_phan_sau"
                                   if self.relation(parent.get("module_id"), node.get("module_id")) == "sau"
                                   else None),
                "note": ("Đoạn liên quan; artifact cũ thiếu câu trích bằng chứng của cạnh"
                         if legacy_excerpt else
                         "công cụ, không bắt buộc" if edge.get("soft_reason") == "cong_cu" else None),
            })
        return {"node_id": node_id, "found": True, "prerequisites": prerequisites,
                "current_relation": self.relation(node.get("module_id"), current_module_id)}

    def path_to(self, node_id: str) -> dict[str, Any]:
        if node_id not in self.nodes:
            return {"node_id": node_id, "found": False, "modules": []}
        target_module = self._node_module.get(node_id)
        if not target_module:
            return {"node_id": node_id, "found": True, "modules": [], "module_id": None}
        parents = defaultdict(set)
        for edge in self.payload.get("requires_edges", []):
            if edge.get("edge_type", "requires") != "requires" or edge.get("soft"):
                continue
            source_module = self._node_module.get(edge.get("source"))
            dest_module = self._node_module.get(edge.get("target"))
            if source_module and dest_module and source_module != dest_module:
                parents[dest_module].add(source_module)
        needed, queue = {target_module}, [target_module]
        while queue:
            current = queue.pop()
            for parent in parents[current] - needed:
                needed.add(parent)
                queue.append(parent)
        rows = [self.modules[module] for module in needed]
        rows.sort(key=lambda module: (self._module_order.get(module["module_id"], 10**9), module["module_id"]))
        shown = rows[:12]
        omitted = len(rows) - len(shown)
        return {"node_id": node_id, "found": True, "target_module_id": target_module,
                "modules": [{"module_id": row["module_id"], "index": row.get("index"),
                             "title": row.get("display_name") or row.get("title")} for row in shown],
                "omitted_module_count": omitted,
                "omitted_note": f"và {omitted} module nữa" if omitted else None}

    def traverse(self, node_id: str, edge_type: str, direction: str = "out") -> dict[str, Any]:
        if direction not in {"out", "in"}:
            raise ValueError("direction phải là 'out' hoặc 'in'")
        if node_id not in self.nodes:
            return {"node_id": node_id, "edges": []}
        if edge_type == "requires":
            edges = self.payload.get("requires_edges", [])
        else:
            edges = [*self.payload.get("open_edges", []), *self.payload.get("recommended_edges", [])]
        result = []
        for edge in edges:
            if edge.get("edge_type") != edge_type or edge.get("soft"):
                continue
            if edge_type == "requires" and edge not in self.payload.get("requires_edges", []):
                continue
            if edge_type != "requires" and (not edge.get("quote") or edge.get("confirmed") is False):
                continue
            if edge_type == "requires" and not edge.get("quote"):
                continue
            source, target = edge.get("source"), edge.get("target")
            if (source if direction == "out" else target) != node_id:
                continue
            other_id = target if direction == "out" else source
            result.append({"source": source, "target": target, "edge_type": edge_type,
                           "node_id": other_id, "quote": edge.get("quote"),
                           "chunk_ids": list(edge.get("chunk_ids", []))[:3],
                           "source_refs": list(edge.get("source_refs", []))[:3],
                           "soft_reason": edge.get("soft_reason")})
            if len(result) == 5:
                break
        return {"node_id": node_id, "edges": result}

    def get_media(self, node_id: str) -> list[dict[str, Any]]:
        media_nodes = {node_id: node for node_id, node in self.nodes.items() if node.get("media_id")}
        result = []
        for edge in self.payload.get("open_edges", []):
            if edge.get("edge_type") not in {"illustrates", "tabulates"} or not edge.get("confirmed"):
                continue
            if node_id not in {edge.get("source"), edge.get("target")}:
                continue
            media_id = edge.get("target") if edge.get("source") == node_id else edge.get("source")
            media = media_nodes.get(media_id)
            if not media:
                continue
            result.append({"node_id": media_id, "media_id": media.get("media_id"),
                           "name": media.get("display_name") or media.get("name"),
                           "caption": media.get("caption"), "caption_source": media.get("caption_source"),
                           "page": media.get("page"),
                           "image_refs": media.get("image_refs", []),
                           "source_refs": media.get("source_refs", [])})
            if len(result) >= 2:
                break
        return result


def _get(item: Any, key: str, default=None):
    if item is None:
        return default
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


def _edge_citation(edge, source_node, target_node, chunks, sources):
    candidates = []
    quote = edge.get("quote")
    if quote:
        candidates.extend((chunk_id, quote) for chunk_id in edge.get("chunk_ids", []))
    for evidence in edge.get("evidence", []):
        if isinstance(evidence, dict) and evidence.get("chunk_id") and evidence.get("quote"):
            candidates.append((evidence["chunk_id"], evidence["quote"]))
    for source_ref in edge.get("source_refs", []):
        if isinstance(source_ref, dict) and source_ref.get("chunk_id") and source_ref.get("quote"):
            candidates.append((source_ref["chunk_id"], source_ref["quote"]))
    for chunk_id, source_quote in candidates:
        if chunk_id in chunks:
            bounded = _bounded_quote(source_quote)
            citation = sources.citation_for_chunk(chunk_id, "Q", bounded)
            if citation:
                return (*citation, "quoted_evidence")
    # Older A8 graph artifacts contain evidence chunk IDs and a generated reason,
    # but no quoted text. Cite a short, contiguous source excerpt naming both ends.
    for chunk_id in edge.get("chunk_ids", []):
        chunk = chunks.get(chunk_id)
        if chunk is None:
            continue
        excerpt = _edge_excerpt(str(_get(chunk, "text", "")), source_node, target_node)
        if excerpt:
            citation = sources.citation_for_chunk(chunk_id, "S", _bounded_quote(excerpt))
            if citation:
                return (*citation, "legacy_excerpt")
    return None


def _bounded_quote(value: str, limit: int = 120) -> str:
    value = str(value).strip()
    if len(value) <= limit:
        return value
    prefix = value[:limit]
    boundary = prefix.rfind(" ")
    return prefix[:boundary] if boundary > limit // 2 else prefix


def _edge_excerpt(text: str, source_node: dict, target_node: dict) -> str | None:
    def occurrences(node):
        found = []
        for name in _names(node):
            phrase = r"\s+".join(re.escape(part) for part in name.split())
            if not phrase:
                continue
            found.extend((match.start(), match.end()) for match in re.finditer(phrase, text, re.IGNORECASE))
        return found

    left, right = occurrences(source_node), occurrences(target_node)
    pairs = [(min(a[0], b[0]), max(a[1], b[1])) for a in left for b in right if a != b]
    if not pairs:
        return None
    start, end = min(pairs, key=lambda span: span[1] - span[0])
    line_start = text.rfind("\n", 0, start) + 1
    newline = text.find("\n", end)
    line_end = len(text) if newline < 0 else newline
    if line_end - line_start <= 400:
        start, end = line_start, line_end
    excerpt = text[start:end].strip()
    return excerpt if excerpt and len(excerpt) <= 900 else None
