from __future__ import annotations

import html
import json

from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.roadmap import reviewed_sessions
from doc2roadmap.domain.sequence import DEFAULT_WEIGHTS, build_sequence_roadmap
from doc2roadmap.domain.teaching import EXCLUDED_STATUSES, bypass_excluded

_FAR = 10**9


def render_roadmap_html(payload):
    node_by_id = {node["node_id"]: node for node in [*payload["nodes"], *payload.get("excluded_nodes", [])]}
    names = {node_id: node.get("name", node_id) for node_id, node in node_by_id.items()}
    module_rows = []
    for module in payload["modules"]:
        items = []
        for node_id in module["node_ids"]:
            needs = ", ".join(names.get(parent, parent) for parent in node_by_id[node_id].get("prerequisites", []))
            extra = f" <small>— cần: {html.escape(needs)}</small>" if needs else ""
            items.append(f"<li>{html.escape(names[node_id])}{extra}</li>")
        module_rows.append(
            f'<section><h2>{module["index"] + 1}. {html.escape(module["title"])}</h2><ol>{"".join(items)}</ol></section>'
        )
    excluded_rows = []
    for status, heading in (("prior_knowledge", "Kiến thức nền cần có"), ("not_subject_matter", "Không đưa vào lộ trình")):
        members = [node for node in payload.get("excluded_nodes", []) if node.get("teaching_status") == status]
        if members:
            items = "".join(f"<li>{html.escape(node.get('name', node['node_id']))}</li>" for node in members)
            excluded_rows.append(f"<section><h2>{heading}</h2><ul>{items}</ul></section>")
    edge_rows = []
    for edge in payload.get("requires_edges", []):
        evidence = ", ".join(edge.get("chunk_ids", [])) or "(none)"
        redundant = f' · redundant via {html.escape(" → ".join(edge["redundant_via"]))}' if edge.get("redundant_via") else ""
        edge_rows.append(
            f"<li>{html.escape(names.get(edge['source'], edge['source']))} → {html.escape(names.get(edge['target'], edge['target']))} · chunks {html.escape(evidence)}{redundant}</li>"
        )
    flags = html.escape(json.dumps(payload.get("display_flags", []), ensure_ascii=False, indent=2))
    return """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Doc2Roadmap review</title><style>body{font-family:system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}section{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}small{color:#666}code,pre{background:#f6f6f6;padding:.75rem;white-space:pre-wrap}</style></head>
<body><h1>Learning roadmap</h1>""" + "".join(module_rows) + "".join(excluded_rows) + "<h2>Requires edges</h2><ul>" + "".join(edge_rows) + "</ul><h2>Flags</h2><pre>" + flags + "</pre></body></html>\n"


class BuildRoadmap:
    """A10 neo sách (ADR 0010): dãy học theo thứ tự dạy, chia module liền mạch có thứ tự bên trong."""

    def __init__(self, store, *, stage_cap=8):
        if type(stage_cap) is not int or stage_cap < 1:
            raise ValueError("stage_cap phải là số nguyên dương")
        self.store = store
        self.stage_cap = stage_cap

    def _upstream(self, doc_id, latest):
        artifact = latest
        while artifact.payload.get("stage") not in ("verified", "teaching", "validated"):
            if artifact.payload.get("stage") == "clusters":
                raise ValueError("stage roadmap cần artifact validated")
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("stage roadmap cần artifact validated")
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    def _chunks(self, doc_id, upstream):
        config = upstream.manifest.get("config", {})
        version = config.get("chunks_version")
        if version is None:
            version = self.store.load_graph(doc_id, config["edges_version"]).manifest["config"]["chunks_version"]
        return self.store.load_chunks(doc_id, version)

    def execute(self, doc_id, *, upstream=None):
        upstream = upstream if upstream is not None else self._upstream(doc_id, self.store.load_latest_graph(doc_id))
        if upstream.payload.get("stage") not in ("verified", "teaching", "validated"):
            raise ValueError("stage roadmap cần artifact validated")
        chunks_artifact = self._chunks(doc_id, upstream)
        config = {
            "algorithm_id": "a10-book-anchored-sequence-v1",
            "upstream_version": upstream.version,
            "upstream_config_hash": upstream.manifest["config_hash"],
            "chunks_version": chunks_artifact.version,
            "eligibility": "exclude-prior-knowledge-and-not-subject-matter-v1",
            "requires_cycles": "assert-dag",
            "module_cap": self.stage_cap,
            "weights": DEFAULT_WEIGHTS,
            "level_rule": "median-concepts-per-section-at-least-half-cap",
        }
        config_hash = digest(config)
        source_hash = digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True

        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks_artifact.result.chunks}
        sections = {section.section_id: section for section in chunks_artifact.result.sections}

        def place(node):
            """Khoá vị trí (chỉ số chunk dạy, vị trí ký tự trong chunk) và chunk dạy sớm nhất."""
            chunk_ids = node.get("teaching_chunk_ids") or node.get("defining_chunk_ids", [])
            chunks = sorted((chunk_by_id[value] for value in chunk_ids if value in chunk_by_id),
                            key=lambda chunk: (chunk.order_index, chunk.chunk_id))
            if not chunks:
                order = node.get("teaching_order_index")
                return ((order if order is not None else node.get("first_order_index", _FAR)), _FAR), None
            first = chunks[0]
            offsets = [span["char_start"] for span in node.get("evidence", [])
                       if isinstance(span, dict) and span.get("chunk_id") == first.chunk_id
                       and isinstance(span.get("char_start"), int)]
            return (first.order_index, min(offsets, default=_FAR)), first

        def chain(section_id):
            path, current = [], sections.get(section_id)
            while current is not None and current.level >= 1:
                path.append(current.section_id)
                current = sections.get(current.parent_section_id)
            return path[::-1]

        # C8: khái niệm không phải kiến thức môn học, hoặc chỉ được liệt kê là kiến thức nền, rời khỏi lộ trình. Cạnh đi
        # qua chúng được co lại để việc bỏ khái niệm không làm mất ràng buộc học trước.
        excluded = sorted((node for node in upstream.payload["nodes"]
                           if node.get("teaching_status") in EXCLUDED_STATUSES), key=lambda node: node["node_id"])
        excluded_ids = {node["node_id"] for node in excluded}
        edges, bypassed = bypass_excluded(upstream.payload["requires_edges"], excluded_ids)
        placed = [node for node in upstream.payload["nodes"] if node.get("learnable") and node["node_id"] not in excluded_ids]
        position, ancestry = {}, {}
        for node in placed:
            key, chunk = place(node)
            position[node["node_id"]] = key
            ancestry[node["node_id"]] = chain(chunk.parent_section_id) if chunk is not None else []
        invalid_sessions = {
            flag.get("session_id")
            for flag in upstream.payload.get("main_flags", [])
            if flag.get("kind") == "invalid_main_session"
        }
        reviewed = reviewed_sessions(
            {node["node_id"] for node in placed},
            [session for session in upstream.payload.get("main_sessions", [])
             if session.get("session_id") not in invalid_sessions],
            upstream.payload.get("completed_secondary_pairs", []),
            upstream.payload.get("suspected_pairs", []),
        )
        roadmap = build_sequence_roadmap(
            placed,
            edges,
            position=position,
            ancestry=ancestry,
            section_titles={section_id: section.title for section_id, section in sections.items()},
            width=self.stage_cap,
            reviewed=reviewed,
        )
        stats = {
            "module_count": len(roadmap["modules"]),
            "concept_count": len(roadmap["sequence"]),
            "excluded_node_count": len(excluded),
            "unreviewed_node_count": len(roadmap["coverage_flags"]),
            "longest_path": roadmap["longest_path"],
            "chapter_level": roadmap["levels"]["chapter"],
            "unit_level": roadmap["levels"]["unit"],
        }
        payload = {
            **upstream.payload,
            "stage": "stages",
            "roadmap_mode": roadmap["mode"],
            "nodes": roadmap["nodes"],
            "sequence": roadmap["sequence"],
            "modules": roadmap["modules"],
            "chunk_module_map": roadmap["chunk_module_map"],
            "coverage_flags": roadmap["coverage_flags"],
            "excluded_nodes": excluded,
            "bypassed_edges": bypassed,
            "display_flags": [*upstream.payload.get("validation_flags", []), *roadmap["coverage_flags"]],
            "stats": stats,
        }
        for stale in ("stages", "chunk_stage_map", "contracted_components", "unmergeable_small_stages"):
            payload.pop(stale, None)
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=upstream.version,
            manifest_fields={"stage": "stages", "roadmap_mode": roadmap["mode"], "stats": stats},
        )
        if artifact.path is not None:
            (artifact.path / "roadmap.html").write_text(render_roadmap_html(payload), encoding="utf-8", newline="\n")
        return artifact, False
