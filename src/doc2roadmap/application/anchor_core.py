"""C8 anchor rules shared by teaching and canonical, without graph artifacts."""
from __future__ import annotations

from collections import Counter
from typing import Any

from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
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


class AnchorCore:
    def __init__(self, nodes, chunks, hard_mentions):
        """The caller supplies hard mentions and the node's candidate chunk region.

        Teaching uses defining_chunk_ids; canonical supplies source chunks there
        before A5 has selected defining chunks. Neither nodes nor chunks is changed.
        """
        self.nodes = nodes
        self.chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        content_chunks = [c for c in chunks if getattr(c, "role", "noi_dung") == "noi_dung"]
        self.candidates_of, self.outside_of = {}, {}
        for node in nodes:
            if not node.get("learnable"):
                continue
            headings = heading_chunks(node, content_chunks)
            ids = set(node.get("defining_chunk_ids", [])) | hard_mentions.get(node["node_id"], set())
            ids |= {span["chunk_id"] for span in node.get("evidence", []) if isinstance(span, dict) and "chunk_id" in span}
            ids |= symbolic_name_chunks(node, chunks)
            ids.update(headings)
            self.outside_of[node["node_id"]] = sorted({getattr(self.chunk_by_id[c], "role", "noi_dung")
                for c in ids if c in self.chunk_by_id and getattr(self.chunk_by_id[c], "role", "noi_dung") != "noi_dung"})
            candidates = candidate_sentences(node, [self.chunk_by_id[c] for c in ids if c in self.chunk_by_id],
                                             limit=CANDIDATES, headings=headings)
            if not candidates:
                # A6 can omit literal mentions outside its retrieved pairs. Scan only
                # nodes otherwise marked mentioned_only, avoiding a full corpus join.
                new_ids = exact_mentions([node], content_chunks, common_names=())
                ids.update(new_ids)
                candidates = candidate_sentences(node, [self.chunk_by_id[c] for c in ids if c in self.chunk_by_id],
                                                 limit=CANDIDATES, headings=headings)
            self.candidates_of[node["node_id"]] = candidates

    def pending(self, answers):
        return [node for node in sorted(self.nodes, key=lambda n: n["node_id"])
                if node["node_id"] in self.candidates_of and self.candidates_of[node["node_id"]]
                and node["node_id"] not in answers]

    def anchor_input(self, node):
        return _anchor_input(node, self.candidates_of[node["node_id"]], self.chunk_by_id)

    def prior_inputs(self, answers):
        return _prior_inputs(self.nodes, answers)

    def judge(self, model, *, generation, concurrency=4, answers=None, decision_log=(), metrics=None,
              save_checkpoint=None):
        """Return answers, decision log and call/token counts; save each completed batch."""
        answers, decision_log, metrics = dict(answers or {}), list(decision_log), Counter(metrics or {})
        pending = self.pending(answers)
        system_prompt = load_prompt("a10", "anchor")
        prompt_hash = anchor_prompt_hash(model.model_id, generation)
        for start in range(0, len(pending), NODE_BATCH):
            group = pending[start:start + NODE_BATCH]
            jobs = []
            for node in group:
                candidates = self.candidates_of[node["node_id"]]
                data = self.anchor_input(node)

                def validate(value, node_id=node["node_id"], candidates=candidates):
                    validate_anchor_response(value, node_id=node_id, candidates=candidates)

                jobs.append(ModelJob("anchor", model, system_prompt, prompt_hash, data, ANCHOR_SCHEMA, validate))
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=concurrency)
            decision_log.extend(rows)
            metrics.update(counts)
            for node, value in zip(group, values):
                # Hỏng quá lượt sửa: chưa đủ căn cứ để loại, giữ khái niệm.
                answers[node["node_id"]] = value or {"node_id": node["node_id"], "status": "uncertain",
                                                     "reason": "invalid_response"}
            if save_checkpoint is not None:
                save_checkpoint({"answers": answers, "decision_log": decision_log, "metrics": dict(metrics)})
        return answers, decision_log, metrics

    def verify_prior(self, model, answers, *, generation, concurrency=4, verified=None, decision_log=(), metrics=None,
                     save_checkpoint=None):
        """Independently verify prior knowledge, without the first verdict's reason."""
        verified, decision_log, metrics = dict(verified or {}), list(decision_log), Counter(metrics or {})
        prior_prompt = load_prompt("a10", "prior_verify")
        prior_hash = digest([prior_prompt, PRIOR_SCHEMA, model.model_id, generation])
        remaining = [row for row in self.prior_inputs(answers) if row["node_id"] not in verified]
        for start in range(0, len(remaining), NODE_BATCH):
            group = remaining[start:start + NODE_BATCH]
            jobs = []
            for data in group:
                def validate(value, node_id=data["node_id"]):
                    if (not isinstance(value, dict) or value.get("node_id") != node_id
                        or type(value.get("explicit_prior")) is not bool
                        or not isinstance(value.get("reason"), str) or not value["reason"].strip()):
                        raise ValueError("xác minh prior sai node_id, nhãn hoặc thiếu lý do")
                jobs.append(ModelJob("anchor_prior_verify", model, prior_prompt, prior_hash, data, PRIOR_SCHEMA, validate))
            values, rows, counts = run_model_jobs(jobs, decision_log, concurrency=concurrency)
            decision_log.extend(rows)
            metrics.update(counts)
            verified.update({row["node_id"]: value or {"explicit_prior": None, "reason": "invalid_response"}
                             for row, value in zip(group, values)})
            if save_checkpoint is not None:
                save_checkpoint({"answers": verified, "decision_log": decision_log, "metrics": dict(metrics)})
        return verified, decision_log, metrics

    def apply(self, answers, verified):
        """Return node fields and checked verdicts, preserving original provenance."""
        final_answers = {key: dict(value) for key, value in answers.items()}
        for node_id, check in verified.items():
            final_answers[node_id].update(model_status="prior_knowledge", prior_verification=check)
            if check["explicit_prior"] is not True:
                final_answers[node_id]["status"] = "uncertain"
        checked = []
        for node in self.nodes:
            if not node.get("learnable"):
                checked.append(node)
            elif node["node_id"] in answers:
                checked.append({**node, **anchor_fields(final_answers[node["node_id"]], self.candidates_of[node["node_id"]])})
            elif self.outside_of.get(node["node_id"]):
                roles = self.outside_of[node["node_id"]]
                checked.append({**node, **anchor_fields({"status": "mentioned_only"}, []),
                                "mentioned_in": roles[0] if len(roles) == 1 else roles})
            else:
                checked.append({**node, "teaching_status": "unchecked", "teaching_chunk_ids": [],
                                "teaching_order_index": None, "teaching_conflict": False, "anchor": None})
        return checked, final_answers
