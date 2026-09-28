from __future__ import annotations

from collections import Counter
from typing import Any

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.identity import (
    VERDICTS,
    VERIFY_RELATIONS,
    SEMANTIC_TOP_K,
    SEMANTIC_MIN_SIMILARITY,
    identity_candidates,
    identity_map,
    merge_and_break_cycles,
    merge_identity_nodes,
    validate_identity_response,
)
from doc2roadmap.domain.teaching import EXCLUDED_STATUSES

IDENTITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "pair_id": {"type": "string"},
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "reason": {"type": "string"},
    },
    "required": ["pair_id", "verdict", "reason"],
}
PAIR_BATCH = 8
VERIFY_SCHEMA = {"type": "object", "properties": {
    "pair_id": {"type": "string"}, "relation": {"type": "string", "enum": list(VERIFY_RELATIONS)},
    "reason": {"type": "string"}}, "required": ["pair_id", "relation", "reason"]}
# Quyết định của người duyệt (T5) thắng phán của mô hình. Chỉ "Đồng ý gộp" cho gộp; "Không chắc" thì giữ tách.
HUMAN_VERDICT = {"Đồng ý gộp": "same", "Không gộp": "different", "Là hai nghĩa khác nhau": "sense_split",
                 "Không chắc": "different"}


def load_identity_review(path, *, doc_id):
    """Đọc quyết định duyệt danh tính (T5) của một tài liệu: {"doc_id", "decisions": [{"left", "right", "decision"}]}."""
    import json
    from pathlib import Path

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("doc_id") != doc_id:
        raise ValueError(f"tệp duyệt danh tính của doc_id {data.get('doc_id')!r}, không phải {doc_id!r}")
    review = {}
    for row in data.get("decisions", []):
        if row.get("decision") not in HUMAN_VERDICT:
            raise ValueError(f"quyết định {row.get('decision')!r} ngoài {sorted(HUMAN_VERDICT)}")
        review[frozenset((row["left"], row["right"]))] = row["decision"]
    return review


def identity_prompt_hash(model_id, generation):
    return digest([load_prompt("a10", "identity"), IDENTITY_SCHEMA, model_id, generation])


def _concept(node):
    anchor = node.get("anchor") or {}
    return {"name": node["name"], "description": node.get("description", ""),
            "aliases": sorted({str(a["name"] if isinstance(a, dict) else a) for a in node.get("aliases", [])}),
            "anchor_sentence": anchor.get("sentence")}


def verify_identity_pairs(store, model, doc_id, inputs, *, generation, concurrency, planning=False):
    """Lượt độc lập dùng chung cho pipeline và tập kiểm: không nhận lời phán/lý do lượt 1."""
    system_prompt = load_prompt("a10", "identity_verify")
    prompt_hash = digest([system_prompt, VERIFY_SCHEMA, model.model_id, generation])
    source_hash = digest(inputs)
    checkpoint_id = "identity-verify-" + digest([prompt_hash, source_hash])
    checkpoint = store.load_checkpoint(doc_id, checkpoint_id)
    resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
    answers = dict(checkpoint["answers"]) if resumable else {}
    log = list(checkpoint["decision_log"]) if resumable else []
    metrics = Counter(checkpoint["metrics"]) if resumable else Counter()
    pending = [data for data in inputs if data["pair_id"] not in answers]
    if planning:
        return model_plan(pending, system_prompt=system_prompt, generation=generation, unit="pair",
                          checkpoint_id=checkpoint_id, metrics=metrics)
    for start in range(0, len(pending), PAIR_BATCH):
        group = pending[start:start + PAIR_BATCH]
        jobs = []
        for data in group:
            def validate(value, pair_id=data["pair_id"]):
                if not isinstance(value, dict) or value.get("pair_id") != pair_id:
                    raise ValueError("xác minh sai pair_id")
                if value.get("relation") not in VERIFY_RELATIONS:
                    raise ValueError("relation ngoài tập đóng")
                if not isinstance(value.get("reason"), str) or not value["reason"].strip():
                    raise ValueError("xác minh thiếu reason")
            jobs.append(ModelJob("identity_verify", model, system_prompt, prompt_hash, data, VERIFY_SCHEMA, validate))
        values, rows, counts = run_model_jobs(jobs, log, concurrency=concurrency)
        log.extend(rows)
        metrics.update(counts)
        answers.update({data["pair_id"]: value or {"pair_id": data["pair_id"], "relation": None,
                                                   "reason": "invalid_response"} for data, value in zip(group, values)})
        store.save_checkpoint(doc_id, checkpoint_id, {"source_hash": source_hash, "answers": answers,
                                                      "decision_log": log, "metrics": dict(metrics)})
    return answers, log, metrics


class JudgeIdentity:
    """Danh tính (v3 R8/R8b). Stage `identity` sau `teaching`, phán rồi xác minh độc lập mọi `same`.

    Mỗi cặp ứng viên một lời phán trên hai câu neo; bản đồ gộp chỉ từ nhóm mà mọi cặp đều `same`. Khái niệm bị gộp rời
    `nodes` sang `merged_nodes` (có `merged_into`); cạnh chuyển sang đại diện rồi gỡ chu trình bằng hàm của A9. Canonical
    và provenance không đổi; bộ chấm áp cùng `identity_map` lên bộ vàng.
    """

    def __init__(self, store, model, *, concurrency=4, generation=None, review=None,
                 semantic_top_k=SEMANTIC_TOP_K, semantic_min_similarity=SEMANTIC_MIN_SIMILARITY):
        """`review`: {frozenset((node_id, node_id)): quyết định trong bảng T5}."""
        self.store = store
        self.review = dict(review or {})
        self.model = model
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 1024}
        self.semantic_top_k = semantic_top_k
        self.semantic_min_similarity = semantic_min_similarity

    def execute(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream, planning=False):
        if upstream.payload.get("stage") != "teaching":
            raise ValueError("stage identity cần artifact teaching")
        prompt_hash = identity_prompt_hash(self.model.model_id, self.generation)
        first_config = {"algorithm_id": "a10-identity-v2", "teaching_version": upstream.version,
                  "teaching_config_hash": upstream.manifest["config_hash"],
                  # A10 tìm chunk theo config của artifact đầu vào
                  "chunks_version": upstream.manifest.get("config", {}).get("chunks_version"),
                  "model_id": self.model.model_id,
                  "generation": self.generation, "prompt_hash": prompt_hash, "merge_rule": "verified-clique-v1",
                  "candidate_rule": "nfkc-latex-dash+initialism+generic-prefix+same-anchor+description-top-k-v2",
                  "semantic_top_k": self.semantic_top_k, "semantic_min_similarity": self.semantic_min_similarity,
                  "semantic_vectors": "a6-description; anchor-sentence-in-judge-input",
                  "review_hash": digest(sorted([sorted(pair), decision] for pair, decision in self.review.items())),
                  "pricing_usd_per_million": PRICING_USD_PER_MILLION, "pricing_source": PRICING_SOURCE}
        # Giữ nguyên khoá lượt 1 của v2: đổi luật gộp hoặc prompt xác minh không được hỏi lại lượt 1.
        first_config_hash = digest(first_config)
        config = {**first_config, "algorithm_id": "a10-identity-v3",
                  "first_pass_config_hash": first_config_hash,
                  "verify_prompt_hash": digest([load_prompt("a10", "identity_verify"), VERIFY_SCHEMA,
                                                 self.model.model_id, self.generation]),
                  "verify_relations": list(VERIFY_RELATIONS), "representative_rule": "taught-then-earliest-v1",
                  "merged_order_rule": "changed-endpoints-representative-position-v1"}
        config_hash, source_hash = digest(config), digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)

        nodes = upstream.payload["nodes"]
        placed = [n for n in nodes if n.get("learnable") and n.get("teaching_status") not in EXCLUDED_STATUSES]
        by_id = {n["node_id"]: n for n in placed}
        vector_version = upstream.payload.get("node_vectors_version")
        vectors = (self.store.load_graph(doc_id, vector_version).payload["node_vectors"] if vector_version is not None
                   else upstream.payload.get("node_vectors", {}))
        vectors = {**vectors, **upstream.payload.get("incremental_node_vectors", {})}
        pairs = [{"pair_id": f"p{index}", **row} for index, row in enumerate(identity_candidates(
            placed, vectors=vectors, semantic_top_k=self.semantic_top_k,
            semantic_min_similarity=self.semantic_min_similarity), 1)]

        checkpoint_id = "identity-" + first_config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        answers = dict(checkpoint["answers"]) if resumable else {}
        decision_log = list(checkpoint["decision_log"]) if resumable else []
        metrics = Counter(checkpoint["metrics"]) if resumable else Counter()
        system_prompt = load_prompt("a10", "identity")
        pending = [pair for pair in pairs if pair["pair_id"] not in answers]
        if planning:
            inputs = [{"pair_id": pair["pair_id"], "paired_because": pair["reasons"],
                       "first": _concept(by_id[pair["left"]]), "second": _concept(by_id[pair["right"]])}
                      for pair in pending]
            first = model_plan(inputs, system_prompt=system_prompt, generation=self.generation, unit="pair",
                               checkpoint_id=checkpoint_id, metrics=metrics)
            verify_inputs = [{"pair_id": pair["pair_id"], "first": _concept(by_id[pair["left"]]),
                              "second": _concept(by_id[pair["right"]])} for pair in pairs
                             if pair["pair_id"] not in answers or answers[pair["pair_id"]]["verdict"] == "same"]
            verification = verify_identity_pairs(self.store, self.model, doc_id, verify_inputs,
                generation=self.generation, concurrency=self.concurrency, planning=True)
            first.remaining_items += verification.remaining_items
            first.calls_estimate += verification.calls_estimate
            first.usd_estimate = round(first.usd_estimate + verification.usd_estimate, 6)
            first.note += (f" Lượt 1 còn {len(pending)} cặp; xác minh tối đa {verification.remaining_items} cặp "
                           "(giả sử mọi cặp chưa phán đều same); checkpoint riêng " + verification.checkpoint_id + ".")
            return first
        for start in range(0, len(pending), PAIR_BATCH):
            group = pending[start:start + PAIR_BATCH]
            jobs = []
            for pair in group:
                data = {"pair_id": pair["pair_id"], "paired_because": pair["reasons"],
                        "first": _concept(by_id[pair["left"]]), "second": _concept(by_id[pair["right"]])}

                def validate(value, pair_id=pair["pair_id"]):
                    validate_identity_response(value, pair_id=pair_id)

                jobs.append(ModelJob("identity", self.model, system_prompt, prompt_hash, data, IDENTITY_SCHEMA, validate))
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=self.concurrency)
            decision_log.extend(rows)
            metrics.update(counts)
            for pair, value in zip(group, values):
                # Hỏng quá lượt sửa: không gộp, và cặp còn mở (tính vào Q2).
                answers[pair["pair_id"]] = value or {"pair_id": pair["pair_id"], "verdict": "uncertain",
                                                     "reason": "invalid_response"}
            self.store.save_checkpoint(doc_id, checkpoint_id, {"source_hash": source_hash, "answers": answers,
                                                               "decision_log": decision_log, "metrics": dict(metrics)})

        verify_inputs = [{"pair_id": pair["pair_id"], "first": _concept(by_id[pair["left"]]),
                          "second": _concept(by_id[pair["right"]])} for pair in pairs
                         if answers[pair["pair_id"]]["verdict"] == "same"]
        verified, verify_log, verify_metrics = verify_identity_pairs(self.store, self.model, doc_id, verify_inputs,
            generation=self.generation, concurrency=self.concurrency)
        metrics.update(verify_metrics)
        log = []
        for pair in pairs:
            answer = answers[pair["pair_id"]]
            check = verified.get(pair["pair_id"], {})
            row = {**pair, "model_verdict": answer["verdict"], "verdict": answer["verdict"], "reason": answer["reason"],
                   "verify_relation": check.get("relation"), "verify_reason": check.get("reason")}
            if answer["verdict"] == "same":
                row["verdict"] = ("uncertain" if check["relation"] is None else
                                  ("same" if check["relation"] == "dong_nhat" else "different"))
            decision = self.review.get(frozenset((pair["left"], pair["right"])))
            if decision is not None:
                row.update(verdict=HUMAN_VERDICT[decision], human_decision=decision)
            log.append(row)
        position = {n["node_id"]: (n.get("teaching_order_index") if n.get("teaching_order_index") is not None
                                   else n.get("first_order_index", 0)) for n in nodes}
        mapping, open_groups = identity_map(log, position, taught={n["node_id"] for n in placed if n.get("teaching_status") == "taught"})
        edges, removed = merge_and_break_cycles(upstream.payload["requires_edges"], mapping, position)
        open_pairs = [row["pair_id"] for row in log if row["verdict"] == "uncertain"]
        tokens_in = sum(v for k, v in metrics.items() if k.endswith("_input_tokens"))
        tokens_out = sum(v for k, v in metrics.items() if k.endswith("_output_tokens"))
        cost = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
        previous = upstream.payload.get("cost_summary", {})
        stats = {"identity_pair_count": len(pairs), "identity_verdicts": dict(sorted(Counter(r["verdict"] for r in log).items())),
                 "merged_node_count": len(mapping), "identity_removed_edge_count": len(removed),
                 "identity_open_count": len(open_groups) + len(open_pairs), **dict(sorted(metrics.items()))}
        payload = {**upstream.payload, "stage": "identity",
                   "nodes": merge_identity_nodes(nodes, mapping),
                   "merged_nodes": [{**n, "merged_into": mapping[n["node_id"]]} for n in nodes if n["node_id"] in mapping],
                   "requires_edges": edges, "identity_removed_edges": removed, "identity_map": mapping,
                   "identity_log": log, "identity_open_groups": open_groups, "identity_open_pairs": open_pairs,
                   "identity_decision_log": decision_log,
                   "identity_verify_decision_log": verify_log,
                   "cost_summary": {**previous, "identity_usd": cost, "usd": float(previous.get("usd", 0.0)) + cost},
                   "stats": stats}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": "identity", "stats": stats,
                                                          "llm_transport": getattr(self.model, "transport", "unknown")})
        return artifact, False
