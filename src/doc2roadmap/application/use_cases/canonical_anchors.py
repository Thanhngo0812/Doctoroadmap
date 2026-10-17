"""Canonical's C8 integration, using A3 sources and literal mentions only."""
from collections import Counter

from doc2roadmap.application.anchor_core import AnchorCore, CANDIDATES, PRIOR_SCHEMA, anchor_prompt_hash
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.stage_measurements import measure_phase
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.mentions import exact_mentions, normalize_mention_chunks


GENERATION = {"temperature": 0.0, "max_output_tokens": 2048}


def anchor_config(model):
    config = {"model_id": model.model_id, "generation": GENERATION,
            "prompt_hash": anchor_prompt_hash(model.model_id, GENERATION),
            "prior_verify_prompt_hash": digest([load_prompt("a10", "prior_verify"), PRIOR_SCHEMA,
                                                 model.model_id, GENERATION]),
            "candidates": CANDIDATES,
            "candidate_rule": "source+a3+whole-document-exact+symbol+heading-content-v1"}
    return config


def prepare_anchors(nodes, chunks):
    eligible = [node for node in nodes if node.get("learnable") and not node.get("media_id")]
    normalized = normalize_mention_chunks(chunks)
    hard = {node["node_id"]: set(node.get("source_chunk_ids", [])) |
            set(exact_mentions([node], chunks, common_names=(), normalized_chunks=normalized)) for node in eligible}
    core = AnchorCore(eligible, chunks, hard, normalized_mentions=normalized)
    return core


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
    with measure_phase("anchor"):
        answers, log, metrics = core.judge(model, generation=GENERATION, concurrency=concurrency,
            decision_log=previous.get("anchor_decision_log", []), batch_size=None)
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
