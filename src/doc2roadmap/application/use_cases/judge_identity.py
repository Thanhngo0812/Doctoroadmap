from __future__ import annotations

from collections import Counter
from typing import Any

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.identity import (
    VERDICTS,
    identity_candidates,
    identity_map,
    merge_and_break_cycles,
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
# Quyết định của người duyệt (T5) thắng phán của mô hình. Chỉ "Đồng ý gộp" cho gộp; "Không chắc" thì giữ tách.
HUMAN_VERDICT = {"Đồng ý gộp": "same", "Không gộp": "different", "Là hai nghĩa khác nhau": "sense_split",
                 "Không chắc": "different"}


def identity_prompt_hash(model_id, generation):
    return digest([load_prompt("a10", "identity"), IDENTITY_SCHEMA, model_id, generation])


def _concept(node):
    anchor = node.get("anchor") or {}
    return {"name": node["name"], "description": node.get("description", ""),
            "aliases": sorted({str(a["name"] if isinstance(a, dict) else a) for a in node.get("aliases", [])}),
            "anchor_sentence": anchor.get("sentence")}


class JudgeIdentity:
    """Danh tính (spec v2, W14–W15). Stage `identity` sau `teaching`, chưa nằm trong chuỗi mặc định cho tới khi qua cổng.

    Mỗi cặp ứng viên một lời phán trên hai câu neo; bản đồ gộp chỉ từ nhóm mà mọi cặp đều `same`. Khái niệm bị gộp rời
    `nodes` sang `merged_nodes` (có `merged_into`); cạnh chuyển sang đại diện rồi gỡ chu trình bằng hàm của A9. Canonical
    và provenance không đổi; bộ chấm áp cùng `identity_map` lên bộ vàng.
    """

    def __init__(self, store, model, *, concurrency=4, generation=None, review=None):
        """`review`: {frozenset((node_id, node_id)): quyết định trong bảng T5}."""
        self.store = store
        self.review = dict(review or {})
        self.model = model
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 1024}

    def execute(self, doc_id, *, upstream):
        if upstream.payload.get("stage") != "teaching":
            raise ValueError("stage identity cần artifact teaching")
        prompt_hash = identity_prompt_hash(self.model.model_id, self.generation)
        config = {"algorithm_id": "a10-identity-v1", "teaching_version": upstream.version,
                  "teaching_config_hash": upstream.manifest["config_hash"],
                  # A10 tìm chunk theo config của artifact đầu vào
                  "chunks_version": upstream.manifest.get("config", {}).get("chunks_version"),
                  "model_id": self.model.model_id,
                  "generation": self.generation, "prompt_hash": prompt_hash, "merge_rule": "verified-clique-v1",
                  "review_hash": digest(sorted([sorted(pair), decision] for pair, decision in self.review.items())),
                  "pricing_usd_per_million": PRICING_USD_PER_MILLION, "pricing_source": PRICING_SOURCE}
        config_hash, source_hash = digest(config), digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True

        nodes = upstream.payload["nodes"]
        placed = [n for n in nodes if n.get("learnable") and n.get("teaching_status") not in EXCLUDED_STATUSES]
        by_id = {n["node_id"]: n for n in placed}
        pairs = [{"pair_id": f"p{index}", **row} for index, row in enumerate(identity_candidates(placed), 1)]

        checkpoint_id = "identity-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        answers = dict(checkpoint["answers"]) if resumable else {}
        decision_log = list(checkpoint["decision_log"]) if resumable else []
        metrics = Counter(checkpoint["metrics"]) if resumable else Counter()
        system_prompt = load_prompt("a10", "identity")
        pending = [pair for pair in pairs if pair["pair_id"] not in answers]
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

        log = []
        for pair in pairs:
            answer = answers[pair["pair_id"]]
            row = {**pair, "model_verdict": answer["verdict"], "verdict": answer["verdict"], "reason": answer["reason"]}
            decision = self.review.get(frozenset((pair["left"], pair["right"])))
            if decision is not None:
                row.update(verdict=HUMAN_VERDICT[decision], human_decision=decision)
            log.append(row)
        position = {n["node_id"]: (n.get("teaching_order_index") if n.get("teaching_order_index") is not None
                                   else n.get("first_order_index", 0)) for n in placed}
        mapping, open_groups = identity_map(log, position)
        edges, removed = merge_and_break_cycles(upstream.payload["requires_edges"], mapping)
        open_pairs = [row["pair_id"] for row in log if row["verdict"] == "uncertain"]
        tokens_in = sum(v for k, v in metrics.items() if k.endswith("_input_tokens"))
        tokens_out = sum(v for k, v in metrics.items() if k.endswith("_output_tokens"))
        cost = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
        previous = upstream.payload.get("cost_summary", {})
        stats = {"identity_pair_count": len(pairs), "identity_verdicts": dict(sorted(Counter(r["verdict"] for r in log).items())),
                 "merged_node_count": len(mapping), "identity_removed_edge_count": len(removed),
                 "identity_open_count": len(open_groups) + len(open_pairs), **dict(sorted(metrics.items()))}
        payload = {**upstream.payload, "stage": "identity",
                   "nodes": [n for n in nodes if n["node_id"] not in mapping],
                   "merged_nodes": [{**n, "merged_into": mapping[n["node_id"]]} for n in nodes if n["node_id"] in mapping],
                   "requires_edges": edges, "identity_removed_edges": removed, "identity_map": mapping,
                   "identity_log": log, "identity_open_groups": open_groups, "identity_open_pairs": open_pairs,
                   "identity_decision_log": decision_log,
                   "cost_summary": {**previous, "identity_usd": cost, "usd": float(previous.get("usd", 0.0)) + cost},
                   "stats": stats}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": "identity", "stats": stats})
        return artifact, False
