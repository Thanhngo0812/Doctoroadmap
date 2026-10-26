from __future__ import annotations

from collections import Counter

from doc2roadmap.application.stage_measurements import measure_stage, resume_measurements
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.graph_chain import graph_chain_fields
from doc2roadmap.application.prerequisite_prompt import (
    SECONDARY_SCHEMA,
    PRICING_SOURCE,
    PRICING_USD_PER_MILLION,
    secondary_prompt_hash,
    secondary_system_prompt,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.prerequisites import merge_main_proposals, validate_main_proposals
from doc2roadmap.domain.secondary import (
    pair_dossier,
    reconcile_pair_verdicts,
    select_secondary_pairs,
    validate_secondary_response,
)


def chuan_hoa_loc_dich(target_filter):
    """Bộ lọc cặp theo đích (DG-06): None = không lọc; danh sách rỗng là lỗi, không âm thầm bỏ hết cặp."""
    if target_filter is None:
        return None
    if isinstance(target_filter, (str, bytes)) or not isinstance(target_filter, (list, tuple, set, frozenset)):
        raise ValueError("bộ lọc đích pass phụ phải là danh sách id node hoặc None")
    if not target_filter:
        raise ValueError("danh sách đích pass phụ rỗng: bỏ hết mọi cặp; dùng None để không lọc")
    if any(not isinstance(value, str) or not value for value in target_filter):
        raise ValueError("bộ lọc đích pass phụ phải là danh sách id node (chuỗi không rỗng)")
    return sorted(set(target_filter))


class BuildSecondaryEdges:
    def __init__(self, store, model, *, concurrency=4, window_pairs=None, generation=None, target_filter=None):
        self.target_filter = chuan_hoa_loc_dich(target_filter)
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        if window_pairs is not None and (type(window_pairs) is not int or window_pairs < 1):
            raise ValueError("cửa sổ pass phụ phải là số nguyên dương")
        self.store = store
        self.model = model
        self.concurrency = concurrency
        self.window_pairs = window_pairs or max(1, concurrency // 2)
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 8192}

    def _loc_cap(self, pairs):
        """Giữ cặp có ít nhất một đầu là đích được phép; cặp không có đầu nào thì không được chấm hay gửi đi."""
        allowed = getattr(self, "target_filter", None)
        if allowed is None:
            return pairs
        allowed = set(allowed)
        return [pair for pair in pairs if pair["left"] in allowed or pair["right"] in allowed]

    def _edge_checkpoint(self, doc_id, latest):
        artifact = latest
        while artifact.payload.get("stage") != "edges":
            if artifact.payload.get("stage") == "clusters":
                raise ValueError("artifact graph không trỏ về stage edges")
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("artifact graph không trỏ về stage edges")
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    def _main(self, doc_id, edge_checkpoint):
        if "secondary_base_config_hash" not in edge_checkpoint.payload:
            return edge_checkpoint
        upstream = edge_checkpoint.manifest.get("upstream_version")
        if upstream is None:
            raise ValueError("artifact pass phụ không trỏ về pass chính")
        return self.store.load_graph(doc_id, upstream)

    @staticmethod
    def _reverse_dossier(dossier):
        return {
            **dossier,
            "left": dossier["right"],
            "right": dossier["left"],
            "nodes": list(reversed(dossier["nodes"])),
            "provenance_order": {
                dossier["right"]: dossier["provenance_order"][dossier["right"]],
                dossier["left"]: dossier["provenance_order"][dossier["left"]],
            },
            "presentation_order": [dossier["right"], dossier["left"]],
        }

    @measure_stage
    def execute(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream=None, planning=False):
        if upstream is None:
            edge_checkpoint = self._edge_checkpoint(doc_id, self.store.load_latest_graph(doc_id))
            main = self._main(doc_id, edge_checkpoint)
        else:
            main = upstream
        if main.payload.get("stage") != "edges" or not main.payload.get("main_complete"):
            raise ValueError("pass phụ cần artifact pass chính hoàn chỉnh")
        main_config = main.manifest.get("config", {})
        definition_before = main_config.get("definition_before", 0)
        definition_after = main_config.get("definition_after", 2)
        require_kind = bool(main.payload.get("definition_contract"))
        chunks_version = main_config.get("chunks_version")
        chunks_artifact = (
            self.store.load_chunks(doc_id, chunks_version)
            if chunks_version is not None
            else self.store.load_latest_chunks(doc_id)
        )
        chunks = chunks_artifact.result.chunks
        nodes = main.payload["nodes"]
        route = main.payload["routing"]["route"]
        prompt_hash = secondary_prompt_hash(self.model.model_id, self.generation)
        base_config = {
            **graph_chain_fields(main),
            "algorithm_id": "a8-secondary-pass-lazy-v7",
            "main_version": main.version,
            "main_config_hash": main.manifest["config_hash"],
            "canonical_version": main_config.get("canonical_version"),
            "chunks_version": chunks_artifact.version,
            "model_id": self.model.model_id,
            "generation": self.generation,
            "prompt_hash": prompt_hash,
            "route": route,
            "definition_before": definition_before,
            "definition_after": definition_after,
            "order_check": "fully-reversed-dossier-v2",
            "reconcile_rule": "same-direction-weaker-evidence-or-soft-v2",
            "prune_rule": "direct-hard-or-explicit-hard-path-v3",
            "checkpoint": "progress-file-outside-version-chain-v1",
            "pricing_usd_per_million": PRICING_USD_PER_MILLION,
            "pricing_source": PRICING_SOURCE,
        }
        if getattr(self, "target_filter", None) is not None:  # chỉ khi bật: tắt thì hash cấu hình giữ nguyên từng bit
            base_config["target_filter"] = self.target_filter
        base_config_hash = digest(base_config)
        source_hash = digest(main.payload)
        cached = self.store.find_graph(doc_id, source_hash, base_config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        checkpoint_id = "secondary-" + base_config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        resume_measurements(checkpoint if resumable else None)
        if resumable:
            completed = set(checkpoint.get("completed_secondary_pairs", []))
            secondary_edges = list(checkpoint.get("secondary_edges", []))
            secondary_flags = list(checkpoint.get("secondary_flags", []))
            decision_log = list(checkpoint.get("decision_log", []))
            executor_log = list(checkpoint.get("executor_log", []))
            secondary_log = list(checkpoint.get("secondary_log", []))
            metrics = Counter(checkpoint.get("secondary_model_metrics", {}))
        else:
            completed, secondary_edges, secondary_flags = set(), [], []
            decision_log = []
            executor_log = list(main.payload.get("executor_log", []))
            secondary_log, metrics = [], Counter()
        pairs, _ = select_secondary_pairs(
            nodes,
            main.payload.get("suspected_pairs", []),
            main.payload.get("pair_cluster_ledger", []),
            [],
            route=route,
        )
        pairs = self._loc_cap(pairs)
        pending = [pair for pair in pairs if pair["pair_id"] not in completed]
        system_prompt = secondary_system_prompt()
        if planning:
            existing = list(main.payload.get("main_edges", [])) + secondary_edges
            askable, pruned = select_secondary_pairs(nodes, pending, main.payload.get("pair_cluster_ledger", []),
                                                     existing, route=route)
            inputs = [{"session_id": "secondary_" + pair["pair_id"] + "_left",
                       "dossier": {**pair_dossier(pair, nodes, chunks, main.payload["mention_map"],
                                                   main.payload.get("pair_cluster_ledger", []), existing,
                                                   definition_before=definition_before, definition_after=definition_after),
                                   "presentation_order": [pair["left"], pair["right"]]}} for pair in askable]
            result = model_plan(inputs, system_prompt=system_prompt, generation=self.generation, unit="pair",
                                checkpoint_id=checkpoint_id, metrics=metrics, calls_per_item=2)
            result.remaining_items = len(pending)
            result.note += (f" {len(askable)} cặp cần phán tối đa hai chiều, {len(pruned)} cặp cắt được ngay; "
                            "chỉ hỏi chiều sau khi chiều đầu tạo cạnh; cạnh mới có thể cắt thêm cặp nên số lời gọi có thể giảm.")
            return result

        def save_progress():
            self.store.save_checkpoint(doc_id, checkpoint_id, {
                "source_hash": source_hash,
                "completed_secondary_pairs": sorted(completed),
                "secondary_edges": secondary_edges,
                "secondary_flags": secondary_flags,
                "decision_log": decision_log,
                "executor_log": executor_log,
                "secondary_log": secondary_log,
                "secondary_model_metrics": dict(sorted(metrics.items())),
            })

        ledger = main.payload.get("pair_cluster_ledger", [])
        main_edges = list(main.payload.get("main_edges", []))

        def prepare(pair, existing):
            dossier = pair_dossier(
                pair, nodes, chunks, main.payload["mention_map"], ledger, existing,
                definition_before=definition_before, definition_after=definition_after,
            )
            pair_session = {"session_id": "secondary_" + pair["pair_id"],
                            "allowed_node_ids": [pair["left"], pair["right"]],
                            "chunk_ids": [row["chunk_id"] for row in dossier["evidence_chunks"]]}

            def validate(value):
                validate_secondary_response(value, pair)
                if value["decision"] == "create":
                    output = {
                        "edges": [{
                            "target": value["target"],
                            "prerequisite": value["prerequisite"],
                            "evidence_kind": value["evidence_kind"],
                            **({"prerequisite_kind": value["prerequisite_kind"], "quote": value["quote"]}
                               if "prerequisite_kind" in value else {}),
                            "chunk_ids": value["chunk_ids"],
                            "reason": value["reason"],
                            **({"confidence": value["confidence"]} if "confidence" in value else {}),
                        }],
                        "flags": value["flags"],
                    }
                    _, _, _, retry = validate_main_proposals(
                        output,
                        pair_session,
                        nodes,
                        chunks,
                        main.payload["mention_map"],
                        existing_edges=existing,
                        require_kind=require_kind,
                        definition_before=definition_before, definition_after=definition_after,
                    )
                    if retry:
                        raise ValueError(retry[0]["error"])
            return dossier, pair_session, validate

        def downgrade(pair, pair_session, validate, values, rows, existing):
            for index, (value, row) in enumerate(zip(values, rows, strict=True)):
                if value is not None or row.get("error") != "quote_outside_definition_window":
                    continue
                original = row.get("last_output")
                if not isinstance(original, dict) or original.get("decision") != "create":
                    continue
                downgraded = {**original, "prerequisite_kind": "cong_cu"}
                output = {"edges": [{"target": downgraded.get("target"), "prerequisite": downgraded.get("prerequisite"),
                                     "prerequisite_kind": "cong_cu", "evidence_kind": downgraded.get("evidence_kind"),
                                     "chunk_ids": downgraded.get("chunk_ids"), "quote": downgraded.get("quote"),
                                     "reason": downgraded.get("reason")}], "flags": []}
                try:
                    validate_secondary_response(downgraded, pair)
                    _, _, _, invalid = validate_main_proposals(
                        output, pair_session, nodes, chunks, main.payload["mention_map"], existing_edges=existing,
                        require_kind=True, definition_before=definition_before, definition_after=definition_after)
                except (ValueError, TypeError, KeyError):
                    continue
                if not invalid:
                    values[index] = downgraded
                    row["downgraded_to_cong_cu_after_retry"] = True

        def commit(pair, pair_session, values):
            nonlocal secondary_edges
            if any(value is None for value in values):
                verdict = {"pair_id": pair["pair_id"], "decision": "defer", "reason": "invalid_or_outside_dossier",
                           "flags": [{"kind": "outside_or_invalid_secondary_edge", "pair_id": pair["pair_id"]}]}
            elif len(values) == 1:
                verdict = values[0]
            else:
                verdict = reconcile_pair_verdicts(values[0], values[1])
            if verdict["decision"] == "create":
                output = {"edges": [{"target": verdict["target"], "prerequisite": verdict["prerequisite"],
                                     "evidence_kind": verdict["evidence_kind"],
                                     **({"prerequisite_kind": verdict["prerequisite_kind"], "quote": verdict["quote"]}
                                        if "prerequisite_kind" in verdict else {}),
                                     "chunk_ids": verdict["chunk_ids"], "reason": verdict["reason"]}],
                          "flags": verdict.get("flags", [])}
                proposals, pair_flags, operation_log, retry = validate_main_proposals(
                    output, pair_session, nodes, chunks, main.payload["mention_map"],
                    existing_edges=main_edges + secondary_edges, require_kind=require_kind,
                    definition_before=definition_before, definition_after=definition_after)
                secondary_edges, duplicate_log = merge_main_proposals(proposals, secondary_edges)
                secondary_flags.extend(pair_flags)
                executor_log.extend(operation_log)
                executor_log.extend(duplicate_log)
                if retry:
                    secondary_log.append({"pair_id": pair["pair_id"], "status": "deferred", "reason": retry[0]["error"]})
                else:
                    secondary_log.append({"pair_id": pair["pair_id"], "status": "created", "edge_count": len(proposals)})
            else:
                secondary_flags.extend(verdict.get("flags", []))
                secondary_log.append({"pair_id": pair["pair_id"],
                                      "status": "deferred" if verdict["decision"] == "defer" else "rejected",
                                      "reason": "first_order_final" if len(values) == 1 else verdict.get("reason", verdict["decision"]),
                                      **({"verdict_reason": verdict.get("reason", verdict["decision"])} if len(values) == 1 else {}),
                                      "decision": verdict["decision"]})

        while True:
            pending = [pair for pair in pairs if pair["pair_id"] not in completed]
            if not pending:
                break
            snapshot = main_edges + secondary_edges
            window, prefix = [], []
            for pair in pending:
                prefix.append(pair)
                askable, _ = select_secondary_pairs(nodes, [pair], ledger, snapshot, route=route)
                if askable:
                    window.append(pair)
                    if len(window) == self.window_pairs:
                        break
            if not window:
                for pair in prefix:
                    _, pruned = select_secondary_pairs(nodes, [pair], ledger, snapshot, route=route)
                    secondary_log.extend(pruned)
                    completed.add(pair["pair_id"])
                save_progress()
                continue

            specs, jobs = {}, []
            for pair in window:
                dossier, pair_session, validate = prepare(pair, snapshot)
                inputs = [
                    {"session_id": pair_session["session_id"] + "_left",
                     "dossier": {**dossier, "presentation_order": [pair["left"], pair["right"]]}},
                    {"session_id": pair_session["session_id"] + "_right", "dossier": self._reverse_dossier(dossier)},
                ]
                start = len(jobs)
                jobs.append(ModelJob("secondary", self.model, system_prompt, prompt_hash, inputs[0], SECONDARY_SCHEMA, validate))
                specs[pair["pair_id"]] = (dossier, pair_session, validate, start, inputs[1])

            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=self.concurrency)
            answered, second_jobs, second_pairs = {}, [], []
            for pair in window:
                dossier, pair_session, validate, start, second_input = specs[pair["pair_id"]]
                pair_values = values[start:start + 1]
                downgrade(pair, pair_session, validate, pair_values, rows[start:start + 1], snapshot)
                answered[pair["pair_id"]] = pair_values
                if pair_values[0] is not None and pair_values[0]["decision"] == "create":
                    second_jobs.append(ModelJob("secondary", self.model, system_prompt, prompt_hash, second_input, SECONDARY_SCHEMA, validate))
                    second_pairs.append(pair)
            decision_log.extend(rows)
            metrics.update(counts)
            second_values, second_rows, second_counts = run_model_jobs(second_jobs, decision_log, concurrency=self.concurrency)
            for index, pair in enumerate(second_pairs):
                _, pair_session, validate, _, _ = specs[pair["pair_id"]]
                pair_values = second_values[index:index + 1]
                downgrade(pair, pair_session, validate, pair_values, second_rows[index:index + 1], snapshot)
                answered[pair["pair_id"]].extend(pair_values)
            decision_log.extend(second_rows)
            metrics.update(second_counts)

            for pair in prefix:
                current = main_edges + secondary_edges
                askable, pruned = select_secondary_pairs(nodes, [pair], ledger, current, route=route)
                if not askable:
                    secondary_log.extend(pruned)
                    completed.add(pair["pair_id"])
                    continue
                dossier, pair_session, _, start, _ = specs[pair["pair_id"]]
                current_dossier = pair_dossier(
                    pair, nodes, chunks, main.payload["mention_map"], ledger, current,
                    definition_before=definition_before, definition_after=definition_after)
                if current_dossier != dossier:
                    break
                commit(pair, pair_session, answered[pair["pair_id"]])
                completed.add(pair["pair_id"])
            save_progress()
        pruned_count = sum(
            row.get("status") in {"pruned_direct_edge", "pruned_explicit_path"}
            for row in secondary_log
        )
        stats = {
            "secondary_pair_count": len(pairs),
            "completed_secondary_pair_count": len(completed),
            "pruned_secondary_pair_count": pruned_count,
            "secondary_edge_count": len(secondary_edges),
            "evidence_hard_count": sum(
                edge.get("evidence_hard", False)
                for edge in [*main.payload.get("main_edges", []), *secondary_edges]
            ),
            "evidence_soft_count": sum(
                not edge.get("evidence_hard", False)
                for edge in [*main.payload.get("main_edges", []), *secondary_edges]
            ),
            **dict(sorted(metrics.items())),
        }
        input_tokens = sum(value for key, value in metrics.items() if key.endswith("_input_tokens"))
        output_tokens = sum(value for key, value in metrics.items() if key.endswith("_output_tokens"))
        secondary_cost = input_tokens * PRICING_USD_PER_MILLION["input"] / 1_000_000 + output_tokens * PRICING_USD_PER_MILLION["output"] / 1_000_000
        main_cost = float(main.payload.get("cost_summary", {}).get("usd", 0.0))
        cost_summary = {
            "model_id": self.model.model_id,
            "input_tokens": int(main.payload.get("cost_summary", {}).get("input_tokens", 0)) + input_tokens,
            "output_tokens": int(main.payload.get("cost_summary", {}).get("output_tokens", 0)) + output_tokens,
            "main_usd": main_cost,
            "secondary_usd": secondary_cost,
            "usd": main_cost + secondary_cost,
        }
        payload = {
            **main.payload,
            "secondary_complete": True,
            "secondary_base_config_hash": base_config_hash,
            "completed_secondary_pairs": sorted(completed),
            "secondary_edges": secondary_edges,
            "secondary_flags": secondary_flags,
            "main_decision_log_version": main.version,
            "decision_log": decision_log,
            "executor_log": executor_log,
            "secondary_log": secondary_log,
            "secondary_model_metrics": dict(sorted(metrics.items())),
            "cost_summary": cost_summary,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            base_config_hash,
            base_config,
            payload,
            upstream_version=main.version,
            manifest_fields={"stage": "edges", "edge_pass": "secondary", "complete": True, "stats": stats,
                             "llm_transport": getattr(self.model, "transport", "unknown"),
                             "execution_limits": {
                                 "concurrency": self.concurrency,
                                 "window_pairs": self.window_pairs,
                                 **(self.model.limiter.snapshot() if getattr(self.model, "limiter", None) else {}),
                             }},
        )
        self.store.clear_checkpoint(doc_id, checkpoint_id)
        return artifact, False
