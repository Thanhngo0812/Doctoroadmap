from __future__ import annotations

from collections import Counter

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.anchors import label_families, numbered_label, validate_display_name
from doc2roadmap.domain.canonical import digest

DISPLAY_SCHEMA = {"type": "object", "properties": {"node_id": {"type": "string"},
    "display_name": {"type": "string"}}, "required": ["node_id", "display_name"]}


class NameConceptLabels:
    """Vé 11: đặt tên hiển thị sau danh tính, không phán lại neo hoặc danh tính."""

    def __init__(self, store, model, *, concurrency=4, generation=None):
        self.store, self.model, self.concurrency = store, model, concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 512}

    def plan(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream, planning=True)

    def execute(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream)

    def _run(self, doc_id, *, upstream, planning=False):
        if upstream.payload.get("stage") not in {"teaching", "identity"}:
            raise ValueError("đặt tên nhãn cần artifact teaching/identity")
        chunks = self.store.load_role_chunks(doc_id, upstream.manifest["config"]["chunks_version"]).result.chunks
        nodes = upstream.payload["nodes"]
        families = label_families(nodes, chunks)
        generic_ids = {n["node_id"] for n in nodes if n.get("learnable")
                       and " ".join(n["name"].casefold().split()) in families}
        inputs = [{"node_id": n["node_id"], "label": n["name"], "anchor_sentence": n["anchor"]["sentence"]}
                  for n in nodes if n.get("teaching_status") == "taught" and n.get("anchor")
                  and (numbered_label(n["name"]) or (None,))[0] in families]
        prompt = load_prompt("a10", "display_name")
        prompt_hash = digest([prompt, DISPLAY_SCHEMA, self.model.model_id, self.generation])
        config = {"algorithm_id": "a10-concept-labels-v2", "upstream_version": upstream.version,
                  "upstream_config_hash": upstream.manifest["config_hash"], "chunks_version": upstream.manifest["config"]["chunks_version"],
                  "label_rule": "document-family-two-distinct-numbers-v1", "prompt_hash": prompt_hash,
                  "model_id": self.model.model_id, "generation": self.generation,
                  "pricing_usd_per_million": PRICING_USD_PER_MILLION, "pricing_source": PRICING_SOURCE}
        config_hash, source_hash = digest(config), digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        checkpoint_id = "concept-labels-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id) or {}
        log = list(checkpoint.get("decision_log", []))
        answers = dict(checkpoint.get("answers", {}))
        metrics = Counter(checkpoint.get("metrics", {}))
        pending = [data for data in inputs if data["node_id"] not in answers]
        if planning:
            reusable = {row["input_hash"] for row in log if row.get("valid")}
            remaining = [data for data in pending if digest([self.model.model_id, prompt_hash, data]) not in reusable]
            return model_plan(remaining, system_prompt=prompt, generation=self.generation, unit="numbered label",
                              checkpoint_id=checkpoint_id, metrics=metrics)
        jobs = []
        for data in pending:
            def validate(value, data=data):
                validate_display_name(value, node_id=data["node_id"], label=data["label"],
                                      sentence=data["anchor_sentence"])
            jobs.append(ModelJob("concept_display_name", self.model, prompt, prompt_hash, data, DISPLAY_SCHEMA, validate))
        values, rows, counts = run_model_jobs(jobs, log, concurrency=self.concurrency)
        log.extend(rows)
        metrics.update(counts)
        answers.update({data["node_id"]: value for data, value in zip(pending, values)})
        if pending:
            self.store.save_checkpoint(doc_id, checkpoint_id, {"answers": answers, "decision_log": log,
                                                             "metrics": dict(metrics)})
        checked = []
        for node in nodes:
            node_id = node["node_id"]
            if node_id in generic_ids:
                checked.append({**node, "teaching_status": "not_subject_matter", "teaching_reason": "từ chung",
                                "teaching_chunk_ids": [], "teaching_order_index": None, "anchor": None})
            elif answers.get(node_id):
                aliases = list(node.get("aliases", []))
                if not any((a.get("name") if isinstance(a, dict) else a) == node["name"] for a in aliases):
                    aliases.append(node["name"])
                checked.append({**node, "display_name": answers[node_id]["display_name"], "aliases": aliases})
            else:
                checked.append(node)
        tokens_in = sum(value for key, value in metrics.items() if key.endswith("_input_tokens"))
        tokens_out = sum(value for key, value in metrics.items() if key.endswith("_output_tokens"))
        cost = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
        previous = upstream.payload.get("cost_summary", {})
        stats = {"label_families": sorted(families), "generic_excluded": len(generic_ids),
                 "numbered_candidates": len(inputs), "display_named": sum(bool(answers.get(d["node_id"])) for d in inputs),
                 **dict(sorted(metrics.items()))}
        payload = {**upstream.payload, "nodes": checked, "concept_display_name_decision_log": log,
                   "cost_summary": {**previous, "concept_labels_usd": cost,
                                    "usd": float(previous.get("usd", 0)) + cost}, "stats": stats}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": upstream.payload["stage"], "stats": stats})
        return artifact, False
