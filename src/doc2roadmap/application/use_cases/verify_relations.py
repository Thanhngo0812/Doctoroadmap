from __future__ import annotations

from collections import Counter

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.relation_prompt import RELATION_SCHEMA, relation_prompt_hash, relation_system_prompt
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.relation_check import apply_relation_verdicts, edge_id, validate_relation_response

PASSAGES_PER_NODE = 2
EVIDENCE_PER_EDGE = 3
BATCH = 16


class VerifyRelations:
    """Stage `verified` (C10): mỗi cạnh `requires` còn là ràng buộc cứng chỉ khi định nghĩa của đích dùng tiên quyết.

    Hồ sơ chứa đoạn dạy của **cả hai** đầu (đoạn định nghĩa nếu chưa có đoạn dạy) và các đoạn bằng chứng của cạnh.
    Cạnh chỉ bị gỡ khi có câu trích chứng minh; thiếu hoặc hỏng câu trả lời thì cạnh vẫn cứng.
    """

    def __init__(self, store, model, *, concurrency=4, generation=None):
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        self.store = store
        self.model = model
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 2048}

    def _upstream(self, doc_id, latest):
        # Chỉ lần ngược từ các stage đứng **sau** bước này; từ `edges` trở về trước thì `teaching` không bao giờ tới.
        artifact = latest
        while artifact.payload.get("stage") in ("verified", "stages"):
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                break
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    def _chunks_version(self, doc_id, upstream):
        config = upstream.manifest.get("config", {})
        if config.get("chunks_version") is not None:
            return config["chunks_version"]
        return self.store.load_graph(doc_id, config["edges_version"]).manifest["config"]["chunks_version"]

    def execute(self, doc_id, *, upstream=None):
        upstream = upstream if upstream is not None else self._upstream(doc_id, self.store.load_latest_graph(doc_id))
        if upstream.payload.get("stage") not in ("teaching", "validated"):
            raise ValueError("stage verified cần artifact teaching hoặc validated")
        chunks_artifact = self.store.load_chunks(doc_id, self._chunks_version(doc_id, upstream))
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks_artifact.result.chunks}
        prompt_hash = relation_prompt_hash(self.model.model_id, self.generation)
        config = {
            "algorithm_id": "a9-relation-check-v1",
            "upstream_version": upstream.version,
            "upstream_config_hash": upstream.manifest["config_hash"],
            "chunks_version": chunks_artifact.version,
            "model_id": self.model.model_id,
            "generation": self.generation,
            "prompt_hash": prompt_hash,
            "passages": {"per_node": PASSAGES_PER_NODE, "evidence_per_edge": EVIDENCE_PER_EDGE},
            "checkpoint": "progress-file-outside-version-chain-v1",
            "pricing_usd_per_million": PRICING_USD_PER_MILLION,
            "pricing_source": PRICING_SOURCE,
        }
        config_hash = digest(config)
        source_hash = digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True

        def ordered(chunk_ids):
            return sorted((chunk_by_id[value] for value in set(chunk_ids) if value in chunk_by_id),
                          key=lambda chunk: (chunk.order_index, chunk.chunk_id))

        def shown(chunk):
            return {"chunk_id": chunk.chunk_id, "section_path": list(getattr(chunk, "section_path", []) or []),
                    "text": chunk.text}

        node_by_id = {node["node_id"]: node for node in upstream.payload["nodes"]}

        def side(node_id):
            node = node_by_id[node_id]
            passages = ordered(node.get("teaching_chunk_ids") or node.get("defining_chunk_ids", []))[:PASSAGES_PER_NODE]
            aliases = sorted({str(alias["name"] if isinstance(alias, dict) else alias) for alias in node.get("aliases", [])})
            return passages, {"node_id": node_id, "name": node["name"], "description": node.get("description", ""),
                              "aliases": aliases}

        checkpoint_id = "relation-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        if checkpoint is not None and checkpoint.get("source_hash") == source_hash:
            verdicts = dict(checkpoint["verdicts"])
            decision_log = list(checkpoint["decision_log"])
            metrics = Counter(checkpoint["relation_model_metrics"])
        else:
            verdicts, decision_log, metrics = {}, [], Counter()

        edges = [edge for edge in upstream.payload["requires_edges"] if edge.get("edge_type") == "requires"]
        pending = [edge for edge in sorted(edges, key=edge_id) if edge_id(edge) not in verdicts
                   and edge["source"] in node_by_id and edge["target"] in node_by_id]
        system_prompt = relation_system_prompt()
        for start in range(0, len(pending), BATCH):
            batch = pending[start:start + BATCH]
            jobs = []
            for edge in batch:
                prerequisite_passages, prerequisite = side(edge["source"])
                target_passages, target = side(edge["target"])
                seen = {chunk.chunk_id for chunk in [*prerequisite_passages, *target_passages]}
                evidence = [chunk for chunk in ordered(edge.get("chunk_ids", [])) if chunk.chunk_id not in seen]
                evidence = evidence[:EVIDENCE_PER_EDGE]
                data = {
                    "edge_id": edge_id(edge),
                    "prerequisite": {**prerequisite, "passages": [shown(chunk) for chunk in prerequisite_passages]},
                    "target": {**target, "passages": [shown(chunk) for chunk in target_passages]},
                    "evidence": [shown(chunk) for chunk in evidence],
                }
                texts = [chunk.text for chunk in [*prerequisite_passages, *target_passages, *evidence]]

                def validate(value, key=edge_id(edge), texts=texts):
                    validate_relation_response(value, edge_id=key, passages=texts)

                jobs.append(ModelJob("relation", self.model, system_prompt, prompt_hash, data, RELATION_SCHEMA, validate))
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=self.concurrency)
            decision_log.extend(rows)
            metrics.update(counts)
            for edge, value in zip(batch, values):
                # Phản hồi hỏng quá lượt sửa: không đủ căn cứ để gỡ ràng buộc, cạnh giữ nguyên là cứng.
                answer = value or {"verdict": "unresolved", "reason": "invalid_response"}
                verdicts[edge_id(edge)] = {"verdict": answer["verdict"], "quote": answer.get("quote"),
                                           "reason": answer["reason"]}
            self.store.save_checkpoint(doc_id, checkpoint_id, {
                "source_hash": source_hash,
                "verdicts": verdicts,
                "decision_log": decision_log,
                "relation_model_metrics": dict(sorted(metrics.items())),
            })

        result = apply_relation_verdicts(edges, verdicts)
        input_tokens = sum(value for key, value in metrics.items() if key.endswith("_input_tokens"))
        output_tokens = sum(value for key, value in metrics.items() if key.endswith("_output_tokens"))
        relation_cost = (input_tokens * PRICING_USD_PER_MILLION["input"]
                         + output_tokens * PRICING_USD_PER_MILLION["output"]) / 1_000_000
        previous = upstream.payload.get("cost_summary", {})
        cost_summary = {
            **previous,
            "input_tokens": int(previous.get("input_tokens", 0)) + input_tokens,
            "output_tokens": int(previous.get("output_tokens", 0)) + output_tokens,
            "relation_usd": relation_cost,
            "usd": float(previous.get("usd", 0.0)) + relation_cost,
        }
        stats = {
            "relation_verdict_counts": dict(sorted(Counter(value["verdict"] for value in verdicts.values()).items())),
            "requires_edge_count": len(result["requires"]),
            "recommended_edge_count": len(result["recommended"]),
            "rejected_edge_count": len(result["rejected"]),
            **dict(sorted(metrics.items())),
        }
        payload = {
            **upstream.payload,
            "stage": "verified",
            "requires_edges": result["requires"],
            "recommended_edges": result["recommended"],
            "rejected_edges": result["rejected"],
            "relation_log": [{"edge_id": key, **value} for key, value in sorted(verdicts.items())],
            "relation_decision_log": decision_log,
            "relation_model_metrics": dict(sorted(metrics.items())),
            "cost_summary": cost_summary,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=upstream.version,
            manifest_fields={"stage": "verified", "stats": stats},
        )
        return artifact, False
