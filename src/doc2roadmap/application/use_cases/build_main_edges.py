from __future__ import annotations

from collections import Counter, defaultdict

from doc2roadmap.application.stage_measurements import measure_stage, resume_measurements
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.graph_chain import artifact_chain, graph_chain_fields
from doc2roadmap.application.prerequisite_prompt import (
    MAIN_SCHEMA,
    PRICING_SOURCE,
    PRICING_USD_PER_MILLION,
    main_prompt_hash,
    main_system_prompt,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.prerequisites import (
    REVERSE_ORDER_PENALTY,
    definition_window,
    merge_main_proposals,
    plan_main_sessions,
    validate_main_proposals,
    validate_main_response,
)


class BuildMainEdges:
    def __init__(self, store, model, *, single_session_limit=20, concurrency=4, generation=None,
                 definition_before=4, definition_after=2, parallel_sessions=True):
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        self.store = store
        self.model = model
        self.single_session_limit = single_session_limit
        self.concurrency = concurrency
        self.parallel_sessions = parallel_sessions
        self.definition_before = definition_before
        self.definition_after = definition_after
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 8192}

    def _provenance(self, doc_id, latest):
        artifact = latest
        while (artifact.payload.get("stage") not in {"provenance", "identity"}
               and not (artifact.payload.get("stage") == "mentions" and artifact_chain(artifact) == "gop")):
            if artifact.payload.get("stage") in {"clusters", "mentions"}:
                raise ValueError("artifact graph không trỏ về stage provenance")
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("artifact graph không trỏ về stage provenance")
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
            "teaching_status": node.get("teaching_status"),
            "anchor": node.get("anchor"),
        }

    def _input(self, session, nodes, chunks, mention_map, proposed_relations, existing_edges, session_by_id):
        node_by_id = {node["node_id"]: node for node in nodes}
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        targets = set(session["target_node_ids"])
        mentioned = [node_id for node_id in session["allowed_node_ids"] if node_id not in targets]
        mentioned += sorted({node_id for chunk_id in session["chunk_ids"]
                             for node_id in mention_map.get(chunk_id, {})
                             if node_id in node_by_id and node_id not in targets and node_id not in mentioned})
        previous_in_chapter = [] if self.parallel_sessions else [
            edge
            for edge in existing_edges
            if session_by_id.get(edge.get("session_id"), {}).get("chapter_id") == session["chapter_id"]
        ]
        allowed = set(session["allowed_node_ids"])
        previous = [
            edge
            for edge in previous_in_chapter
            if edge.get("source") in allowed or edge.get("target") in allowed
        ]
        return {
            "session_id": session["session_id"],
            "route": session["route"],
            "allowed_node_ids": session["allowed_node_ids"],
            "chunks": [
                {"chunk_id": chunk_id, "text": chunk_by_id[chunk_id].text}
                for chunk_id in session["chunk_ids"]
            ],
            "target_concepts": [{**self._concept(node_by_id[node_id]),
                                  "definition_window": definition_window(node_by_id[node_id], list(chunk_by_id.values()),
                                                                         before=getattr(self, "definition_before", 4),
                                                                         after=getattr(self, "definition_after", 2))}
                                 for node_id in session["target_node_ids"]],
            "mentioned_elsewhere": [self._concept(node_by_id[node_id]) for node_id in mentioned],
            "previous_edges_in_chapter": previous,
            "previous_edges_omitted_count": len(previous_in_chapter) - len(previous),
            "proposed_relations": [
                edge
                for edge in proposed_relations
                if edge.get("source") in allowed and edge.get("target") in allowed
            ],
        }

    @measure_stage
    def execute(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream=None, planning=False):
        mentions = upstream if upstream is not None else self._provenance(
            doc_id, self.store.load_latest_graph(doc_id)
        )
        if (mentions.payload.get("stage") not in {"provenance", "identity"}
                and not (mentions.payload.get("stage") == "mentions" and artifact_chain(mentions) == "gop")):
            raise ValueError("pass chính cần artifact identity hoặc provenance")
        mention_config = mentions.manifest.get("config", {})
        chunks_version = mention_config.get("chunks_version")
        chunks_artifact = (
            self.store.load_chunks(doc_id, chunks_version)
            if chunks_version is not None
            else self.store.load_latest_chunks(doc_id)
        )
        chunks = chunks_artifact.result
        canonical_version = mention_config.get("canonical_version")
        canonical = (
            self.store.load_canonical(doc_id, canonical_version)
            if canonical_version is not None
            else self.store.load_latest_canonical(doc_id)
        )
        chain_fields = graph_chain_fields(mentions, canonical)
        definition_contract = (chain_fields.get("canonical_has_anchors", False) if chain_fields else
                               mentions.payload["stage"] == "identity")
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
            **chain_fields,
            "algorithm_id": "a8-main-pass-v7",
            "provenance_version": mentions.version,
            "provenance_config_hash": mentions.manifest["config_hash"],
            "mentions_version": mention_config.get("mentions_version"),
            "mentions_config_hash": mention_config.get("mentions_config_hash"),
            "canonical_version": canonical.version,
            "chunks_version": chunks_artifact.version,
            "model_id": self.model.model_id,
            "generation": self.generation,
            "prompt_hash": prompt_hash,
            "single_session_limit": self.single_session_limit,
            "parallel_sessions": self.parallel_sessions,
            "definition_before": self.definition_before,
            "definition_after": self.definition_after,
            "route": route,
            "route_reason": reason,
            "executor": "definition-paragraph-window-whitespace-v3",
            "reverse_order_penalty": REVERSE_ORDER_PENALTY,
            "checkpoint": "progress-file-outside-version-chain-v1",
            "pricing_usd_per_million": PRICING_USD_PER_MILLION,
            "pricing_source": PRICING_SOURCE,
        }
        base_config_hash = digest(base_config)
        source_hash = digest(mentions.payload)
        cached = self.store.find_graph(doc_id, source_hash, base_config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        checkpoint_id = "main-" + base_config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        resume_measurements(checkpoint if resumable else None)
        if resumable:
            completed = set(checkpoint.get("completed_main_sessions", []))
            edges = list(checkpoint.get("main_edges", []))
            flags = list(checkpoint.get("main_flags", []))
            decision_log = list(checkpoint.get("decision_log", []))
            executor_log = list(checkpoint.get("executor_log", []))
            metrics = Counter(checkpoint.get("model_metrics", {}))
            call_cache = {row["input_hash"]: row for row in checkpoint.get("pending_model_results", [])}
            metrics.update(checkpoint.get("pending_model_metrics", {}))
        else:
            completed, edges, flags, decision_log, executor_log, metrics = set(), [], [], [], [], Counter()
            call_cache = {}
        pending = [session for session in sessions if session["session_id"] not in completed]
        session_by_id = {session["session_id"]: session for session in sessions}
        system_prompt = main_system_prompt()
        if planning:
            inputs = [self._input(session, nodes, chunks.chunks, mentions.payload["mention_map"],
                                 canonical.payload.get("edges", []), edges, session_by_id) for session in pending]
            return model_plan(inputs, system_prompt=system_prompt, generation=self.generation,
                              unit="session", checkpoint_id=checkpoint_id, metrics=metrics)
        pending_counts, unflushed = Counter(), 0

        def save_progress():
            state = {"source_hash": source_hash, "completed_main_sessions": sorted(completed),
                     "main_edges": edges, "main_flags": flags, "decision_log": decision_log,
                     "executor_log": executor_log, "model_metrics": dict(sorted(metrics.items()))}
            if call_cache:
                state.update(pending_model_results=list(call_cache.values()),
                             pending_model_metrics=dict(sorted(pending_counts.items())))
            self.store.save_checkpoint(doc_id, checkpoint_id, state)

        def cache_result(row, counts):
            nonlocal unflushed
            call_cache[row["input_hash"]] = row
            pending_counts.update(counts)
            unflushed += 1
            if unflushed >= 16:
                save_progress()
                unflushed = 0

        def run_jobs(jobs, previous):
            if not self.parallel_sessions:
                return run_model_jobs(jobs, previous, concurrency=self.concurrency)
            try:
                result = run_model_jobs(jobs, previous, completed_log=call_cache.values(),
                                        concurrency=self.concurrency, on_complete=cache_result)
            except BaseException:
                save_progress()
                raise
            pending_counts.clear()
            return result

        for wave in ([pending] if self.parallel_sessions and pending else self._waves(pending)):
            validation_edges = [] if self.parallel_sessions else edges
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
            values, rows, counts = run_jobs(jobs, decision_log)
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
                    existing_edges=validation_edges,
                    require_kind=definition_contract,
                    definition_before=self.definition_before,
                    definition_after=self.definition_after,
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
                repaired, repair_rows, repair_counts = run_jobs(
                    repair_jobs,
                    decision_log + rows,
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
                        existing_edges=validation_edges + accepted,
                        require_kind=definition_contract,
                        definition_before=self.definition_before,
                        definition_after=self.definition_after,
                    )
                    for invalid in still_invalid:
                        if invalid["error"] != "quote_outside_definition_window":
                            continue
                        downgraded = {**invalid["operation"], "prerequisite_kind": "cong_cu"}
                        softer, _, downgrade_log, downgrade_retry = validate_main_proposals(
                            {"edges": [downgraded], "flags": []}, session, nodes, chunks.chunks,
                            mentions.payload["mention_map"], existing_edges=validation_edges + accepted + fixed,
                            require_kind=True, definition_before=self.definition_before,
                            definition_after=self.definition_after)
                        fixed.extend(softer)
                        fixed_log.extend(downgrade_log)
                        if not downgrade_retry:
                            invalid["status"] = "downgraded_to_cong_cu"
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
            call_cache.clear()
            pending_counts.clear()
            unflushed = 0
            save_progress()
        stats = {
            "session_count": len(sessions),
            "completed_session_count": len(completed),
            "main_edge_count": len(edges),
            "main_flag_count": len(flags),
            "evidence_hard_count": sum(edge.get("evidence_hard", False) for edge in edges),
            "evidence_soft_count": sum(not edge.get("evidence_hard", False) for edge in edges),
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
            **chain_fields,
            "stage": "edges",
            "main_complete": True,
            "definition_contract": definition_contract,
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
            manifest_fields={"stage": "edges", "edge_pass": "main", "complete": True, "routing": payload["routing"], "stats": stats,
                             "llm_transport": getattr(self.model, "transport", "unknown")},
        )
        self.store.clear_checkpoint(doc_id, checkpoint_id)
        return artifact, False
