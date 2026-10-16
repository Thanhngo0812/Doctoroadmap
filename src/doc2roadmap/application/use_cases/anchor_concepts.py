from __future__ import annotations

from collections import Counter

from doc2roadmap.application.stage_measurements import measure_stage, resume_measurements
from doc2roadmap.application.anchor_core import (
    ANCHOR_SCHEMA,
    CANDIDATES,
    NODE_BATCH,
    PRIOR_SCHEMA,
    AnchorCore,
    _anchor_input,
    _prior_inputs,
    anchor_prompt_hash,
)
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.canonical import digest

HARD_CHANNELS = {"exact", "alias", "provenance"}


class AnchorConcepts:
    """Neo định nghĩa — C8 v3 (spec v2, W11–W13). Stage `teaching`, chưa nằm trong chuỗi mặc định cho tới khi qua cổng.

    Ứng viên là câu, gom từ đoạn định nghĩa, đoạn căn cứ A3 và mọi chunk có mention cứng — không chỉ `defining_chunk_ids`,
    vốn hay trỏ vào đoạn dùng. Chỉ ghi thêm trường; provenance gốc giữ nguyên nên danh tính vàng không đổi.
    """

    def __init__(self, store, model, *, concurrency=4, generation=None, reuse_artifact=None):
        self.store = store
        self.model = model
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 2048}
        self.reuse_artifact = reuse_artifact

    @measure_stage
    def execute(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream, planning=False):
        if upstream.payload.get("stage") not in {"validated", "provenance"}:
            raise ValueError("stage teaching cần artifact provenance hoặc validated")
        if upstream.payload["stage"] == "validated":
            edges = self.store.load_graph(doc_id, upstream.manifest["config"]["edges_version"])
            chunks_version = edges.manifest["config"]["chunks_version"]
        else:
            chunks_version = upstream.manifest["config"]["chunks_version"]
        chunks_artifact = self.store.load_role_chunks(doc_id, chunks_version)
        prompt_hash = anchor_prompt_hash(self.model.model_id, self.generation)
        prior_prompt = load_prompt("a10", "prior_verify")
        prior_hash = digest([prior_prompt, PRIOR_SCHEMA, self.model.model_id, self.generation])
        config = {"algorithm_id": "a10-teaching-anchor-v8" if upstream.payload["stage"] == "provenance" else "a10-teaching-anchor-v7",
                  "validated_version": upstream.version,
                  "validated_config_hash": upstream.manifest["config_hash"], "chunks_version": chunks_artifact.version,
                  "model_id": self.model.model_id, "generation": self.generation, "prompt_hash": prompt_hash,
                  "candidates": CANDIDATES, "candidate_rule": "content-only+a3+heading-reserved+position+unicode-sentences-v7",
                  "prior_verify_prompt_hash": prior_hash,
                  "pricing_usd_per_million": PRICING_USD_PER_MILLION,
                  "pricing_source": PRICING_SOURCE}
        if upstream.payload["stage"] == "provenance":
            config.update(upstream_stage="provenance", canonical_version=upstream.manifest["config"].get("canonical_version"))
        config_hash, source_hash = digest(config), digest(upstream.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)
        old_config = {**config, "algorithm_id": "a10-teaching-anchor-v6",
                      "candidate_rule": "content-only+a3+named-heading+position+unicode-sentences-v6"}
        previous = self.store.find_graph(doc_id, source_hash, digest(old_config))
        if previous is None:
            old_config.update(algorithm_id="a10-teaching-anchor-v5",
                              candidate_rule="content-only+whole-document-exact-name+unicode-sentences+nfkc-latex-dash+a3+symbolic-v5")
            previous = self.store.find_graph(doc_id, source_hash, digest(old_config))
        if previous is None:
            old_config.update(algorithm_id="a10-teaching-anchor-v4",
                              candidate_rule="content-only+unicode-sentences+nfkc-latex-dash+a3+symbolic-v4")
            previous = self.store.find_graph(doc_id, source_hash, digest(old_config))
        old = previous or self.reuse_artifact
        old_log = old.payload.get("anchor_decision_log", []) if old else []
        old_prior_log = old.payload.get("anchor_prior_verify_decision_log", []) if old else []

        mentioned = {}
        for chunk_id, rows in upstream.payload.get("mention_map", {}).items():
            for node_id, row in rows.items():
                if HARD_CHANNELS & set(row.get("channels", [])):
                    mentioned.setdefault(node_id, set()).add(chunk_id)

        checkpoint_id = "anchor-" + config_hash
        checkpoint = self.store.load_checkpoint(doc_id, checkpoint_id)
        resumable = checkpoint is not None and checkpoint.get("source_hash") == source_hash
        resume_measurements(checkpoint if resumable else None)
        answers = dict(checkpoint["answers"]) if resumable else {}
        decision_log = list(checkpoint["decision_log"]) if resumable else list(old_log)
        metrics = Counter(checkpoint["metrics"]) if resumable else Counter()

        nodes = upstream.payload["nodes"]
        core = AnchorCore(nodes, chunks_artifact.result.chunks, mentioned)
        candidates_of = core.candidates_of
        if planning:
            pending = core.pending(answers)
            system_prompt = load_prompt("a10", "anchor")
            inputs = [core.anchor_input(node) for node in pending]
            reusable = {row["input_hash"] for row in decision_log if row.get("valid") and "input_hash" in row}
            inputs = [data for data in inputs if digest([self.model.model_id,prompt_hash,data]) not in reusable]
            plan = model_plan(inputs, system_prompt=system_prompt, generation=self.generation, unit="concept",
                              checkpoint_id=checkpoint_id, metrics=metrics)
            known_prior = _prior_inputs(nodes, answers)
            prior_key = "anchor-prior-" + digest([prior_hash, known_prior])
            prior_checkpoint = self.store.load_checkpoint(doc_id, prior_key) or {}
            verify_inputs = [row for row in known_prior if row["node_id"] not in prior_checkpoint.get("answers", {})]
            verify_inputs += [{"node_id": n["node_id"], "concept": {"name": n["name"], "description": n.get("description", "")},
                              "quote": " ".join(c["context"] for c in candidates_of[n["node_id"]])} for n in pending]
            extra = model_plan(verify_inputs, system_prompt=prior_prompt, generation=self.generation, unit="concept")
            plan.calls_estimate += extra.calls_estimate
            plan.usd_estimate = round(plan.usd_estimate + extra.usd_estimate, 6)
            plan.note += " Bao gồm xác minh prior tối đa cho mọi câu trả lời chưa biết; checkpoint xác minh riêng."
            return plan
        answers, decision_log, metrics = core.judge(
            self.model, generation=self.generation, concurrency=self.concurrency,
            answers=answers, decision_log=decision_log, metrics=metrics,
            save_checkpoint=lambda state: self.store.save_checkpoint(
                doc_id, checkpoint_id, {"source_hash": source_hash, **state}))

        prior_inputs = _prior_inputs(nodes, answers)
        prior_key = "anchor-prior-" + digest([prior_hash, prior_inputs])
        prior_checkpoint = self.store.load_checkpoint(doc_id, prior_key) or {}
        resume_measurements(prior_checkpoint)
        verified = dict(prior_checkpoint.get("answers", {}))
        prior_log = list(prior_checkpoint.get("decision_log", old_prior_log))
        prior_metrics = Counter(prior_checkpoint.get("metrics", {}))
        verified, prior_log, prior_metrics = core.verify_prior(
            self.model, answers, generation=self.generation, concurrency=self.concurrency,
            verified=verified, decision_log=prior_log, metrics=prior_metrics,
            save_checkpoint=lambda state: self.store.save_checkpoint(doc_id, prior_key, state))
        metrics.update(prior_metrics)
        checked, final_answers = core.apply(answers, verified)
        tokens_in = sum(v for k, v in metrics.items() if k.endswith("_input_tokens"))
        tokens_out = sum(v for k, v in metrics.items() if k.endswith("_output_tokens"))
        cost = (tokens_in * PRICING_USD_PER_MILLION["input"] + tokens_out * PRICING_USD_PER_MILLION["output"]) / 1e6
        previous = upstream.payload.get("cost_summary", {})
        stats = {"teaching_status_counts": dict(sorted(Counter(n["teaching_status"] for n in checked
                                                                 if "teaching_status" in n).items())),
                 **dict(sorted(metrics.items()))}
        payload = {**upstream.payload, "stage": "teaching", "nodes": checked,
                   "anchor_log": [{"node_id": k, **v} for k, v in sorted(final_answers.items())],
                   "anchor_decision_log": decision_log,
                   "anchor_prior_verify_decision_log": prior_log,
                   "cost_summary": {**previous, "teaching_usd": cost, "usd": float(previous.get("usd", 0.0)) + cost},
                   "stats": stats}
        artifact = self.store.save_graph(doc_id, source_hash, config_hash, config, payload,
                                         upstream_version=upstream.version,
                                         manifest_fields={"stage": "teaching", "stats": stats,
                                                          "llm_transport": getattr(self.model, "transport", "unknown")})
        return artifact, False
