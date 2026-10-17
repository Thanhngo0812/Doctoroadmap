"""Canonical's C8 integration, using A3 sources and literal mentions only."""
from collections import Counter

from doc2roadmap.application.anchor_core import ANCHOR_SCHEMA, AnchorCore, CANDIDATES, PRIOR_SCHEMA, anchor_prompt_hash
from doc2roadmap.application.canonical_prompt import DESCRIPTION_SCHEMA, SINGLE_SCHEMA
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.stage_measurements import measure_phase
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.anchors import validate_anchor_response
from doc2roadmap.domain.mentions import exact_mentions, normalize_mention_chunks


GENERATION = {"temperature": 0.0, "max_output_tokens": 2048}


def a5_schema(stage):
    base = DESCRIPTION_SCHEMA if stage == "describe" else SINGLE_SCHEMA["properties"]["nodes"]["items"]
    item = {**base, "properties": {**base["properties"], "anchor_verdict": ANCHOR_SCHEMA}}
    return item if stage == "describe" else {**SINGLE_SCHEMA, "properties": {
        "nodes": {"type": "array", "items": item}}}


def a5_prompt(prompt):
    return (prompt + "\n\nFor each concept with anchor_candidates, return anchor_verdict using those candidates. "
            "Apply the following rules independently to each concept; omit anchor_verdict when no candidates "
            "are supplied. Description and anchor decisions are independent.\n\n" + load_prompt("a10", "anchor"))


def anchor_config(model, mode="single"):
    config = {"model_id": model.model_id, "generation": GENERATION,
            "prompt_hash": anchor_prompt_hash(model.model_id, GENERATION),
            "prior_verify_prompt_hash": digest([load_prompt("a10", "prior_verify"), PRIOR_SCHEMA,
                                                 model.model_id, GENERATION]),
            "candidates": CANDIDATES,
            "candidate_rule": "source+a3+whole-document-exact+symbol+heading-content-v1"}
    if mode == "a5":
        config["a5_contract"] = digest([a5_prompt(""), a5_schema("describe"), a5_schema("check")])
    return config


def prepare_anchors(nodes, chunks):
    eligible = [node for node in nodes if node.get("learnable") and not node.get("media_id")]
    normalized = normalize_mention_chunks(chunks)
    hard = {node["node_id"]: set(node.get("source_chunk_ids", [])) |
            set(exact_mentions([node], chunks, common_names=(), normalized_chunks=normalized)) for node in eligible}
    core = AnchorCore(eligible, chunks, hard, normalized_mentions=normalized)
    core.a5_answers, core.a5_log, core.a5_metrics, core.a5_seen = {}, [], Counter(), set()
    return core


def collect_a5_anchors(core, selected, value, stage, model, prompt_hash):
    """Keep valid anchor parts even when their description part needs repair."""
    rows = ([value] if stage == "describe" else value.get("nodes", [])) if isinstance(value, dict) else []
    if not isinstance(rows, list):
        rows = []
    for node in selected:
        node_id = node["node_id"]
        if not core.candidates_of.get(node_id) or node_id in core.a5_answers:
            continue
        core.a5_seen.add(node_id)
        matches = rows if stage == "describe" else [row for row in rows
            if isinstance(row, dict) and row.get("node_id") == node_id]
        if len(matches) != 1 or not isinstance(matches[0], dict):
            continue
        verdict = matches[0].get("anchor_verdict")
        data = core.anchor_input(node)
        record = {"stage": "anchor", "origin_stage": stage, "model": model.model_id,
                  "prompt_hash": prompt_hash, "input_hash": digest([model.model_id, prompt_hash, data]),
                  "input": data, "output": verdict, "reused": False, "retries": 0, "attempts": []}
        try:
            validate_anchor_response(verdict, node_id=node_id, candidates=core.candidates_of[node_id])
        except (ValueError, TypeError, KeyError, IndexError) as error:
            core.a5_log.append({**record, "valid": False, "error": str(error)})
        else:
            core.a5_answers[node_id] = verdict
            core.a5_log.append({**record, "valid": True})


def apply_anchors(nodes, core, answers, verified):
    checked, final_answers = core.apply(answers, verified)
    by_id = {node["node_id"]: node for node in checked}
    output = []
    for original in nodes:
        node = by_id.get(original["node_id"], original)
        if node["node_id"] in by_id:
            node["defining_chunk_ids_source"] = list(original.get("defining_chunk_ids", []))
            defining = set(node["defining_chunk_ids_source"]) | set(node.get("teaching_chunk_ids", []))
            node["defining_chunk_ids"] = sorted(defining,
                key=lambda chunk_id: (core.chunk_by_id[chunk_id].order_index, chunk_id))
            if defining:
                node["first_order_index"] = min(core.chunk_by_id[c].order_index for c in defining)
        output.append(node)
    return output, final_answers


def anchor_nodes(nodes, chunks, model, *, concurrency, previous=None, core=None):
    core, previous = core or prepare_anchors(nodes, chunks), previous or {}
    fallback = len(core.pending(core.a5_answers))
    with measure_phase("anchor"):
        answers, log, metrics = core.judge(model, generation=GENERATION, concurrency=concurrency,
            answers=core.a5_answers, decision_log=previous.get("anchor_decision_log", []) + sorted(
                core.a5_log, key=lambda row: row["input"]["node_id"]),
            metrics=core.a5_metrics, batch_size=None)
    if core.a5_metrics or core.a5_log:
        metrics.update(anchor_concepts_in_batch=len(core.a5_answers), anchor_concepts_fallback=fallback)
    with measure_phase("anchor_prior_verify"):
        verified, prior_log, prior_metrics = core.verify_prior(
            model, answers, generation=GENERATION, concurrency=concurrency,
            decision_log=previous.get("anchor_prior_verify_decision_log", []), batch_size=None)
    metrics.update(prior_metrics)
    checked, final_answers = apply_anchors(nodes, core, answers, verified)
    metrics["teaching_status_counts"] = dict(sorted(Counter(
        node["teaching_status"] for node in checked if "teaching_status" in node).items()))
    return checked, {"anchor_log": [{"node_id": key, **value} for key, value in sorted(final_answers.items())],
                     "anchor_decision_log": log, "anchor_prior_verify_decision_log": prior_log}, dict(metrics)
