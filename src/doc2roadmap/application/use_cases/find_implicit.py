from __future__ import annotations

from collections import Counter
from typing import Any

from doc2roadmap.application.stage_measurements import measure_stage, resume_measurements
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.implicit import (
    IMPLICIT_CONFIDENCE,
    IMPLICIT_KIND,
    add_implicit_edges,
    implicit_candidates,
    validate_implicit_response,
)
from doc2roadmap.domain.teaching import EXCLUDED_STATUSES

IMPLICIT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "node_id": {"type": "string"},
        "prerequisites": {
            "type": "array",
            "items": {"type": "object",
                      "properties": {"node_id": {"type": "string"}, "quote": {"type": "string"},
                                     "reason": {"type": "string"}},
                      "required": ["node_id", "quote", "reason"]},
        },
    },
    "required": ["node_id", "prerequisites"],
}
K_CANDIDATES = 30
DESCRIPTION_CHARS = 200
TARGET_BATCH = 8


def implicit_prompt_hash(model_id, generation):
    return digest([load_prompt("a8", "implicit"), IMPLICIT_SCHEMA, model_id, generation])


class FindImplicitPrerequisites:
    """Pass cạnh ngầm (vé v2-06, spec v2 W20). Stage `implicit`, sau `teaching` hoặc `identity`; chưa vào chuỗi mặc định.

    Mỗi khái niệm đích một lời gọi: đoạn dạy nó (chunk của câu neo, không có thì chunk định nghĩa) và K khái niệm dạy ngay
    trước chưa là tổ tiên. Cạnh nhận được mang `evidence_kind="ngam"`, căn cứ là cụm nguyên văn trong đoạn của đích.
    """

    def __init__(self, store, model, *, concurrency=4, generation=None, k=K_CANDIDATES):
        self.store = store
        self.model = model
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 2048}
        self.k = k

    @measure_stage
    def execute(self, doc_id, *, upstream):
        if upstream.payload.get("stage") not in ("teaching", "identity"):
            raise ValueError("stage implicit cần artifact teaching hoặc identity")
        chunks_version = upstream.manifest["config"]["chunks_version"]
        chunk_by_id = {c.chunk_id: c for c in self.store.load_chunks(doc_id, chunks_version).result.chunks}
        prompt_hash = implicit_prompt_hash(self.model.model_id, self.generation)
        config = {"algorithm_id": "a8-implicit-v1", "upstream_version": upstream.version,
                  "upstream_config_hash": upstream.manifest["config_hash"], "chunks_version": chunks_version,
                  "model_id": self.model.model_id, "generation": self.generation, "prompt_hash": prompt_hash,
                  "k": self.k, "description_chars": DESCRIPTION_CHARS, "confidence": IMPLICIT_CONFIDENCE,
                  "pricing_usd_per_million": PRICING_USD_PER_MILLION, "pricing_source": PRICING_SOURCE}
        config_hash, source_hash = digest(config), digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True

        placed = [n for n in upstream.payload["nodes"]
                  if n.get("learnable") and n.get("teaching_status") not in EXCLUDED_STATUSES]
        by_id = {n["node_id"]: n for n in placed}

        def position(node):
            order = node.get("teaching_order_index")
            return (order if order is not None else node.get("first_order_index", 0), node["node_id"])

        def passage(node):
            for chunk_id in [*(node.get("teaching_chunk_ids") or []), *node.get("defining_chunk_ids", [])]:
                if chunk_id in chunk_by_id:
                    return chunk_by_id[chunk_id]
            return None

        order = [n["node_id"] for n in sorted(placed, key=position)]
        edges = upstream.payload["requires_edges"]
        candidates = implicit_candidates(order, edges, k=self.k)
        targets = [node_id for node_id in order if candidates[node_id] and passage(by_id[node_id]) is not None]

        checkpoint_id = "implicit-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        resume_measurements(checkpoint if resumable else None)
        answers = dict(checkpoint["answers"]) if resumable else {}
        decision_log = list(checkpoint["decision_log"]) if resumable else []
        metrics = Counter(checkpoint["metrics"]) if resumable else Counter()
        system_prompt = load_prompt("a8", "implicit")
        pending = [node_id for node_id in targets if node_id not in answers]
        for start in range(0, len(pending), TARGET_BATCH):
            group = pending[start:start + TARGET_BATCH]
            jobs = []
            for node_id in group:
                node, chunk = by_id[node_id], passage(by_id[node_id])
                data = {"node_id": node_id,
                        "target": {"name": node["name"], "description": node.get("description", "")},
                        "passage": {"chunk_id": chunk.chunk_id,
                                    "section_path": list(getattr(chunk, "section_path", []) or []),
                                    "text": chunk.text},
                        "candidates": [{"node_id": c, "name": by_id[c]["name"],
                                        "description": by_id[c].get("description", "")[:DESCRIPTION_CHARS]}
                                       for c in candidates[node_id]]}

                def validate(value, node_id=node_id, text=chunk.text):
                    validate_implicit_response(value, node_id=node_id, candidates=candidates[node_id],
                                               definition_text=text)

                jobs.append(ModelJob("implicit", self.model, system_prompt, prompt_hash, data, IMPLICIT_SCHEMA, validate))
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=self.concurrency)
            decision_log.extend(rows)
            metrics.update(counts)
            for node_id, value in zip(group, values):
                # Hỏng quá lượt sửa: không thêm cạnh nào cho đích này.
                answers[node_id] = value or {"node_id": node_id, "prerequisites": [], "invalid": True}
            self.store.save_checkpoint(doc_id, checkpoint_id, {"source_hash": source_hash, "answers": answers,
                                                               "decision_log": decision_log, "metrics": dict(metrics)})

        new = []
        for node_id in targets:
            chunk = passage(by_id[node_id])
            for row in answers[node_id]["prerequisites"]:
                new.append({"source": row["node_id"], "target": node_id, "edge_type": "requires",
                            "evidence_kind": IMPLICIT_KIND, "chunk_ids": [chunk.chunk_id], "quote": row["quote"],
                            "reason": row["reason"], "confidence": IMPLICIT_CONFIDENCE, "origin": "implicit_pass"})
        merged, removed = add_implicit_edges(edges, new)
        added = sum(1 for edge in merged if edge.get("origin") == "implicit_pass")
        tokens_in = sum(v for k, v in metrics.items() if k.endswith("_input_tokens"))
        tokens_out = sum(v for k, v in metrics.items() if k.endswith("_output_tokens"))
        cost = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
        previous = upstream.payload.get("cost_summary", {})
        stats = {"implicit_target_count": len(targets), "implicit_proposed": len(new), "implicit_added": added,
                 "implicit_removed_by_cycles": len(removed),
                 "implicit_invalid_targets": sum(1 for a in answers.values() if a.get("invalid")),
                 **dict(sorted(metrics.items()))}
        payload = {**upstream.payload, "stage": "implicit", "requires_edges": merged, "implicit_removed_edges": removed,
                   "implicit_log": [answers[node_id] for node_id in targets], "implicit_decision_log": decision_log,
                   "cost_summary": {**previous, "implicit_usd": cost, "usd": float(previous.get("usd", 0.0)) + cost},
                   "stats": stats}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": "implicit", "stats": stats,
                                                          "llm_transport": getattr(self.model, "transport", "unknown")})
        return artifact, False
