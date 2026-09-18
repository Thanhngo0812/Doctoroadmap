from __future__ import annotations

from collections import Counter, defaultdict

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.prerequisite_prompt import (
    MAIN_SCHEMA,
    PRICING_USD_PER_MILLION,
    main_prompt_hash,
    main_system_prompt,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.prerequisites import (
    merge_main_proposals,
    plan_main_sessions,
    validate_main_proposals,
    validate_main_response,
)


class BuildMainEdges:
    def __init__(self, store, model, *, single_session_limit=20, concurrency=4, generation=None):
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        self.store = store
        self.model = model
        self.single_session_limit = single_session_limit
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 8192}

    def _mentions(self, doc_id, latest):
        artifact = latest
        while artifact.payload.get("stage") != "mentions":
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("artifact graph không trỏ về stage mentions")
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    @staticmethod
    def _waves(sessions):
        if not sessions or sessions[0]["route"] != "chapter":
            return [sessions] if sessions else []
        lanes = defaultdict(list)
        for session in sessions:
            lanes[session["chapter_id"]].append(session)
        for values in lanes.values():
            values.sort(key=lambda row: (row["sequence"], row["session_id"]))
        waves = []
        while any(lanes.values()):
            waves.append([lanes[key].pop(0) for key in sorted(lanes) if lanes[key]])
        return waves

    @staticmethod
    def _concept(node):
        return {
            "node_id": node["node_id"],
            "name": node["name"],
            "aliases": node.get("aliases", []),
            "description": node.get("description", ""),
            "defining_chunk_ids": node.get("defining_chunk_ids", []),
        }

    def _input(self, session, nodes, chunks, mention_map, proposed_relations, existing_edges, session_by_id):
        node_by_id = {node["node_id"]: node for node in nodes}
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        targets = set(session["target_node_ids"])
        mentioned = [node_id for node_id in session["allowed_node_ids"] if node_id not in targets]
        previous = [
            edge
            for edge in existing_edges
            if session_by_id.get(edge.get("session_id"), {}).get("chapter_id") == session["chapter_id"]
        ]
        allowed = set(session["allowed_node_ids"])
        return {
            "session_id": session["session_id"],
            "route": session["route"],
            "allowed_node_ids": session["allowed_node_ids"],
            "chunks": [
                {"chunk_id": chunk_id, "text": chunk_by_id[chunk_id].text}
                for chunk_id in session["chunk_ids"]
            ],
            "target_concepts": [self._concept(node_by_id[node_id]) for node_id in session["target_node_ids"]],
            "mentioned_elsewhere": [self._concept(node_by_id[node_id]) for node_id in mentioned],
            "previous_edges_in_chapter": previous,
            "proposed_relations": [
                edge
                for edge in proposed_relations
                if edge.get("source") in allowed and edge.get("target") in allowed
            ],
        }

    def execute(self, doc_id):
        latest = self.store.load_latest_graph(doc_id)
        mentions = self._mentions(doc_id, latest)
        chunks = self.store.load_latest_chunks(doc_id).result
        canonical = self.store.load_latest_canonical(doc_id)
        nodes = mentions.payload["nodes"]
        sessions = plan_main_sessions(
            nodes,
            chunks.chunks,
            chunks.sections,
            mentions.payload["mention_map"],
            single_limit=self.single_session_limit,
        )
        route = sessions[0]["route"] if sessions else "none"
        reason = {
            "single": "learnable_count_at_most_limit",
            "chapter": "declarative_tree_has_real_hierarchy",
            "topic_cluster": "declarative_tree_is_degenerate",
            "none": "no_learnable_nodes",
        }[route]
        prompt_hash = main_prompt_hash(self.model.model_id, self.generation)
        base_config = {
            "algorithm_id": "a8-main-pass-v2",
            "mentions_version": mentions.version,
            "mentions_config_hash": mentions.manifest["config_hash"],
            "model_id": self.model.model_id,
            "generation": self.generation,
            "prompt_hash": prompt_hash,
            "single_session_limit": self.single_session_limit,
            "concurrency": self.concurrency,
            "route": route,
            "route_reason": reason,
            "executor": "requires-reverse-order-v2",
            "reverse_order_penalty": 0.1,
            "checkpoint": "progress-file-outside-version-chain-v1",
            "pricing_usd_per_million": PRICING_USD_PER_MILLION,
        }
        base_config_hash = digest(base_config)
        source_hash = digest(mentions.payload)
        cached = self.store.find_graph(doc_id, source_hash, base_config_hash)
        if cached is not None:
            return cached, True
        checkpoint_id = "main-" + base_config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        if resumable:
            completed = set(checkpoint.get("completed_main_sessions", []))
            edges = list(checkpoint.get("main_edges", []))
            flags = list(checkpoint.get("main_flags", []))
            decision_log = list(checkpoint.get("decision_log", []))
            executor_log = list(checkpoint.get("executor_log", []))
            metrics = Counter(checkpoint.get("model_metrics", {}))
        else:
            completed, edges, flags, decision_log, executor_log, metrics = set(), [], [], [], [], Counter()
        pending = [session for session in sessions if session["session_id"] not in completed]
        session_by_id = {session["session_id"]: session for session in sessions}
        system_prompt = main_system_prompt()
        for wave in self._waves(pending):
            inputs = [
                self._input(
                    session,
                    nodes,
                    chunks.chunks,
                    mentions.payload["mention_map"],
                    canonical.payload.get("edges", []),
                    edges,
                    session_by_id,
                )
                for session in wave
            ]
            jobs = [
                ModelJob("main", self.model, system_prompt, prompt_hash, data, MAIN_SCHEMA, validate_main_response)
                for data in inputs
            ]
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=self.concurrency)
            metrics.update(counts)
            decisions = defaultdict(list)
            for row in rows:
                decisions[row.get("input", {}).get("session_id", "")].append(row)
            results = {}
            repair_jobs, repair_sessions = [], []
            for session, data, value in zip(wave, inputs, values, strict=True):
                if value is None:
                    results[session["session_id"]] = ([], [{"kind": "invalid_main_session", "session_id": session["session_id"]}], [], [])
                    continue
                accepted, session_flags, operation_log, retry = validate_main_proposals(
                    value,
                    session,
                    nodes,
                    chunks.chunks,
                    mentions.payload["mention_map"],
                    existing_edges=edges,
                )
                results[session["session_id"]] = (accepted, session_flags, operation_log, retry)
                if retry:
                    repair_data = {
                        "session_id": session["session_id"],
                        "repair_only": True,
                        "original_input": data,
                        "rejected_operations": retry,
                    }
                    repair_jobs.append(ModelJob(
                        "main_repair",
                        self.model,
                        system_prompt,
                        prompt_hash,
                        repair_data,
                        MAIN_SCHEMA,
                        validate_main_response,
                    ))
                    repair_sessions.append(session)
            if repair_jobs:
                repaired, repair_rows, repair_counts = run_model_jobs(
                    repair_jobs,
                    decision_log + rows,
                    concurrency=self.concurrency,
                )
                metrics.update(repair_counts)
                for row in repair_rows:
                    decisions[row.get("input", {}).get("session_id", "")].append(row)
                for session, value in zip(repair_sessions, repaired, strict=True):
                    accepted, session_flags, operation_log, retry = results[session["session_id"]]
                    if value is None:
                        session_flags.append({"kind": "invalid_main_repair", "session_id": session["session_id"]})
                        continue
                    fixed, fixed_flags, fixed_log, still_invalid = validate_main_proposals(
                        value,
                        session,
                        nodes,
                        chunks.chunks,
                        mentions.payload["mention_map"],
                        existing_edges=edges + accepted,
                    )
                    accepted.extend(fixed)
                    session_flags.extend(fixed_flags)
                    operation_log.extend(fixed_log)
                    operation_log.extend({
                        "session_id": session["session_id"],
                        "status": "deferred_after_retry",
                        **row,
                    } for row in still_invalid)
            for session in sorted(wave, key=lambda row: row["session_id"]):
                session_id = session["session_id"]
                proposals, session_flags, operation_log, _ = results[session_id]
                edges, duplicate_log = merge_main_proposals(proposals, edges)
                flags.extend(session_flags)
                executor_log.extend(operation_log)
                executor_log.extend(duplicate_log)
                decision_log.extend(decisions[session_id])
                completed.add(session_id)
                self.store.save_checkpoint(doc_id, checkpoint_id, {
                    "source_hash": source_hash,
                    "completed_main_sessions": sorted(completed),
                    "main_edges": edges,
                    "main_flags": flags,
                    "decision_log": decision_log,
                    "executor_log": executor_log,
                    "model_metrics": dict(sorted(metrics.items())),
                })
        stats = {
            "session_count": len(sessions),
            "completed_session_count": len(completed),
            "main_edge_count": len(edges),
            "main_flag_count": len(flags),
            **dict(sorted(metrics.items())),
        }
        input_tokens = sum(value for key, value in metrics.items() if key.endswith("_input_tokens"))
        output_tokens = sum(value for key, value in metrics.items() if key.endswith("_output_tokens"))
        cost_summary = {
            "model_id": self.model.model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "usd": input_tokens * PRICING_USD_PER_MILLION["input"] / 1_000_000 + output_tokens * PRICING_USD_PER_MILLION["output"] / 1_000_000,
        }
        payload = {
            **mentions.payload,
            "stage": "edges",
            "main_complete": True,
            "main_base_config_hash": base_config_hash,
            "routing": {"route": route, "reason": reason, "single_session_limit": self.single_session_limit},
            "main_sessions": sessions,
            "completed_main_sessions": sorted(completed),
            "main_edges": edges,
            "main_flags": flags,
            "decision_log": decision_log,
            "executor_log": executor_log,
            "model_metrics": dict(sorted(metrics.items())),
            "cost_summary": cost_summary,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            base_config_hash,
            base_config,
            payload,
            upstream_version=mentions.version,
            manifest_fields={"stage": "edges", "edge_pass": "main", "complete": True, "routing": payload["routing"], "stats": stats},
        )
        self.store.clear_checkpoint(doc_id, checkpoint_id)
        return artifact, False
