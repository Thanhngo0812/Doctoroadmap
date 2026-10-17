from __future__ import annotations

import html
import json
import unicodedata

from doc2roadmap.application.stage_measurements import measure_stage
from doc2roadmap.domain.canonical import digest
from doc2roadmap.application.graph_chain import graph_chain_fields
from doc2roadmap.application.planning import StagePlan
from doc2roadmap.domain.roadmap import reviewed_sessions
from doc2roadmap.domain.sequence import (DEFAULT_WEIGHTS, build_sequence_roadmap, target_modules,
                                         soften_backward_edges, transitive_reduction, module_dependencies)
from doc2roadmap.domain.teaching import EXCLUDED_STATUSES, bypass_excluded
from doc2roadmap.domain.anchors import symbolic_name_chunks
from doc2roadmap.domain.mentions import exact_mentions
from doc2roadmap.domain.module_titles import transfer_chunk_sections

_FAR = 10**9


def render_roadmap_html(payload):
    node_by_id = {node["node_id"]: node for node in [*payload["nodes"], *payload.get("excluded_nodes", []),
                                                      *payload.get("mentioned_nodes", []),
                                                      *payload.get("non_learnable_nodes", [])]}
    names = {node_id: node.get("display_name") or node.get("name", node_id) for node_id, node in node_by_id.items()}
    module_rows = []
    for module in payload["modules"]:
        items = []
        for node_id in module["node_ids"]:
            node = node_by_id[node_id]
            direct = node.get("display_prerequisites", node.get("prerequisites", []))
            needs = ", ".join(names.get(parent, parent) for parent in direct)
            more = node.get("display_prerequisites_more_count", 0)
            if more:
                needs += f" và {more} khái niệm khác"
            extra = f" <small>— cần: {html.escape(needs)}</small>" if needs else ""
            items.append(f"<li>{html.escape(names[node_id])}{extra}</li>")
        mentions = "".join(f"<li>{html.escape(names[node_id])}</li>"
                           for node_id in module.get("mentioned_node_ids", []))
        aside = f"<h3>Nhắc tới</h3><ul>{mentions}</ul>" if mentions else ""
        prior = ", ".join(module_id.replace("module_", "") for module_id in module.get("module_dependencies", []))
        prior = f"<p>Học trước: module {html.escape(prior)}</p>" if prior else ""
        description = ''.join('<p>' + html.escape(sentence['text']) + '</p>'
                              for sentence in module.get('description', []) if isinstance(sentence, dict))
        code = ('<small>Mục ' + html.escape(module['section_code']) + '</small>') if module.get('section_code') else ''
        module_rows.append(
            f'<section><h2>{module["index"] + 1}. {html.escape(module["title"])}</h2>{code}{description}{prior}<ol>{"".join(items)}</ol>{aside}</section>'
        )
    excluded_rows = []
    for status, heading in (("prior_knowledge", "Kiến thức nền cần có"), ("not_subject_matter", "Không đưa vào lộ trình")):
        members = [node for node in payload.get("excluded_nodes", []) if node.get("teaching_status") == status]
        if members:
            items = "".join(f"<li>{html.escape(node.get('name', node['node_id']))}</li>" for node in members)
            excluded_rows.append(f"<section><h2>{heading}</h2><ul>{items}</ul></section>")
    edge_rows, tool_rows = [], []
    groups = payload.get("overview_groups", {})
    overview = "".join(f"<li>{html.escape(names[node_id])}</li>"
                       for node_id in groups.get("tong_quan", payload.get("overview_mentioned_node_ids", [])))
    overview = f"<section><h2>Tổng quan môn học</h2><ul>{overview}</ul></section>" if overview else ""
    exercises = "".join(f"<li>{html.escape(names[node_id])}</li>"
                        for node_id in groups.get("chi_trong_bai_tap", []))
    exercises = f"<section><h2>Chỉ xuất hiện trong bài tập</h2><ul>{exercises}</ul></section>" if exercises else ""
    for edge in payload.get("requires_edges", []):
        evidence = ", ".join(edge.get("chunk_ids", [])) or "(none)"
        redundant = f' · redundant via {html.escape(" → ".join(edge["redundant_via"]))}' if edge.get("redundant_via") else ""
        row = (
            f"<li>{html.escape(names.get(edge['source'], edge['source']))} → {html.escape(names.get(edge['target'], edge['target']))} · chunks {html.escape(evidence)}{redundant}</li>"
        )
        (tool_rows if edge.get("soft_reason") == "cong_cu" else edge_rows).append(row)
    flags = html.escape(json.dumps(payload.get("display_flags", []), ensure_ascii=False, indent=2))
    return """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Doc2Roadmap review</title><style>body{font-family:system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}section{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}small{color:#666}code,pre{background:#f6f6f6;padding:.75rem;white-space:pre-wrap}</style></head>
<body><h1>Learning roadmap</h1>""" + overview + exercises + "".join(module_rows) + "".join(excluded_rows) + "<h2>Requires edges</h2><ul>" + "".join(edge_rows) + "</ul>" + ("<h2>Cạnh công cụ (không bắt buộc học trước)</h2><ul>" + "".join(tool_rows) + "</ul>" if tool_rows else "") + "<h2>Flags</h2><pre>" + flags + "</pre></body></html>\n"


def _norm(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def target_roadmap(payload, concepts):
    """Lộ trình tới mục tiêu (spec v2, W9): lọc module của một artifact lộ trình, giữ đích và mọi tổ tiên.

    Khái niệm được chọn bằng mã node, tên hoặc alias; một tên khớp nhiều khái niệm thì báo lỗi thay vì đoán.
    """
    if "sequence" not in payload:
        raise ValueError("artifact chưa phải lộ trình dãy học (ADR 0010); chạy lại A10")
    nodes = {node["node_id"]: node for node in payload["nodes"]}
    targets = []
    for query in concepts:
        hits = [query] if query in nodes else [
            node_id for node_id, node in nodes.items()
            if _norm(node.get("name", "")) == _norm(query)
            or _norm(node.get("display_name", "")) == _norm(query)
            or _norm(query) in {_norm(alias["name"] if isinstance(alias, dict) else alias)
                                for alias in node.get("aliases", [])}
        ]
        if not hits:
            raise ValueError(f"không có khái niệm {query!r} trên lộ trình")
        if len(hits) > 1:
            raise ValueError(f"{query!r} khớp nhiều khái niệm: {sorted(hits)}")
        targets.append(hits[0])
    edges = [edge for edge in [*payload.get("requires_edges", []), *payload.get("bypassed_edges", [])]
             if not edge.get("soft")]
    modules = target_modules(payload["modules"], edges, targets)
    dependencies = module_dependencies(payload["modules"], edges)
    chosen_modules = {module["module_id"] for module in modules}
    return {
        "targets": targets,
        "target_module_id": nodes[targets[-1]]["module_id"] if targets else None,
        "concept_count": sum(len(module["node_ids"]) for module in modules),
        "modules": [{
            "module_id": module["module_id"],
            "index": module.get("index"),
            "title": module.get("title"),
            "module_dependencies": [value for value in dependencies[module["module_id"]] if value in chosen_modules],
            "target_node_ids": [node_id for node_id in module["node_ids"] if node_id in targets],
            "concepts": [{
                "node_id": node_id,
                "name": nodes[node_id].get("display_name") or nodes[node_id]["name"],
                "prerequisites": [nodes[parent].get("display_name") or nodes[parent]["name"]
                                  for parent in nodes[node_id].get("prerequisites", [])
                                  if parent in nodes],
            } for node_id in module["node_ids"]],
        } for module in modules],
    }


class BuildRoadmap:
    """A10 neo sách (ADR 0010): dãy học theo thứ tự dạy, chia module liền mạch có thứ tự bên trong."""

    def __init__(self, store, *, stage_cap=8):
        if type(stage_cap) is not int or stage_cap < 1:
            raise ValueError("stage_cap phải là số nguyên dương")
        self.store = store
        self.stage_cap = stage_cap

    def _upstream(self, doc_id, latest):
        artifact = latest
        while artifact.payload.get("stage") not in ("implicit", "identity", "verified", "teaching", "validated"):
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
        return self.store.load_role_chunks(doc_id, version)

    @measure_stage
    def execute(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream=None, planning=False):
        upstream = upstream if upstream is not None else self._upstream(doc_id, self.store.load_latest_graph(doc_id))
        if upstream.payload.get("stage") not in ("implicit", "identity", "verified", "teaching", "validated"):
            raise ValueError("stage roadmap cần artifact validated")
        chunks_artifact = self._chunks(doc_id, upstream)
        reference_version = (chunks_artifact.manifest.get("role_transfer") or {}).get("reference_version")
        title_chunks = self.store.load_chunks(doc_id, reference_version) if reference_version else chunks_artifact
        config = {
            **graph_chain_fields(upstream),
            "algorithm_id": "a10-book-anchored-sequence-v3",
            "upstream_version": upstream.version,
            "upstream_config_hash": upstream.manifest["config_hash"],
            "chunks_version": chunks_artifact.version,
            "title_sections_version": title_chunks.version,
            "eligibility": "taught-or-uncertain-only-with-mentioned-aside-v2",
            "requires_cycles": "assert-dag",
            "module_cap": self.stage_cap,
            "weights": DEFAULT_WEIGHTS,
            "level_rule": "median-concepts-per-section-at-least-half-cap",
            "placement_rule": "content-evidence-before-name-mention-v3",
            "backward_edges": "backward-edges-soft-v1",
        }
        config_hash = digest(config)
        source_hash = digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        if planning:
            return StagePlan("run", remaining_items=1, note="Dãy học và module bằng luật thuần, không gọi mô hình.")

        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks_artifact.result.chunks}
        sections = {section.section_id: section for section in title_chunks.result.sections}
        old_sections = {section.section_id: section for section in chunks_artifact.result.sections}
        section_of = (transfer_chunk_sections(chunks_artifact.result.chunks, title_chunks.result.chunks)
                      if reference_version else {})
        content_chunks = [c for c in chunks_artifact.result.chunks if getattr(c, "role", "noi_dung") == "noi_dung"]

        def place(node, *, mentioned_node=False):
            """Khoá vị trí (chỉ số chunk dạy, vị trí ký tự trong chunk) và chunk dạy sớm nhất."""
            chunk_ids = node.get("defining_chunk_ids", []) if mentioned_node else node.get("teaching_chunk_ids") or []
            # Artifact trước bước neo vẫn dùng provenance; sau neo không được rơi về đoạn chỉ được dùng/nhắc.
            if "teaching_status" not in node:
                chunk_ids = node.get("defining_chunk_ids", [])
            chunks = sorted((chunk_by_id[value] for value in chunk_ids if value in chunk_by_id
                             and getattr(chunk_by_id[value], "role", "noi_dung") == "noi_dung"),
                            key=lambda chunk: (chunk.order_index, chunk.chunk_id))
            if not chunks:
                searchable = [c for c in content_chunks if getattr(c, "text", "")]
                mentions = exact_mentions([node], searchable, common_names=())
                ids = set(mentions) | symbolic_name_chunks(node, searchable)
                chunks = sorted((c for c in searchable if c.chunk_id in ids), key=lambda c: (c.order_index, c.chunk_id))
            if not chunks:
                return (_FAR, _FAR), None
            first = chunks[0]
            offsets = [span["char_start"] for span in node.get("evidence", [])
                       if isinstance(span, dict) and span.get("chunk_id") == first.chunk_id
                       and isinstance(span.get("char_start"), int)]
            return (first.order_index, min(offsets, default=_FAR)), first

        def chain(section_id):
            source = sections if section_id in sections else old_sections
            path, current = [], source.get(section_id)
            while current is not None and current.level >= 1:
                path.append(current.section_id)
                current = source.get(current.parent_section_id)
            return path[::-1]

        # C8: khái niệm không phải kiến thức môn học, hoặc chỉ được liệt kê là kiến thức nền, rời khỏi lộ trình. Cạnh đi
        # qua chúng được co lại để việc bỏ khái niệm không làm mất ràng buộc học trước.
        excluded = sorted((node for node in upstream.payload["nodes"]
                           if node.get("teaching_status") in EXCLUDED_STATUSES), key=lambda node: node["node_id"])
        non_learnable = sorted((node for node in upstream.payload["nodes"] if not node.get("learnable")),
                               key=lambda node: node["node_id"])
        mentioned = sorted((node for node in upstream.payload["nodes"]
                            if node.get("teaching_status") in {"mentioned_only", "unchecked"}),
                           key=lambda node: node["node_id"])
        excluded_ids = {node["node_id"] for node in [*excluded, *mentioned]}
        edges, bypassed = bypass_excluded(upstream.payload["requires_edges"], excluded_ids)
        placed = [node for node in upstream.payload["nodes"] if node.get("learnable") and node["node_id"] not in excluded_ids]
        position, ancestry, taught_sections = {}, {}, {}
        for node in placed:
            key, chunk = place(node)
            position[node["node_id"]] = key
            section_id = (section_of.get(chunk.chunk_id) or chunk.parent_section_id) if chunk is not None else None
            ancestry[node["node_id"]] = chain(section_id)
            taught_sections[node["node_id"]] = section_id
        hard_edges, soft_edges = soften_backward_edges(edges, position)
        soft_pairs = {(edge["source"],edge["target"]) for edge in soft_edges}
        displayed_edges = [({**edge,"soft":True,"soft_reason":"ngược thứ tự sách"}
                            if (edge["source"],edge["target"]) in soft_pairs and not edge.get("soft")
                            else edge) for edge in upstream.payload["requires_edges"]]
        effective_bypassed = [({**edge,"soft":True,"soft_reason":"ngược thứ tự sách"}
                               if (edge["source"],edge["target"]) in soft_pairs else edge)
                              for edge in bypassed]
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
            hard_edges,
            position=position,
            ancestry=ancestry,
            section_titles={section_id: section.title for section_id, section in {**old_sections, **sections}.items()},
            width=self.stage_cap,
            reviewed=reviewed,
        )
        for module in roadmap["modules"]:
            module["title_section_ids"] = [taught_sections.get(node_id) for node_id in module["node_ids"]]
        direct = transitive_reduction(hard_edges)
        for node in roadmap["nodes"]:
            prerequisites = [parent for parent in node["prerequisites"] if (parent, node["node_id"]) in direct]
            node["display_prerequisites"] = prerequisites[:3]
            node["display_prerequisites_more_count"] = max(0, len(prerequisites) - 3)
        dependencies = module_dependencies(roadmap["modules"], hard_edges)
        for module in roadmap["modules"]:
            module["module_dependencies"] = dependencies[module["module_id"]]
        for module in roadmap["modules"]:
            module["mentioned_node_ids"] = []
        mention_rows = []
        overview_groups = {key: [] for key in ("tong_quan", "chi_trong_bai_tap", "thong_tin_hoc_phan", "cuoi_sach", "khong_ro")}

        def add_overview(node):
            regions = node.get("mentioned_in") or []
            regions = {regions} if isinstance(regions, str) else set(regions)
            for group, accepted in (("tong_quan", {"de_cuong", "mo_dau"}),
                                    ("chi_trong_bai_tap", {"bai_tap"}),
                                    ("thong_tin_hoc_phan", {"hanh_chinh"}),
                                    ("cuoi_sach", {"cuoi_sach"})):
                if regions & accepted:
                    overview_groups[group].append(node["node_id"])
                    return
            overview_groups["khong_ro"].append(node["node_id"])

        for node in mentioned:
            key, chunk = place(node, mentioned_node=True)
            if chunk is None:
                add_overview(node)
                mention_rows.append({**node, "mention_module_id": None})
                continue
            # Mention belongs to the last module whose taught content starts no later than the mention.
            candidates = [(position[node_id], module["index"], module)
                          for module in roadmap["modules"] for node_id in module["node_ids"]
                          if position[node_id] <= key]
            module = max(candidates, key=lambda row:(row[0],row[1]))[2] if candidates else (
                roadmap["modules"][0] if roadmap["modules"] else None)
            if module:
                module["mentioned_node_ids"].append(node["node_id"])
            else:
                add_overview(node)
            mention_rows.append({**node, "mention_module_id": module["module_id"] if module else None})
        stats = {
            "module_count": len(roadmap["modules"]),
            "concept_count": len(roadmap["sequence"]),
            "excluded_node_count": len(excluded),
            "mentioned_node_count": len(mentioned),
            "soft_backward_edge_count": sum(edge.get("soft_reason")=="ngược thứ tự sách" for edge in soft_edges),
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
            "non_learnable_nodes": non_learnable,
            "mentioned_nodes": mention_rows,
            "overview_groups": overview_groups,
            "overview_mentioned_node_ids": overview_groups["tong_quan"],
            "requires_edges": displayed_edges,
            "bypassed_edges": effective_bypassed,
            "soft_backward_edges": [edge for edge in soft_edges if edge.get("soft_reason")=="ngược thứ tự sách"],
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
