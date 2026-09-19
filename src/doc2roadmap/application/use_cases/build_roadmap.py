from __future__ import annotations

import html
import json

from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.roadmap import build_roadmap


def render_roadmap_html(payload):
    names = {node["node_id"]: node.get("name", node["node_id"]) for node in payload["nodes"]}
    stage_rows = []
    for stage in payload["stages"]:
        concepts = "".join(f"<li>{html.escape(names[node_id])}</li>" for node_id in stage["node_ids"])
        stage_rows.append(
            f'<section><h2>{html.escape(stage["stage_id"])} · layer {stage["layer"]}</h2><ul>{concepts}</ul></section>'
        )
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
<title>Doc2Roadmap review</title><style>body{font-family:system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}section{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}code,pre{background:#f6f6f6;padding:.75rem;white-space:pre-wrap}</style></head>
<body><h1>Learning roadmap</h1>""" + "".join(stage_rows) + "<h2>Requires edges</h2><ul>" + "".join(edge_rows) + "</ul><h2>Flags</h2><pre>" + flags + "</pre></body></html>\n"


class BuildRoadmap:
    def __init__(self, store, *, stage_cap=8):
        if type(stage_cap) is not int or not 5 <= stage_cap <= 8:
            raise ValueError("stage_cap phải nằm trong [5, 8]")
        self.store = store
        self.stage_cap = stage_cap

    def _validated(self, doc_id, latest):
        artifact = latest
        while artifact.payload.get("stage") != "validated":
            if artifact.payload.get("stage") == "clusters":
                raise ValueError("stage roadmap cần artifact validated")
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("stage roadmap cần artifact validated")
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    def execute(self, doc_id, *, upstream=None):
        validated = upstream if upstream is not None else self._validated(
            doc_id, self.store.load_latest_graph(doc_id)
        )
        if validated.payload.get("stage") != "validated":
            raise ValueError("stage roadmap cần artifact validated")
        config = {
            "algorithm_id": "a10-kahn-stage-v5",
            "validated_version": validated.version,
            "validated_config_hash": validated.manifest["config_hash"],
            "stage_rule": "layer-intersection-topic-cluster",
            "kahn_queue": "global-node-id-min-heap",
            "requires_cycles": "contract-two-node-scc-reject-larger-v1",
            "stage_cap": self.stage_cap,
            "fallback": "document-order-when-quality-gate-fails",
        }
        config_hash = digest(config)
        source_hash = digest(validated.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True
        invalid_sessions = {
            flag.get("session_id")
            for flag in validated.payload.get("main_flags", [])
            if flag.get("kind") == "invalid_main_session"
        }
        roadmap = build_roadmap(
            validated.payload["nodes"],
            validated.payload["requires_edges"],
            [
                session
                for session in validated.payload.get("main_sessions", [])
                if session.get("session_id") not in invalid_sessions
            ],
            validated.payload.get("completed_secondary_pairs", []),
            validated.payload.get("suspected_pairs", []),
            stage_cap=self.stage_cap,
            quality_gate=validated.payload["quality_gate"],
        )
        display_flags = [
            *validated.payload.get("validation_flags", []),
            *roadmap["coverage_flags"],
        ]
        stats = {
            "layer_count": max((node["layer"] for node in roadmap["nodes"]), default=0),
            "stage_count": len(roadmap["stages"]),
            "unreviewed_node_count": len(roadmap["coverage_flags"]),
            "contracted_component_count": len(roadmap["contracted_components"]),
        }
        payload = {
            **validated.payload,
            "stage": "stages",
            "roadmap_mode": roadmap["mode"],
            "nodes": roadmap["nodes"],
            "stages": roadmap["stages"],
            "chunk_stage_map": roadmap["chunk_stage_map"],
            "coverage_flags": roadmap["coverage_flags"],
            "contracted_components": roadmap["contracted_components"],
            "display_flags": display_flags,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=validated.version,
            manifest_fields={"stage": "stages", "roadmap_mode": roadmap["mode"], "stats": stats},
        )
        if artifact.path is not None:
            (artifact.path / "roadmap.html").write_text(
                render_roadmap_html(payload),
                encoding="utf-8",
                newline="\n",
            )
        return artifact, False
