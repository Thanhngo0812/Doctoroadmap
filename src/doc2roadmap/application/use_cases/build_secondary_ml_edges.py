"""A8 E5 secondary pass, reusing the LLM pass's selector and main contract."""
from math import isfinite

from doc2roadmap.application.ports.secondary_scoring import SecondaryScorer
from doc2roadmap.application.planning import StagePlan
from doc2roadmap.application.graph_chain import graph_chain_fields
from doc2roadmap.application.stage_measurements import measure_stage
from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges, chuan_hoa_loc_dich
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.prerequisites import merge_main_proposals, validate_main_proposals
from doc2roadmap.domain.secondary import select_secondary_pairs
from doc2roadmap.domain.secondary_features import (
    CANDIDATE_RULE, FEATURE_VERSION, SecondaryFeatureContext, is_candidate, pair_features,
)


class BuildSecondaryMLEdges(BuildSecondaryEdges):
    def __init__(self, store, scorer: SecondaryScorer, tokenize, *, target_filter=None):
        self.store, self.scorer, self.tokenize = store, scorer, tokenize
        self.target_filter = chuan_hoa_loc_dich(target_filter)

    @measure_stage
    def execute(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream)

    def _run(self, doc_id, *, upstream=None, planning=False):
        main = upstream if upstream is not None else self._main(
            doc_id, self._edge_checkpoint(doc_id, self.store.load_latest_graph(doc_id)))
        if main.payload.get("stage") != "edges" or not main.payload.get("main_complete") or main.payload.get("secondary_complete"):
            raise ValueError("pass phụ ML cần artifact pass chính hoàn chỉnh")
        main_config = main.manifest.get("config", {})
        before, after = main_config.get("definition_before", 0), main_config.get("definition_after", 2)
        version = main_config.get("chunks_version")
        chunk_artifact = (self.store.load_chunks(doc_id, version) if version is not None
                          else self.store.load_latest_chunks(doc_id))
        chunks, payload = chunk_artifact.result.chunks, main.payload
        nodes, ledger, route = payload["nodes"], payload.get("pair_cluster_ledger", []), payload["routing"]["route"]
        config = {**graph_chain_fields(main), "algorithm_id": "a8-secondary-ml-v1", "mode": "ml", "main_version": main.version,
                  "main_config_hash": main.manifest["config_hash"], "canonical_version": main_config.get("canonical_version"),
                  "chunks_version": chunk_artifact.version, "definition_before": before, "definition_after": after,
                  "scorer": self.scorer.metadata, "feature_version": FEATURE_VERSION,
                  "tokenizer": self.tokenize.identifier, "candidate_rule": CANDIDATE_RULE,
                  "threshold_rule": "round-sum-isotonic-on-judged-directions-fixed-point-10-v1",
                  "prune_rule": "direct-hard-or-explicit-hard-path-v3", "route": route}
        if self.target_filter is not None:  # chỉ khi bật: tắt thì hash cấu hình giữ nguyên từng bit
            config["target_filter"] = self.target_filter
        source_hash, config_hash = digest(payload), digest(config)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        pairs, _ = select_secondary_pairs(nodes, payload.get("suspected_pairs", []), ledger, [], route=route)
        pairs = self._loc_cap(pairs)
        if planning:
            return StagePlan("run", remaining_items=len(pairs), unit="pair", calls_estimate=0, usd_estimate=0.0,
                             note="Pass phụ ML chạy offline; không cần --allow-spend, không gọi LLM/embedding.")
        ctx = SecondaryFeatureContext(payload, chunks, before, after, tokenize=self.tokenize)
        main_edges = list(payload.get("main_edges", []))
        eligible, _ = select_secondary_pairs(nodes, pairs, ledger, main_edges, route=route)
        features, keys = [], []
        for pair in eligible:
            for x, y in ((pair["left"], pair["right"]), (pair["right"], pair["left"])):
                row = pair_features(ctx, x, y, pair)
                if is_candidate(ctx, x, y, row):
                    keys.append((pair["pair_id"], x, y))
                    features.append(row)
        scores = self.scorer.score(features)
        if len(scores) != len(keys) or any(not isfinite(v) or not 0 <= v <= 1 for v in scores):
            raise ValueError("bộ chấm pass phụ ML trả điểm không hợp lệ")
        probabilities = self.scorer.calibrate(scores)
        if len(probabilities) != len(scores) or any(not isfinite(v) or not 0 <= v <= 1 for v in probabilities):
            raise ValueError("bộ hiệu chỉnh pass phụ ML trả xác suất không hợp lệ")
        by_direction = dict(zip(keys, scores, strict=True))

        def choose_threshold(pair_ids):
            values = [(score, probability) for key, score, probability in zip(keys, scores, probabilities, strict=True)
                      if key[0] in pair_ids]
            k = int(round(sum(probability for _, probability in values)))
            return (sorted((score for score, _ in values), reverse=True)[k - 1] if k else None), k

        threshold, k = choose_threshold({p["pair_id"] for p in eligible})
        counts, history, oscillation = {threshold: k}, [], False
        for _ in range(10):
            history.append(threshold)
            edges, log, executor_log = self._assemble(payload, ctx, pairs, by_direction, threshold, before, after)
            judged = {r["pair_id"] for r in log if not r["status"].startswith("pruned_")}
            next_threshold, next_k = choose_threshold(judged)
            counts[next_threshold] = next_k
            if not next_k:
                threshold, stop_reason = None, "zero_positive"
                break
            if next_threshold == threshold:
                stop_reason = "fixed_point"
                break
            if next_threshold in history:
                threshold = max(history[history.index(next_threshold):])
                oscillation, stop_reason = True, "cycle"
                break
            threshold = next_threshold
        else:
            threshold, stop_reason = max(history), "iteration_limit"
        reassembled = threshold != history[-1]
        if reassembled:
            edges, log, executor_log = self._assemble(payload, ctx, pairs, by_direction, threshold, before, after)
        stats = {"secondary_pair_count": len(pairs), "completed_secondary_pair_count": len(log),
                 "secondary_candidate_count": len(keys), "pruned_secondary_pair_count": sum(r["status"].startswith("pruned_") for r in log),
                 "below_threshold_count": sum(r["status"] == "below_threshold" for r in log),
                 "no_evidence_count": sum(r["status"] == "no_evidence" for r in log),
                 "secondary_edge_count": len(edges), "threshold": threshold, "expected_positive_count": counts[threshold],
                 "threshold_history": history, "threshold_iterations": len(history), "threshold_oscillation": oscillation,
                 "threshold_stop_reason": stop_reason, "threshold_final_reassembled": reassembled,
                 "evidence_hard_count": sum(e.get("evidence_hard", False) for e in main_edges + edges),
                 "evidence_soft_count": sum(not e.get("evidence_hard", False) for e in main_edges + edges),
                 "secondary_calls": 0, "secondary_input_tokens": 0, "secondary_output_tokens": 0}
        cost = {**payload.get("cost_summary", {}), "main_usd": payload.get("cost_summary", {}).get("usd", 0.0),
                "secondary_usd": 0.0, "usd": payload.get("cost_summary", {}).get("usd", 0.0)}
        result = {**payload, "secondary_complete": True, "secondary_base_config_hash": config_hash,
                  "completed_secondary_pairs": sorted(p["pair_id"] for p in pairs), "secondary_edges": edges,
                  "secondary_flags": [], "secondary_log": log, "secondary_model_metrics": {"secondary_calls": 0},
                  "main_decision_log_version": main.version, "decision_log": [], "executor_log": executor_log,
                  "stats": stats, "cost_summary": cost}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, result, upstream_version=main.version,
                                         manifest_fields={"stage": "edges", "edge_pass": "secondary", "complete": True,
                                                          "stats": stats, "cost_summary": cost, "llm_transport": "none"})
        return artifact, False

    def _assemble(self, payload, ctx, pairs, by_direction, threshold, before, after):
        nodes, chunks = ctx.nodes, list(ctx.chunk_by_id.values())
        ledger, route = payload.get("pair_cluster_ledger", []), payload["routing"]["route"]
        main_edges = list(payload.get("main_edges", []))
        edges, log, executor_log = [], [], list(payload.get("executor_log", []))
        for pair in pairs:
            current = main_edges + edges
            askable, pruned = select_secondary_pairs(nodes, [pair], ledger, current, route=route)
            left, right = pair["left"], pair["right"]
            left_score = by_direction.get((pair["pair_id"], left, right))
            right_score = by_direction.get((pair["pair_id"], right, left))
            row = {"pair_id": pair["pair_id"], "score_left_to_right": left_score,
                   "score_right_to_left": right_score, "threshold": threshold, "quote": None}
            if not askable:
                log.append({**row, **pruned[0]})
                continue
            options = [(score, x, y) for score, x, y in ((left_score, left, right), (right_score, right, left))
                       if score is not None]
            # Same deterministic score/id tie break as the research assembler.
            selected = max(options) if options else None
            if selected is not None:
                row.update(score=selected[0], source=selected[1], target=selected[2])
            if selected is None or threshold is None or selected[0] < threshold:
                log.append({**row, "status": "below_threshold"})
                continue
            score, x, y = selected
            row.update(source=x, target=y, score=score)
            sentences, anchor_index = ctx.window_cache[y]
            quotes = sorted((abs(i - (anchor_index or 0)), i, sentence) for i, sentence in enumerate(sentences)
                            if ctx.found(ctx.pattern_cache[x], sentence)
                            and ctx.found_words(ctx.word_cache[x], sentence))
            accepted = None
            for _, _, quote in quotes:
                output = {"edges": [{"prerequisite": x, "target": y, "prerequisite_kind": "can_de_hieu",
                                     "evidence_kind": "trong_dinh_nghia", "quote": quote,
                                     "chunk_ids": [(ctx.node_by_id[y].get("anchor") or {}).get("chunk_id")],
                                     "reason": f"pass phụ không LLM: điểm {score:.3f}; căn cứ trong_dinh_nghia"}], "flags": []}
                session = {"session_id": "secondary_" + pair["pair_id"], "allowed_node_ids": [left, right]}
                proposals, _, operations, retry = validate_main_proposals(
                    output, session, nodes, chunks, payload["mention_map"], existing_edges=current,
                    require_kind=True, definition_before=before, definition_after=after)
                executor_log.extend(operations)
                if proposals and not retry:
                    accepted = proposals
                    row["quote"] = quote
                    break
            if accepted is None:
                log.append({**row, "status": "no_evidence"})
                continue
            edges, duplicate_log = merge_main_proposals(accepted, edges)
            executor_log.extend(duplicate_log)
            log.append({**row, "status": "created", "edge_count": len(accepted)})
        return edges, log, executor_log
