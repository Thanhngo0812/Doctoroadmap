from __future__ import annotations

from doc2roadmap.application.stage_measurements import measure_stage
from doc2roadmap.domain.canonical import digest
from doc2roadmap.application.planning import StagePlan
from doc2roadmap.domain.global_validation import apply_resolved_nodes, strongly_connected_components, validate_graph_rules


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

    @measure_stage
    def execute(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream=None, planning=False):
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
        role_chunks = self.store.load_role_chunks(doc_id, edge_config["chunks_version"])
        chunk_roles = {chunk.chunk_id: chunk.role for chunk in role_chunks.result.chunks}
        aliases = self.store.load_type_aliases()
        config = {
            "algorithm_id": "a9-structural-consistency-v10",
            "check_name": "structural_consistency_check",
            "edges_version": edges_artifact.version,
            "edges_config_hash": edges_artifact.manifest["config_hash"],
            "role_chunks_version": role_chunks.version,
            "role_chunks_config_hash": role_chunks.manifest["config_hash"],
            "cycle_scope": "requires-learnable-scc",
            "cycle_keep_order": ["evidence_kind", "provenance_order", "independent_source_count"],
            "cycle_method": "weighted-simple-cycle-cover",
            "cycle_budget": 1000,
            "cycle_work_budget": 10000,
            "two_edge_cycle": "suspected-relation-type-error-exclude-both",
            "quality_min_nonredundant_edges_per_learnable": 0.15,
            "quality_max_isolated_ratio": 0.85,
            "redundancy": "mark-only",
            "cycle_large_component_method": "approximate-eades-priority",
            "type_aliases": aliases,
        }
        config_hash = digest(config)
        source_hash = digest([edges_artifact.payload, canonical.payload.get("edges", [])])
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        if planning:
            return StagePlan("run", remaining_items=1, note="Luật thuần, không gọi mô hình.")
        raw_flags = [
            *edges_artifact.payload.get("flags", []),
            *edges_artifact.payload.get("main_flags", []),
            *edges_artifact.payload.get("secondary_flags", []),
        ]
        valid_flags = [
            flag for flag in raw_flags
            if isinstance(flag, dict) and isinstance(flag.get("kind"), str) and flag["kind"].strip()
        ]
        invalid_upstream_flag_count = len(raw_flags) - len(valid_flags)
        node_vectors_version = edges_artifact.payload.get("node_vectors_version")
        if node_vectors_version is None:
            base_vectors = edges_artifact.payload.get("node_vectors", {})
        else:
            base_vectors = self.store.load_graph(doc_id, node_vectors_version).payload["node_vectors"]
        pending_nodes, _, _ = apply_resolved_nodes(
            edges_artifact.payload["nodes"],
            valid_flags,
            base_vectors,
            assign_clusters=False,
        )
        suspected = {
            frozenset((row["left"], row["right"])): len(row.get("sources", []))
            for row in edges_artifact.payload.get("suspected_pairs", [])
        }
        requires = []
        seen = set()
        for edge in sorted([
            *edges_artifact.payload.get("main_edges", []),
            *edges_artifact.payload.get("secondary_edges", []),
        ], key=lambda row: bool(row.get("soft"))):
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
            pending_nodes,
            requires,
            canonical.payload.get("edges", []),
            type_aliases=aliases,
            cycle_budget=config["cycle_budget"],
            work_budget=config["cycle_work_budget"],
            chunk_roles=chunk_roles,
        )
        nodes, node_vectors, resolution_log = apply_resolved_nodes(
            edges_artifact.payload["nodes"], valid_flags, base_vectors
        )
        remaining_scc_sizes = [
            len(component) for component in strongly_connected_components(
                (node["node_id"] for node in nodes if node.get("learnable")),
                [edge for edge in result["requires_edges"] if not edge.get("soft")],
            )
        ]
        remaining_scc_size_distribution = {
            str(size): remaining_scc_sizes.count(size) for size in sorted(set(remaining_scc_sizes))
        }
        backlog = [
            {**flag, "status": "unresolved"}
            for flag in valid_flags
            if not flag.get("resolved_node")
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
            *result["region_flags"],
        ]
        if invalid_upstream_flag_count:
            validation_flags.append({
                "kind": "invalid_upstream_flags",
                "count": invalid_upstream_flag_count,
                "reason": "Legacy edge artifact contains flags without a nonempty kind; omitted from review",
            })
        if not result["quality_gate"]["passed"]:
            validation_flags.append({
                "kind": "structural_consistency_gate_closed",
                "reason": result["quality_gate"]["warning"],
                "quality_gate": result["quality_gate"],
            })
        stats = {
            "requires_edge_count": len(result["requires_edges"]),
            "excluded_region_edge_count": len(result["region_flags"]),
            "soft_requires_edge_count": sum(edge.get("soft") is True for edge in result["requires_edges"]),
            "removed_cycle_edge_count": len(result["removed_cycle_edges"]),
            "cycle_component_count": len(result["cycle_resolution"]),
            "two_way_requires_count": len(result["two_way_flags"]),
            "redundant_edge_count": sum("redundant_via" in edge for edge in result["requires_edges"]),
            "validation_flag_count": len(validation_flags),
            "incremental_node_count": len(resolution_log),
            "invalid_upstream_flag_count": invalid_upstream_flag_count,
            "remaining_scc_size_distribution": remaining_scc_size_distribution,
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
                "check_name": "structural_consistency_check",
                "quality_gate": result["quality_gate"],
                "type_registry": result["type_registry"],
                "stats": stats,
            },
        )
        return artifact, False
