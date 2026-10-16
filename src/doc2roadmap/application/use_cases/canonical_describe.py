"""A5 descriptions; called through CanonicalReasoning.describe."""
import json
from collections import Counter

from doc2roadmap.application.canonical_prompt import DESCRIPTION_SCHEMA, SINGLE_SCHEMA
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.stage_measurements import measure_phase
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.canonical_decisions import (
    validate_description, document_language, vietnamese, split_sentences,
)
from .canonical_anchors import a5_prompt, a5_schema, collect_a5_anchors


def describe(self, nodes, chunks, previous_log, declared_language=None, *, anchor_core=None,
             anchor_batch_mode="single"):
    chunks_by_id = {c.chunk_id: c for c in chunks.chunks}
    logs, metrics = [], Counter()
    language = declared_language or document_language(chunks.chunks)
    batched = anchor_core is not None and anchor_batch_mode == "a5"

    def run_calls(jobs, selected_groups):
        if not batched:
            return self.run_calls(jobs, previous_log, logs, metrics)
        calls, origins = [], []
        for (stage, data, schema, validate), selected in zip(jobs, selected_groups, strict=True):
            combined = any(anchor_core.candidates_of.get(node["node_id"])
                           and node["node_id"] not in anchor_core.a5_seen for node in selected)
            if combined:
                prompt, schema = a5_prompt(self.prompts[stage]), a5_schema(stage)
                prompt_hash = digest([prompt, schema, self.writer.model_id, self.generation,
                                      [self.language_rule, "sentence-language-v2"]])

                def validate_parts(value, validate=validate, selected=selected, stage=stage,
                                   prompt_hash=prompt_hash):
                    collect_a5_anchors(anchor_core, selected, value, stage, self.writer, prompt_hash)
                    cleaned = ({key: field for key, field in value.items() if key != "anchor_verdict"}
                               if isinstance(value, dict) else value)
                    validate(cleaned)

                calls.append(ModelJob("anchor", self.writer, prompt, prompt_hash, data, schema, validate_parts))
            else:
                calls.append(ModelJob(stage, self.writer, self.prompts[stage], self.prompt_hash(stage, schema),
                                      data, schema, validate))
            origins.append(stage if combined else None)
        with measure_phase("anchor" if any(origins) else calls[0].stage if calls else None):
            values, rows, counts = run_model_jobs(calls, previous_log, concurrency=self.concurrency)
        for row, origin, selected in zip(rows, origins, selected_groups, strict=True):
            if origin:
                row["origin_stage"] = origin
                node_ids = {node["node_id"] for node in selected}
                for record in anchor_core.a5_log:
                    if record["origin_stage"] == origin and record["input"]["node_id"] in node_ids:
                        record["reused"] = row.get("reused", False)
        logs.extend(rows)
        # Combined A5 calls belong to the anchor phase once, including retries.
        anchor_core.a5_metrics.update({key: value for key, value in counts.items() if key.startswith("anchor_")})
        anchor_core.a5_metrics["anchor_in_a5_calls"] += counts.get("anchor_calls", 0)
        metrics.update({key: value for key, value in counts.items() if not key.startswith("anchor_")})
        return values

    def description_input(node, draft=False):
        source_chunks = sorted((chunks_by_id[c] for c in node["source_chunk_ids"]), key=lambda c: c.order_index)
        tokens = sum(c.token_count for c in source_chunks)
        selected = source_chunks if tokens <= 4000 else source_chunks[:1]
        data = {"node_id": node["node_id"], "name": node["name"], "aliases": node["aliases"],
                "symbols": node["symbols"], "node_type": node["node_type"], "language": language,
                "chunks": [{"chunk_id": c.chunk_id, "text": c.text} for c in selected],
                "evidence": node["evidence"]}
        if tokens > 4000 and selected:
            count = self.counter.count if self.counter else lambda text: len(text.split())
            remaining = max(0, 4000 - count(json.dumps(data["evidence"], ensure_ascii=False)))
            text = data["chunks"][0]["text"]
            low, high = 0, len(text)
            while low < high:
                middle = (low + high + 1)//2
                if count(text[:middle]) <= remaining:
                    low = middle
                else:
                    high = middle - 1
            data["chunks"][0]["text"] = text[:low]
            data["source_truncated"] = low < len(text) or len(selected) < len(source_chunks)
        if draft:
            data["draft"] = node["description"]
        if batched and anchor_core.candidates_of.get(node["node_id"]) and node["node_id"] not in anchor_core.a5_seen:
            data["anchor_candidates"] = anchor_core.anchor_input(node)["candidates"]
        return data
    def apply_description(node, value):
        if value is None:
            node["description_status"] = "draft_fallback_invalid"
            metrics["a5_fallback"] += 1
            return
        node["description"] = " ".join(s["text"].strip() + " " + " ".join(f"[{id}]" for id in s["chunk_ids"]) for s in value["sentences"])
        node["description_sentences"] = value["sentences"]
        node["defining_chunk_ids"] = value["defining_chunk_ids"]
        node["nghi_gop_nham"] = value["nghi_gop_nham"]
        node["description_reason"] = value["reason"]
        node["description_status"] = "verified_citations"
        if value["defining_chunk_ids"]:
            node["first_order_index"] = min(chunks_by_id[c].order_index for c in value["defining_chunk_ids"])
        metrics["nghi_gop_nham"] += value["nghi_gop_nham"]
    def describe_many(selected):
        jobs = [("describe", description_input(node), DESCRIPTION_SCHEMA,
                 lambda value, node=node: validate_description(value, node["source_chunk_ids"], language)) for node in selected]
        for node, value in zip(selected, run_calls(jobs, [[node] for node in selected]), strict=True):
            apply_description(node, value)
    multiple = [n for n in nodes if not n["media_id"] and len(n["members"]) > 1]
    describe_many(multiple)
    metrics["a5_synthesized"] += len(multiple)
    singles = [n for n in nodes if not n["media_id"] and len(n["members"]) == 1]
    batches = [singles[start:start+self.batch_size] for start in range(0, len(singles), self.batch_size)]
    jobs = []
    for batch in batches:
        def validate_check(value, batch=batch):
            rows = value["nodes"]
            if len(rows) != len(batch) or {r["node_id"] for r in rows} != {n["node_id"] for n in batch}:
                raise ValueError("lô kiểm thiếu/thừa/lặp node")
            if any(not isinstance(r["keep"], bool) or not isinstance(r["reason"], str) for r in rows):
                raise ValueError("keep phải boolean")
        jobs.append(("check", {"nodes": [description_input(n, True) for n in batch]}, SINGLE_SCHEMA, validate_check))
    rewrites = []
    for batch, value in zip(batches, run_calls(jobs, batches), strict=True):
        if value is None:
            for node in batch:
                apply_description(node, None)
            continue
        decisions = {r["node_id"]: r for r in value["nodes"]}
        for node in batch:
            correct_language = ("vi" if vietnamese(node["description"] or "") else "en") == language
            if decisions[node["node_id"]]["keep"] and correct_language and node["description"] and node["source_chunk_ids"]:
                sentences = split_sentences(node["description"])
                kept = {"sentences": [{"text": s, "chunk_ids": node["source_chunk_ids"]} for s in sentences],
                        "defining_chunk_ids": node["source_chunk_ids"], "nghi_gop_nham": False, "reason": decisions[node["node_id"]]["reason"]}
                try:
                    validate_description(kept, node["source_chunk_ids"], language)
                except ValueError:
                    rewrites.append(node)
                    metrics["a5_rewritten_invalid_draft"] += 1
                else:
                    apply_description(node, kept); metrics["a5_kept"] += 1
            else:
                rewrites.append(node)
                metrics["a5_rewritten_language" if not correct_language else "a5_rewritten_unsupported"] += 1
    describe_many(rewrites)
    return logs, {**metrics, "document_language": language,
                  "language_decision": "declared" if declared_language else "detected"}
