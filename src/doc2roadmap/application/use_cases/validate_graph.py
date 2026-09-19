from __future__ import annotations

from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.global_validation import apply_resolved_nodes, validate_graph_rules


class ValidateGraph:
    def __init__(self, store):
        self.store = store

    def _edges(self, doc_id, latest):
        artifact = latest
        while artifact.payload.get("stage") != "edges":
            if artifact.payload.get("stage") == "clusters":
                raise ValueError("artifact graph không trỏ về stage edges")
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("artifact graph không trỏ về stage edges")
            artifact = self.store.load_graph(doc_id, upstream)
        if not artifact.payload.get("main_complete") or not artifact.payload.get("secondary_complete"):
            raise ValueError("tầng validate cần artifact edges hoàn tất cả pass chính và pass phụ")
        return artifact

    def execute(self, doc_id, *, upstream=None):
        edges_artifact = upstream if upstream is not None else self._edges(
            doc_id, self.store.load_latest_graph(doc_id)
        )
        if edges_artifact.payload.get("stage") != "edges":
            raise ValueError("tầng validate cần artifact edges")
        edge_config = edges_artifact.manifest.get("config", {})
        canonical_version = edge_config.get("canonical_version")
        canonical = (
            self.store.load_canonical(doc_id, canonical_version)
            if canonical_version is not None
            else self.store.load_latest_canonical(doc_id)
        )
        aliases = self.store.load_type_aliases()
        config = {
            "algorithm_id": "a9-global-validation-v4",
            "edges_version": edges_artifact.version,
            "edges_config_hash": edges_artifact.manifest["config_hash"],
            "cycle_scope": "requires-learnable-scc",
            "cycle_keep_order": ["evidence_kind", "provenance_order", "independent_source_count", "confidence"],
            "two_edge_cycle": "flag-contract-no-quality-penalty-v2",
            "quality_min_edges_per_learnable": 0.5,
            "quality_max_isolated_ratio": 0.6,
            "redundancy": "mark-only",
            "cycle_exhaustive_edge_limit": 16,
            "cycle_large_component_method": "eades_priority",
            "type_aliases": aliases,
        }
        config_hash = digest(config)
        source_hash = digest([edges_artifact.payload, canonical.payload.get("edges", [])])
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True
        raw_flags = [
            *edges_artifact.payload.get("flags", []),
            *edges_artifact.payload.get("main_flags", []),
            *edges_artifact.payload.get("secondary_flags", []),
        ]
        node_vectors_version = edges_artifact.payload.get("node_vectors_version")
        if node_vectors_version is None:
            base_vectors = edges_artifact.payload.get("node_vectors", {})
        else:
            base_vectors = self.store.load_graph(doc_id, node_vectors_version).payload["node_vectors"]
        nodes, node_vectors, resolution_log = apply_resolved_nodes(
            edges_artifact.payload["nodes"],
            raw_flags,
            base_vectors,
        )
        suspected = {
            frozenset((row["left"], row["right"])): len(row.get("sources", []))
            for row in edges_artifact.payload.get("suspected_pairs", [])
        }
        requires = []
        seen = set()
        for edge in [
            *edges_artifact.payload.get("main_edges", []),
            *edges_artifact.payload.get("secondary_edges", []),
        ]:
            key = edge["source"], edge["target"], edge.get("edge_type")
            if key in seen:
                continue
            seen.add(key)
            requires.append({
                **edge,
                "independent_source_count": max(
                    int(edge.get("independent_source_count", 1)),
                    suspected.get(frozenset((edge["source"], edge["target"])), 0),
                ),
            })
        result = validate_graph_rules(
            nodes,
            requires,
            canonical.payload.get("edges", []),
            type_aliases=aliases,
        )
        backlog = [
            {**flag, "status": "unresolved"}
            for flag in raw_flags
            if isinstance(flag, dict) and not flag.get("resolved_node")
        ]
        backlog.extend(
            {"kind": "deferred_identity_group", "value": value, "status": "unresolved"}
            for value in canonical.payload.get("deferred", [])
        )
        backlog.extend(
            {"kind": "deferred_identity_pair", "value": value, "status": "unresolved"}
            for value in canonical.payload.get("deferred_pairs", [])
        )
        validation_flags = [
            *backlog,
            *result["two_way_flags"],
            *result["type_flags"],
        ]
        stats = {
            "requires_edge_count": len(result["requires_edges"]),
            "removed_cycle_edge_count": len(result["removed_cycle_edges"]),
            "cycle_component_count": len(result["cycle_resolution"]),
            "two_way_requires_count": len(result["two_way_flags"]),
            "redundant_edge_count": sum("redundant_via" in edge for edge in result["requires_edges"]),
            "validation_flag_count": len(validation_flags),
            "incremental_node_count": len(resolution_log),
        }
        edge_payload = {
            key: value
            for key, value in edges_artifact.payload.items()
            if key not in {"decision_log", "node_vectors"}
        }
        payload = {
            **edge_payload,
            "stage": "validated",
            "nodes": nodes,
            "decision_log_version": edges_artifact.version,
            "node_vectors_version": node_vectors_version,
            "incremental_node_vectors": {
                key: value for key, value in node_vectors.items() if key not in base_vectors
            },
            "requires_edges": result["requires_edges"],
            "removed_cycle_edges": result["removed_cycle_edges"],
            "cycle_resolution": result["cycle_resolution"],
            "open_edges": result["open_edges"],
            "type_registry": result["type_registry"],
            "quality_gate": result["quality_gate"],
            "validation_flags": validation_flags,
            "resolution_log": resolution_log,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=edges_artifact.version,
            manifest_fields={
                "stage": "validated",
                "quality_gate": result["quality_gate"],
                "type_registry": result["type_registry"],
                "stats": stats,
            },
        )
        return artifact, False
