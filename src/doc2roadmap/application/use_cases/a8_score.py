"""Chấm E1 và E2 từ bộ vàng và artifact `graph`. Không gọi mô hình, chạy được khi chặn mạng.

Bộ chấm đọc **artifact**, không gọi vào code của pipeline: đầu vào là payload `graph` (stage `mentions` trở đi),
cộng canonical và chunks đúng phiên bản mà bộ vàng đã gán.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from doc2roadmap.application.use_cases.a8_gold import annotation_scope, chapter_lookup, scope_inputs
from doc2roadmap.domain.gold_scoring import (
    POSITION_LABELS,
    POSITIONS,
    agreement,
    bootstrap_interval,
    classify_positions,
    coverage_rows,
    generator_rows,
    gold_order_violations,
    metric_by_target,
    normalized_mutual_information,
    pairs_within,
    position_counts,
    presentation_agreement,
    recall_by_target,
    score_edges,
    share_by_target,
    subset_rows,
    undirected,
)

GRAPH_STAGES = ("mentions", "provenance", "edges", "validated", "stages")
GOLD_MODES = ("union", "intersection")


def load_gold(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("errors"):
        raise ValueError(f"{path}: bộ vàng còn lỗi chưa sửa, chấm sẽ sai — {value['errors'][0]}")
    for key in ("doc_id", "canonical_version", "chapter", "concept_hash", "targets", "edges"):
        if key not in value:
            raise ValueError(f"{path}: thiếu trường {key}; đây có phải đầu ra của a8-gold-check không?")
    return value


def gold_edges(gold: dict[str, Any]) -> set[tuple[str, str]]:
    return {(edge["prerequisite"], edge["target"]) for edge in gold["edges"]}


def merge_gold(golds, *, mode: str) -> set[tuple[str, str]]:
    if mode not in GOLD_MODES:
        raise ValueError(f"cách gộp bộ vàng phải là {' hoặc '.join(GOLD_MODES)}")
    sets = [gold_edges(gold) for gold in golds]
    merged = set(sets[0])
    for value in sets[1:]:
        merged = merged | value if mode == "union" else merged & value
    return merged


def load_graph_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("stage") not in GRAPH_STAGES:
        raise ValueError(f"{path}: cần artifact graph ở stage {', '.join(GRAPH_STAGES)}, đang là {payload.get('stage')!r}")
    for key in ("nodes", "mention_map", "suspected_pairs"):
        if key not in payload:
            raise ValueError(f"{path}: artifact thiếu {key}")
    return payload


def _check_same_concepts(scope, payload, gold):
    if gold["concept_hash"] != scope["concept_hash"]:
        raise ValueError(
            "bộ vàng gán cho danh sách khái niệm khác với canonical đang dùng; sinh lại file gán hoặc chấm đúng "
            f"phiên bản (vàng {gold['concept_hash'][:12]}…, canonical {scope['concept_hash'][:12]}…)"
        )
    scope_ids = {concept["node_id"] for concept in scope["concepts"]}
    graph_ids = {node["node_id"] for node in payload["nodes"] if node.get("learnable")}
    missing = sorted(scope_ids - graph_ids)
    if missing:
        raise ValueError(f"artifact graph thiếu {len(missing)} khái niệm của bộ vàng, ví dụ {missing[0]}")


def with_source_provenance(payload):
    """Bản payload dùng provenance gốc của A3/A4, để so E1 trước và sau khi vá (spec vá, mục Luật chấm)."""
    missing = [node for node in payload["nodes"] if "defining_chunk_ids_source" not in node]
    if missing:
        raise ValueError("artifact chưa qua stage provenance nên không có defining_chunk_ids_source để so")
    return {
        **payload,
        "nodes": [
            {**node, "defining_chunk_ids": list(node["defining_chunk_ids_source"])}
            for node in payload["nodes"]
        ],
    }


def _context(payload, chunks, sections, *, chapter_level):
    chapter_of_section = chapter_lookup(sections, chapter_level)
    section_of_chunk, chapter_of_chunk = {}, {}
    for chunk in chunks:
        section_of_chunk[chunk.chunk_id] = chunk.parent_section_id
        chapter_of_chunk[chunk.chunk_id] = chapter_of_section(chunk.parent_section_id)
    learnable = [node for node in payload["nodes"] if node.get("learnable")]
    return {
        "provenance": {node["node_id"]: list(node.get("defining_chunk_ids", [])) for node in learnable},
        "section_of_chunk": section_of_chunk,
        "chapter_of_chunk": chapter_of_chunk,
        "cluster_of_node": {node["node_id"]: node.get("cluster_id") for node in learnable},
        "mention_map": payload["mention_map"],
    }


def _sources_by_pair(payload):
    rows = {}
    for row in payload.get("suspected_pairs", []):
        rows[frozenset((row["left"], row["right"]))] = set(row.get("sources", []))
    return rows


def _axis_groups(payload, context, chunks):
    """Nhóm khái niệm theo hai trục của D6, để đo cấu hình định tuyến của E2.

    Đây là **định nghĩa đo**, dựng lại từ artifact: một cặp "nhìn thấy được" trên một trục khi hai khái niệm cùng
    nằm trong một phiên của trục đó — phiên theo mục (trục chương) hoặc theo cụm chủ đề (trục cụm).
    """
    learnable = {node["node_id"] for node in payload["nodes"] if node.get("learnable")}
    mention_map = payload["mention_map"]
    chunks_of_section = {}
    for chunk in chunks:
        chunks_of_section.setdefault(chunk.parent_section_id, []).append(chunk.chunk_id)
    def allowed(chunk_ids, targets):
        result = set(targets)
        for chunk_id in chunk_ids:
            result.update(node_id for node_id in mention_map.get(chunk_id, {}) if node_id in learnable)
        return result
    section_groups = []
    for section_id, chunk_ids in sorted(chunks_of_section.items()):
        targets = {
            node_id for node_id, provenance in context["provenance"].items()
            if set(provenance) & set(chunk_ids)
        }
        if targets:
            section_groups.append(allowed(chunk_ids, targets))
    cluster_members = {}
    for node_id, cluster_id in context["cluster_of_node"].items():
        cluster_members.setdefault(cluster_id, set()).add(node_id)
    cluster_groups = []
    for cluster_id, members in sorted(cluster_members.items(), key=lambda item: str(item[0])):
        chunk_ids = sorted({c for node_id in members for c in context["provenance"].get(node_id, ())})
        cluster_groups.append(allowed(chunk_ids, members))
    return section_groups, cluster_groups


def score_gold(scope, payload, chunks, sections, golds, *, mode="union", samples=2000, seed=20260918):
    """Báo cáo E1 và E2 cho một bộ vàng (hoặc hai bộ đã gộp)."""
    for gold in golds:
        _check_same_concepts(scope, payload, gold)
    chapter_level = scope["chapter_level"]
    context = _context(payload, chunks, sections, chapter_level=chapter_level)
    targets = sorted({node_id for gold in golds for node_id in gold["targets"]})
    concepts = sorted(context["cluster_of_node"])
    edges = merge_gold(golds, mode=mode) if len(golds) > 1 else gold_edges(golds[0])
    edges = {(prerequisite, target) for prerequisite, target in edges if target in set(targets)}
    rows = classify_positions(edges, **context)
    counts = position_counts(rows)
    total = sum(counts.values())
    positions = [
        {
            "position": position,
            "label": POSITION_LABELS[position],
            "count": counts[position],
            "share": counts[position] / total if total else None,
            "interval": bootstrap_interval(targets, share_by_target(rows, position, targets),
                                           samples=samples, seed=seed),
        }
        for position in POSITIONS
    ]
    chapter_of_node = {}
    for node_id, provenance in context["provenance"].items():
        chapters = sorted({context["chapter_of_chunk"].get(c) for c in provenance} - {None})
        if chapters:
            chapter_of_node[node_id] = chapters[0]
    gold_pairs = undirected(edges)
    sources = _sources_by_pair(payload)
    section_groups, cluster_groups = _axis_groups(payload, context, chunks)
    chapter_axis, cluster_axis = pairs_within(section_groups), pairs_within(cluster_groups)
    coverage = {
        "chapter_axis": chapter_axis,
        "cluster_axis": cluster_axis,
        "both_axes": chapter_axis | cluster_axis,
        "generators_union": set(sources),
        "chapter_axis_plus_generators": chapter_axis | set(sources),
        "both_axes_plus_generators": chapter_axis | cluster_axis | set(sources),
    }
    report = {
        "doc_id": scope["doc_id"],
        "canonical_version": scope["canonical_version"],
        "chapter": scope["chapter"],
        "chapter_level": chapter_level,
        "graph_stage": payload.get("stage"),
        "gold": {
            "annotators": [gold.get("annotator") for gold in golds],
            "mode": mode if len(golds) > 1 else "single",
            "targets": len(targets),
            "concepts": len(concepts),
            "edges": len(edges),
            "edges_per_target": len(edges) / len(targets) if targets else None,
        },
        "bootstrap": {"samples": samples, "seed": seed, "unit": "khái niệm đích"},
        "e1": {
            "positions": positions,
            "nmi_cluster_chapter": normalized_mutual_information(context["cluster_of_node"], chapter_of_node),
            "nmi_nodes": len(set(context["cluster_of_node"]) & set(chapter_of_node)),
        },
        "e2": {
            "generators": [
                {
                    **row,
                    "interval": bootstrap_interval(
                        targets,
                        recall_by_target(edges, {pair for pair, values in sources.items() if row["generator"] in values}),
                        samples=samples, seed=seed,
                    ),
                }
                for row in generator_rows(gold_pairs, sources)
            ],
            "subsets": subset_rows(gold_pairs, sources),
            "routing": [
                {
                    **row,
                    "interval": bootstrap_interval(
                        targets, recall_by_target(edges, coverage[row["configuration"]]),
                        samples=samples, seed=seed,
                    ),
                }
                for row in coverage_rows(gold_pairs, coverage)
            ],
        },
    }
    if len(golds) == 2:
        first, second = gold_edges(golds[0]), gold_edges(golds[1])
        report["gold"]["agreement"] = {
            "direct": agreement(first, second, targets=targets, concepts=concepts),
            "transitive": agreement(first, second, targets=targets, concepts=concepts, transitive=True),
        }
    predicted = _predicted_edges(payload, context)
    if predicted is not None:
        report["prediction"] = _prediction_section(predicted, edges, targets, samples=samples, seed=seed)
    return report


def _predicted_edges(payload, context):
    rows = payload.get("requires_edges")
    if rows is None:
        rows = payload.get("main_edges")
        if rows is not None:
            rows = list(rows) + list(payload.get("secondary_edges", []))
    if rows is None:
        return None
    learnable = set(context["cluster_of_node"])
    return {
        (edge["source"], edge["target"])
        for edge in rows
        if edge.get("edge_type", "requires") == "requires"
        and edge["source"] in learnable
        and edge["target"] in learnable
    }


def _prediction_section(predicted, gold, targets, *, samples, seed):
    section = {"source": "artifact", "edges": len(predicted)}
    for name, closure in (("direct", False), ("closure", True)):
        scores = score_edges(predicted, gold, targets=targets, closure=closure)
        section[name] = {
            **scores,
            "intervals": {
                metric: bootstrap_interval(
                    targets, metric_by_target(predicted, gold, metric=metric, closure=closure),
                    samples=samples, seed=seed,
                )
                for metric in ("precision", "recall", "f1")
            },
        }
    return section


def score_from_store(store, doc_id, graph_path, gold_paths, *, mode="union", samples=2000, seed=20260918,
                     provenance="patched"):
    if provenance not in ("patched", "source"):
        raise ValueError("provenance phải là 'patched' hoặc 'source'")
    golds = [load_gold(path) for path in gold_paths]
    if len({gold["doc_id"] for gold in golds}) != 1 or golds[0]["doc_id"] != doc_id:
        raise ValueError("các file vàng phải cùng một doc_id với tham số --doc-id")
    if len({(gold["canonical_version"], json.dumps(gold["chapter"], sort_keys=True)) for gold in golds}) != 1:
        raise ValueError("các file vàng phải cùng một chương và cùng phiên bản canonical")
    payload = load_graph_payload(graph_path)
    if payload.get("doc_id") not in (None, doc_id):
        raise ValueError(f"artifact graph thuộc {payload['doc_id']!r}, không phải {doc_id!r}")
    first = golds[0]
    inputs = scope_inputs(store, doc_id, first["canonical_version"])
    # Danh tính khái niệm phải dựng từ **đúng payload đã sinh bảng gán**: D13 bắt cột "Nơi dạy" đi theo
    # provenance đã vá, nên bảng gán nào cũng sinh có `--graph`. Dựng scope từ canonical thô thì `concept_hash`
    # lệch và bộ chấm tự từ chối mọi bộ vàng thật (F124).
    scope = annotation_scope(
        doc_id, inputs["version"], inputs["nodes"], inputs["sections"], inputs["chunks"],
        graph_payload=payload,
        chapter=",".join(first["chapter"]["section_ids"]), chapter_level=first["chapter_level"],
    )
    # Đổi về provenance gốc **sau** khi đã chốt danh tính, vì chế độ này chỉ để so E1 trước và sau khi vá.
    if provenance == "source":
        payload = with_source_provenance(payload)
    report = score_gold(scope, payload, inputs["chunks"], inputs["sections"], golds,
                        mode=mode, samples=samples, seed=seed)
    report["graph_path"] = str(graph_path)
    report["provenance_mode"] = provenance
    return report


def score_roadmap_order(graph_path: Path, gold_paths, *, mode: str = "union") -> dict[str, Any]:
    """Chấm **thứ tự** của lộ trình: τ so mục lục, và cạnh vàng nào bị xếp ngược.

    Hai chỉ số tách bạch. τ đo lộ trình lệch mục lục bao nhiêu — nó là **dấu hiệu chẩn đoán**, không phải mục
    tiêu, vì thứ tự sách không phải chân lý về tiên quyết. Tỉ lệ vi phạm cạnh vàng mới là phép chấm đúng/sai,
    và nó chỉ tính trên cặp mà lộ trình thật sự xếp được thứ tự.
    """
    payload = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    if payload.get("stage") != "stages":
        raise ValueError(f"{graph_path}: cần artifact graph ở stage 'stages', đang là {payload.get('stage')!r}")
    stages = [stage["node_ids"] for stage in payload["stages"]]
    nodes = payload["nodes"]
    names = {node["node_id"]: node.get("name") for node in nodes}
    order = presentation_agreement(
        stages, {node["node_id"]: node.get("first_order_index", 0) for node in nodes}
    )
    report: dict[str, Any] = {
        "doc_id": payload.get("doc_id"),
        "stage_count": len(stages),
        "learnable_node_count": len(nodes),
        "presentation_agreement": order,
        "presentation_caveat": "τ dùng một văn bản tham chiếu duy nhất; có thể có nhiều thứ tự chấp nhận được",
    }
    if not gold_paths:
        return report
    golds = [load_gold(path) for path in gold_paths]
    edges = merge_gold(golds, mode=mode)
    violations = gold_order_violations(stages, edges, names=names)
    report["gold_mode"] = mode
    report["gold_edge_count"] = len(edges)
    report["gold_order"] = {key: value for key, value in violations.items() if key != "rows"}
    report["violations"] = violations["rows"]
    return report
