from __future__ import annotations

from collections import Counter
from typing import Any

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.anchors import STATUSES, anchor_fields, candidate_sentences, validate_anchor_response
from doc2roadmap.domain.canonical import digest

ANCHOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "node_id": {"type": "string"},
        "status": {"type": "string", "enum": list(STATUSES)},
        "anchor": {"type": "string"},
        "quote": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["node_id", "status", "reason"],
}
HARD_CHANNELS = {"exact", "alias", "provenance"}
CANDIDATES = 6
NODE_BATCH = 8


def anchor_prompt_hash(model_id, generation):
    return digest([load_prompt("a10", "anchor"), ANCHOR_SCHEMA, model_id, generation])


class AnchorConcepts:
    """Neo định nghĩa — C8 v3 (spec v2, W11–W13). Stage `teaching`, chưa nằm trong chuỗi mặc định cho tới khi qua cổng.

    Ứng viên là câu, gom từ đoạn định nghĩa, đoạn căn cứ A3 và mọi chunk có mention cứng — không chỉ `defining_chunk_ids`,
    vốn hay trỏ vào đoạn dùng. Chỉ ghi thêm trường; provenance gốc giữ nguyên nên danh tính vàng không đổi.
    """

    def __init__(self, store, model, *, concurrency=4, generation=None):
        self.store = store
        self.model = model
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 2048}

    def execute(self, doc_id, *, upstream):
        if upstream.payload.get("stage") != "validated":
            raise ValueError("stage teaching cần artifact validated")
        edges = self.store.load_graph(doc_id, upstream.manifest["config"]["edges_version"])
        chunks_artifact = self.store.load_chunks(doc_id, edges.manifest["config"]["chunks_version"])
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks_artifact.result.chunks}
        prompt_hash = anchor_prompt_hash(self.model.model_id, self.generation)
        config = {"algorithm_id": "a10-teaching-anchor-v3", "validated_version": upstream.version,
                  "validated_config_hash": upstream.manifest["config_hash"], "chunks_version": chunks_artifact.version,
                  "model_id": self.model.model_id, "generation": self.generation, "prompt_hash": prompt_hash,
                  "candidates": CANDIDATES, "candidate_rule": "nfkc-name+a3-evidence",
                  "pricing_usd_per_million": PRICING_USD_PER_MILLION,
                  "pricing_source": PRICING_SOURCE}
        config_hash, source_hash = digest(config), digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True

        mentioned = {}
        for chunk_id, rows in upstream.payload.get("mention_map", {}).items():
            for node_id, row in rows.items():
                if HARD_CHANNELS & set(row.get("channels", [])):
                    mentioned.setdefault(node_id, set()).add(chunk_id)

        checkpoint_id = "anchor-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        answers = dict(checkpoint["answers"]) if resumable else {}
        decision_log = list(checkpoint["decision_log"]) if resumable else []
        metrics = Counter(checkpoint["metrics"]) if resumable else Counter()

        nodes = upstream.payload["nodes"]
        candidates_of = {}
        for node in nodes:
            if not node.get("learnable"):
                continue
            ids = set(node.get("defining_chunk_ids", [])) | mentioned.get(node["node_id"], set())
            ids |= {span["chunk_id"] for span in node.get("evidence", []) if isinstance(span, dict) and "chunk_id" in span}
            candidates_of[node["node_id"]] = candidate_sentences(
                node, [chunk_by_id[c] for c in ids if c in chunk_by_id], limit=CANDIDATES)
        pending = [node for node in sorted(nodes, key=lambda n: n["node_id"])
                   if node["node_id"] in candidates_of and candidates_of[node["node_id"]]
                   and node["node_id"] not in answers]
        system_prompt = load_prompt("a10", "anchor")
        for start in range(0, len(pending), NODE_BATCH):
            group = pending[start:start + NODE_BATCH]
            jobs = []
            for node in group:
                candidates = candidates_of[node["node_id"]]
                data = {"node_id": node["node_id"],
                        "concept": {"name": node["name"], "description": node.get("description", ""),
                                    "aliases": sorted({str(a["name"] if isinstance(a, dict) else a)
                                                       for a in node.get("aliases", [])})},
                        "candidates": [{"cand_id": c["cand_id"], "chunk_id": c["chunk_id"],
                                        "section_path": list(getattr(chunk_by_id[c["chunk_id"]], "section_path", []) or []),
                                        "sentence": c["sentence"], "context": c["context"]} for c in candidates]}

                def validate(value, node_id=node["node_id"], candidates=candidates):
                    validate_anchor_response(value, node_id=node_id, candidates=candidates)

                jobs.append(ModelJob("anchor", self.model, system_prompt, prompt_hash, data, ANCHOR_SCHEMA, validate))
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=self.concurrency)
            decision_log.extend(rows)
            metrics.update(counts)
            for node, value in zip(group, values):
                # Hỏng quá lượt sửa: chưa đủ căn cứ để loại, giữ khái niệm.
                answers[node["node_id"]] = value or {"node_id": node["node_id"], "status": "uncertain",
                                                     "reason": "invalid_response"}
            self.store.save_checkpoint(doc_id, checkpoint_id, {"source_hash": source_hash, "answers": answers,
                                                               "decision_log": decision_log, "metrics": dict(metrics)})

        checked = []
        for node in nodes:
            if not node.get("learnable"):
                checked.append(node)
            elif node["node_id"] in answers:
                checked.append({**node, **anchor_fields(answers[node["node_id"]], candidates_of[node["node_id"]])})
            else:
                checked.append({**node, "teaching_status": "unchecked", "teaching_chunk_ids": [],
                                "teaching_order_index": None, "teaching_conflict": False, "anchor": None})
        tokens_in = sum(v for k, v in metrics.items() if k.endswith("_input_tokens"))
        tokens_out = sum(v for k, v in metrics.items() if k.endswith("_output_tokens"))
        cost = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
        previous = upstream.payload.get("cost_summary", {})
        stats = {"teaching_status_counts": dict(sorted(Counter(n["teaching_status"] for n in checked
                                                                 if "teaching_status" in n).items())),
                 **dict(sorted(metrics.items()))}
        payload = {**upstream.payload, "stage": "teaching", "nodes": checked,
                   "anchor_log": [{"node_id": k, **v} for k, v in sorted(answers.items())],
                   "anchor_decision_log": decision_log,
                   "cost_summary": {**previous, "teaching_usd": cost, "usd": float(previous.get("usd", 0.0)) + cost},
                   "stats": stats}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": "teaching", "stats": stats})
        return artifact, False
