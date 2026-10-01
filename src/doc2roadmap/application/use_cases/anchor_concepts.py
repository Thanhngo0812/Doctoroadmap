from __future__ import annotations

from collections import Counter
from typing import Any

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prerequisite_prompt import PRICING_SOURCE, PRICING_USD_PER_MILLION
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.domain.anchors import (
    STATUSES,
    anchor_fields,
    candidate_sentences,
    heading_chunks,
    symbolic_name_chunks,
    validate_anchor_response,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.mentions import exact_mentions

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
PRIOR_SCHEMA = {"type": "object", "properties": {"node_id": {"type": "string"},
    "explicit_prior": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["node_id", "explicit_prior", "reason"]}


def anchor_prompt_hash(model_id, generation):
    return digest([load_prompt("a10", "anchor"), ANCHOR_SCHEMA, model_id, generation])


def _prior_inputs(nodes, answers):
    return [{"node_id": n["node_id"], "concept": {"name": n["name"], "description": n.get("description", "")},
             "quote": answers[n["node_id"]]["quote"]} for n in nodes
            if answers.get(n["node_id"], {}).get("status") == "prior_knowledge"]


def _anchor_input(node, candidates, chunk_by_id):
    return {"node_id": node["node_id"],
            "concept": {"name": node["name"], "description": node.get("description", ""),
                        "aliases": sorted({str(a["name"] if isinstance(a, dict) else a)
                                           for a in node.get("aliases", [])})},
            "candidates": [{"cand_id": c["cand_id"], "chunk_id": c["chunk_id"],
                            "section_path": list(getattr(chunk_by_id[c["chunk_id"]], "section_path", []) or []),
                            "sentence": c["sentence"], "context": c["context"]} for c in candidates]}


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
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks_artifact.result.chunks}
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
        answers = dict(checkpoint["answers"]) if resumable else {}
        decision_log = list(checkpoint["decision_log"]) if resumable else list(old_log)
        metrics = Counter(checkpoint["metrics"]) if resumable else Counter()

        nodes = upstream.payload["nodes"]
        content_chunks = [c for c in chunks_artifact.result.chunks if getattr(c, "role", "noi_dung") == "noi_dung"]
        candidates_of = {}
        outside_of = {}
        for node in nodes:
            if not node.get("learnable"):
                continue
            headings = heading_chunks(node, content_chunks)
            ids = set(node.get("defining_chunk_ids", [])) | mentioned.get(node["node_id"], set())
            ids |= {span["chunk_id"] for span in node.get("evidence", []) if isinstance(span, dict) and "chunk_id" in span}
            ids |= symbolic_name_chunks(node, chunks_artifact.result.chunks)
            ids.update(headings)
            outside_of[node["node_id"]] = sorted({getattr(chunk_by_id[c], "role", "noi_dung")
                for c in ids if c in chunk_by_id and getattr(chunk_by_id[c], "role", "noi_dung") != "noi_dung"})
            candidates = candidate_sentences(node,[chunk_by_id[c] for c in ids if c in chunk_by_id],
                                             limit=CANDIDATES, headings=headings)
            if not candidates:
                # A6 can omit literal mentions outside its retrieved pairs. Scan only
                # nodes otherwise marked mentioned_only, avoiding a full corpus join.
                new_ids = exact_mentions([node],content_chunks,common_names=())
                ids.update(new_ids)
                candidates = candidate_sentences(node,[chunk_by_id[c] for c in ids if c in chunk_by_id],
                                                 limit=CANDIDATES, headings=headings)
            candidates_of[node["node_id"]] = candidates
        pending = [node for node in sorted(nodes, key=lambda n: n["node_id"])
                   if node["node_id"] in candidates_of and candidates_of[node["node_id"]]
                   and node["node_id"] not in answers]
        system_prompt = load_prompt("a10", "anchor")
        if planning:
            inputs = [_anchor_input(node,candidates_of[node["node_id"]],chunk_by_id) for node in pending]
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
        for start in range(0, len(pending), NODE_BATCH):
            group = pending[start:start + NODE_BATCH]
            jobs = []
            for node in group:
                candidates = candidates_of[node["node_id"]]
                data = _anchor_input(node,candidates,chunk_by_id)

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

        prior_inputs = _prior_inputs(nodes, answers)
        prior_key = "anchor-prior-" + digest([prior_hash, prior_inputs])
        prior_checkpoint = self.store.load_checkpoint(doc_id, prior_key) or {}
        verified = dict(prior_checkpoint.get("answers", {}))
        prior_log = list(prior_checkpoint.get("decision_log", old_prior_log))
        prior_metrics = Counter(prior_checkpoint.get("metrics", {}))
        remaining = [row for row in prior_inputs if row["node_id"] not in verified]
        for start in range(0, len(remaining), NODE_BATCH):
            group = remaining[start:start + NODE_BATCH]
            jobs = []
            for data in group:
                def validate(value, node_id=data["node_id"]):
                    if (not isinstance(value, dict) or value.get("node_id") != node_id
                        or type(value.get("explicit_prior")) is not bool
                        or not isinstance(value.get("reason"), str) or not value["reason"].strip()):
                        raise ValueError("xác minh prior sai node_id, nhãn hoặc thiếu lý do")
                jobs.append(ModelJob("anchor_prior_verify", self.model, prior_prompt, prior_hash, data, PRIOR_SCHEMA, validate))
            values, rows, counts = run_model_jobs(jobs, prior_log, concurrency=self.concurrency)
            prior_log.extend(rows)
            prior_metrics.update(counts)
            verified.update({row["node_id"]: value or {"explicit_prior": None, "reason": "invalid_response"}
                             for row, value in zip(group, values)})
            self.store.save_checkpoint(doc_id, prior_key, {"answers": verified, "decision_log": prior_log,
                                                          "metrics": dict(prior_metrics)})
        metrics.update(prior_metrics)
        final_answers = {key: dict(value) for key, value in answers.items()}
        for node_id, check in verified.items():
            final_answers[node_id].update(model_status="prior_knowledge", prior_verification=check)
            if check["explicit_prior"] is not True:
                final_answers[node_id]["status"] = "uncertain"
        checked = []
        for node in nodes:
            if not node.get("learnable"):
                checked.append(node)
            elif node["node_id"] in answers:
                checked.append({**node, **anchor_fields(final_answers[node["node_id"]], candidates_of[node["node_id"]])})
            elif outside_of.get(node["node_id"]):
                roles = outside_of[node["node_id"]]
                checked.append({**node, **anchor_fields({"status": "mentioned_only"}, []),
                                "mentioned_in": roles[0] if len(roles) == 1 else roles})
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
