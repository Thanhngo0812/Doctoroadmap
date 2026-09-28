from __future__ import annotations

from collections import Counter

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.teaching_prompt import TEACHING_SCHEMA, teaching_prompt_hash, teaching_system_prompt
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.teaching import teaching_status, validate_teaching_response, verdict_of

NODE_BATCH = 8


def _alias_names(node):
    return sorted({str(alias["name"] if isinstance(alias, dict) else alias) for alias in node.get("aliases", [])})


class CheckTeachingSources:
    """Stage `teaching`: mỗi đoạn định nghĩa của một node có thật sự **dạy** node đó không (C8).

    Chỉ ghi thêm trường, không sửa `defining_chunk_ids`, nên danh tính khái niệm mà bộ vàng đã đóng băng giữ nguyên.
    Nằm sau `validated` để không phải chạy lại A8/A9.
    """

    def __init__(self, store, model, *, concurrency=4, generation=None):
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        self.store = store
        self.model = model
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 2048}

    def _validated(self, doc_id, latest):
        artifact = latest
        while artifact.payload.get("stage") not in ("validated", "clusters"):
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                break
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    def execute(self, doc_id, *, upstream=None):
        validated = upstream if upstream is not None else self._validated(doc_id, self.store.load_latest_graph(doc_id))
        if validated.payload.get("stage") != "validated":
            raise ValueError("stage teaching cần artifact validated")
        edges = self.store.load_graph(doc_id, validated.manifest["config"]["edges_version"])
        chunks_artifact = self.store.load_chunks(doc_id, edges.manifest["config"]["chunks_version"])
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks_artifact.result.chunks}
        prompt_hash = teaching_prompt_hash(self.model.model_id, self.generation)
        config = {
            "algorithm_id": "a10-teaching-sources-v2",
            "validated_version": validated.version,
            "validated_config_hash": validated.manifest["config_hash"],
            "chunks_version": chunks_artifact.version,
            "model_id": self.model.model_id,
            "generation": self.generation,
            "prompt_hash": prompt_hash,
            "checkpoint": "progress-file-outside-version-chain-v1",
            "pricing_usd_per_million": PRICING_USD_PER_MILLION,
            "pricing_source": PRICING_SOURCE,
        }
        config_hash = digest(config)
        source_hash = digest(validated.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return cached, True

        checkpoint_id = "teaching-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        if checkpoint is not None and checkpoint.get("source_hash") == source_hash:
            completed = set(checkpoint["completed_nodes"])
            teaching_log = list(checkpoint["teaching_log"])
            decision_log = list(checkpoint["decision_log"])
            metrics = Counter(checkpoint["teaching_model_metrics"])
        else:
            completed, teaching_log, decision_log, metrics = set(), [], [], Counter()

        system_prompt = teaching_system_prompt()
        nodes = validated.payload["nodes"]
        pending = [node for node in sorted((value for value in nodes if value.get("learnable")),
                                           key=lambda value: value["node_id"]) if node["node_id"] not in completed]
        # Mỗi node chỉ có ~1–2 đoạn, nên gom nhiều node một lượt thì mức song song mới được dùng hết.
        for start in range(0, len(pending), NODE_BATCH):
            group = pending[start:start + NODE_BATCH]
            jobs, owners = [], []
            for node in group:
                passages = sorted((chunk_by_id[chunk_id] for chunk_id in set(node.get("defining_chunk_ids", []))
                                   if chunk_id in chunk_by_id), key=lambda chunk: (chunk.order_index, chunk.chunk_id))
                for chunk in passages:
                    data = {
                        "node_id": node["node_id"],
                        "chunk_id": chunk.chunk_id,
                        "concept": {"name": node["name"], "description": node.get("description", ""),
                                    "aliases": _alias_names(node)},
                        "passage": {"section_path": list(getattr(chunk, "section_path", []) or []),
                                    "text": chunk.text},
                    }

                    def validate(value, node_id=node["node_id"], chunk=chunk):
                        validate_teaching_response(value, node_id=node_id, chunk_id=chunk.chunk_id,
                                                   chunk_text=chunk.text)

                    jobs.append(ModelJob("teaching", self.model, system_prompt, prompt_hash, data, TEACHING_SCHEMA,
                                         validate))
                    owners.append((node, chunk))
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=self.concurrency)
            decision_log.extend(rows)
            metrics.update(counts)
            for (node, chunk), value in zip(owners, values):
                # Hết lượt sửa mà phản hồi vẫn hỏng thì không dùng nó để loại node: coi là chưa đủ căn cứ.
                answer = value or {"kind": "uncertain", "role": "uncertain", "reason": "invalid_response"}
                teaching_log.append({
                    "node_id": node["node_id"],
                    "chunk_id": chunk.chunk_id,
                    "order_index": chunk.order_index,
                    "kind": answer["kind"],
                    "role": answer["role"],
                    "verdict": verdict_of(answer),
                    "quote": answer.get("quote"),
                    "reason": answer["reason"],
                })
            completed.update(node["node_id"] for node in group)
            self.store.save_checkpoint(doc_id, checkpoint_id, {
                "source_hash": source_hash,
                "completed_nodes": sorted(completed),
                "teaching_log": teaching_log,
                "decision_log": decision_log,
                "teaching_model_metrics": dict(sorted(metrics.items())),
            })

        rows_by_node = {}
        for row in teaching_log:
            rows_by_node.setdefault(row["node_id"], []).append(row)
        checked = [
            {**node, **teaching_status(rows_by_node.get(node["node_id"], []))} if node.get("learnable") else node
            for node in nodes
        ]
        input_tokens = sum(value for key, value in metrics.items() if key.endswith("_input_tokens"))
        output_tokens = sum(value for key, value in metrics.items() if key.endswith("_output_tokens"))
        teaching_cost = (input_tokens * PRICING_USD_PER_MILLION["input"]
                         + output_tokens * PRICING_USD_PER_MILLION["output"]) / 1_000_000
        previous = validated.payload.get("cost_summary", {})
        cost_summary = {
            **previous,
            "input_tokens": int(previous.get("input_tokens", 0)) + input_tokens,
            "output_tokens": int(previous.get("output_tokens", 0)) + output_tokens,
            "teaching_usd": teaching_cost,
            "usd": float(previous.get("usd", 0.0)) + teaching_cost,
        }
        stats = {
            "teaching_status_counts": dict(sorted(Counter(
                node["teaching_status"] for node in checked if "teaching_status" in node).items())),
            "teaching_conflict_count": sum(bool(node.get("teaching_conflict")) for node in checked),
            **dict(sorted(metrics.items())),
        }
        payload = {
            **validated.payload,
            "stage": "teaching",
            "nodes": checked,
            "teaching_log": teaching_log,
            "teaching_decision_log": decision_log,
            "teaching_model_metrics": dict(sorted(metrics.items())),
            "cost_summary": cost_summary,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=validated.version,
            manifest_fields={"stage": "teaching", "stats": stats,
                             "llm_transport": getattr(self.model, "transport", "unknown")},
        )
        return artifact, False
