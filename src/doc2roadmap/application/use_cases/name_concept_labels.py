from __future__ import annotations

from collections import Counter

from doc2roadmap.application.stage_measurements import measure_stage, resume_measurements
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.graph_chain import graph_chain_fields
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.anchors import label_families, numbered_label, validate_display_name
from doc2roadmap.domain.canonical import digest, name_key
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter

DISPLAY_SCHEMA = {"type": "object", "properties": {"node_id": {"type": "string"},
    "display_name": {"type": "string"}}, "required": ["node_id", "display_name"]}


def _evidence_text(anchor, label, chunks, labels):
    sentence = anchor["sentence"]
    label_at = sentence.casefold().rfind(label.casefold())
    if label_at < 0 or any(char.isalpha() for char in sentence[label_at + len(label):]):
        return sentence
    chunk = next((value for value in chunks if getattr(value, "chunk_id", None) == anchor.get("chunk_id")), None)
    if chunk is None:
        return sentence
    text = chunk.text
    start = anchor.get("char_start", -1) + label_at
    if text[start:start + len(label)].casefold() != label.casefold():
        start = text.casefold().find(label.casefold(), max(anchor.get("char_start", 0), 0))
    if start < 0:
        return sentence
    spans = UnicodeSentenceSplitter().split(text)
    index = next((i for i, span in enumerate(spans)
                  if span.start <= start < span.end), None)
    if index is None:
        return sentence
    evidence = text[start:spans[min(index + 2, len(spans) - 1)].end]
    next_labels = [evidence.casefold().find(other.casefold(), len(label)) for other in labels if other != label]
    next_labels = [position for position in next_labels if position >= 0]
    return evidence[:min(next_labels)].rstrip() if next_labels else evidence


class NameConceptLabels:
    """Vé 11: đặt tên hiển thị sau danh tính, không phán lại neo hoặc danh tính."""

    def __init__(self, store, model, *, concurrency=4, generation=None):
        self.store, self.model, self.concurrency = store, model, concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 512}

    def plan(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream, planning=True)

    @measure_stage
    def execute(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream)

    def _run(self, doc_id, *, upstream, planning=False):
        if upstream.payload.get("stage") not in {"teaching", "identity", "validated"}:
            raise ValueError("đặt tên nhãn cần artifact teaching/identity/validated")
        chunks_version = upstream.manifest["config"].get("chunks_version")
        if chunks_version is None:
            edges = self.store.load_graph(doc_id, upstream.manifest["config"]["edges_version"])
            chunks_version = edges.manifest["config"]["chunks_version"]
        chunks = self.store.load_role_chunks(doc_id, chunks_version).result.chunks
        nodes = upstream.payload["nodes"]
        families = label_families(nodes, chunks)
        generic_ids = {n["node_id"] for n in nodes if n.get("learnable")
                       and " ".join(n["name"].casefold().split()) in families}
        inputs = [{"node_id": n["node_id"], "label": n["name"],
                   "anchor_sentence": _evidence_text(n["anchor"], n["name"], chunks,
                                                      [other["name"] for other in nodes
                                                       if numbered_label(other["name"])])}
                  for n in nodes if n.get("teaching_status") == "taught" and n.get("anchor")
                  and (numbered_label(n["name"]) or (None,))[0] in families]
        prompt = load_prompt("a10", "display_name")
        prompt_hash = digest([prompt, DISPLAY_SCHEMA, self.model.model_id, self.generation])
        config = {**graph_chain_fields(upstream), "algorithm_id": "a10-concept-labels-v3", "upstream_version": upstream.version,
                  "upstream_config_hash": upstream.manifest["config_hash"], "chunks_version": chunks_version,
                  "label_rule": "document-family-two-distinct-numbers-v1", "prompt_hash": prompt_hash,
                  "model_id": self.model.model_id, "generation": self.generation,
                  "pricing_usd_per_million": PRICING_USD_PER_MILLION, "pricing_source": PRICING_SOURCE}
        config_hash, source_hash = digest(config), digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        checkpoint_id = "concept-labels-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id) or {}
        resume_measurements(checkpoint)
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
        occupied = {}
        for node in nodes:
            for value in [node["name"], node.get("display_name"),
                          *(alias.get("name") if isinstance(alias, dict) else alias for alias in node.get("aliases", []))]:
                if isinstance(value, str) and value.strip():
                    occupied.setdefault(name_key(value), []).append((node["node_id"], value))
        for node_id, answer in answers.items():
            occupied.setdefault(name_key(answer["display_name"]), []).append((node_id, answer["display_name"]))
        for data in pending:
            def validate(value, data=data):
                validate_display_name(value, node_id=data["node_id"], label=data["label"],
                                      sentence=data["anchor_sentence"])
                name = value["display_name"]
                collision = next((existing for other_id, existing in occupied.get(name_key(name), [])
                                  if other_id != data["node_id"]), None)
                if collision:
                    raise ValueError(f"display_name trùng tên khái niệm khác: {collision}")
                occupied.setdefault(name_key(name), []).append((data["node_id"], name))
            jobs.append(ModelJob("concept_display_name", self.model, prompt, prompt_hash, data, DISPLAY_SCHEMA, validate))
        values, rows, counts = run_model_jobs(jobs, log, concurrency=1)
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
        warnings = [{"node_id": data["node_id"], "reason": next(
            (row.get("error", "không có tên hợp lệ") for row in reversed(log)
             if row.get("input", {}).get("node_id") == data["node_id"] and not row.get("valid")),
            "không có tên hợp lệ")}
            for data in inputs if not answers.get(data["node_id"])]
        tokens_in = sum(value for key, value in metrics.items() if key.endswith("_input_tokens"))
        tokens_out = sum(value for key, value in metrics.items() if key.endswith("_output_tokens"))
        cost = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
        previous = upstream.payload.get("cost_summary", {})
        stats = {"label_families": sorted(families), "generic_excluded": len(generic_ids),
                 "numbered_candidates": len(inputs), "display_named": sum(bool(answers.get(d["node_id"])) for d in inputs),
                 "display_name_warnings": len(warnings),
                 **dict(sorted(metrics.items()))}
        payload = {**upstream.payload, "nodes": checked, "concept_display_name_decision_log": log,
                   "concept_display_name_warnings": warnings,
                   "cost_summary": {**previous, "concept_labels_usd": cost,
                                    "usd": float(previous.get("usd", 0)) + cost}, "stats": stats}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": upstream.payload["stage"], "stats": stats,
                                                          "llm_transport": getattr(self.model, "transport", "unknown")})
        return artifact, False
