"""Independent gop identity verification and human constraints at the A4 boundary."""
from itertools import combinations
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.prompt_library import load_prompt
from doc2roadmap.application.stage_measurements import measure_phase
from doc2roadmap.application.identity_review import VERIFY_SCHEMA
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.canonical_review import shared_names, validate_merge_verification
from doc2roadmap.domain.canonical_decisions import guarded_components


def verify_merges(reasoning, same, different, node_map, previous_log, logs, metrics):
    components, _ = guarded_components(list(node_map), same, [])
    pairs = sorted({tuple(sorted(pair)) for component in components for pair in combinations(component, 2)
                    if not shared_names(node_map[pair[0]], node_map[pair[1]])})
    prompt = load_prompt("a10", "identity_verify")
    prompt_hash = digest([prompt, VERIFY_SCHEMA, reasoning.judge.model_id, reasoning.generation])

    def profile(node_id):
        node = node_map[node_id]
        return {"name": node["name"], "aliases": node["aliases"],
                "description": node.get("description", ""), "evidence": node.get("evidence", [])}

    jobs = [ModelJob("merge_verify", reasoning.judge, prompt, prompt_hash,
                    {"pair_id": digest([left, right])[:24], "first": profile(left), "second": profile(right)},
                    VERIFY_SCHEMA, lambda value, left=left, right=right: validate_merge_verification(
                        value, pair_id=digest([left, right])[:24])) for left, right in pairs]
    with measure_phase("merge_verify"):
        values, rows, counts = run_model_jobs(jobs, previous_log, concurrency=reasoning.concurrency)
    logs.extend(rows)
    metrics.update(counts)
    rejected, review = set(), []
    for (left, right), value in zip(pairs, values, strict=True):
        value = value or {"relation": None, "reason": "invalid_response"}
        accepted = value["relation"] == "dong_nhat"
        if not accepted:
            rejected.add((left, right))
            different.append((left, right))
        review.append({"left": left, "right": right, "first": profile(left), "second": profile(right),
                       "verification": value, "accepted": accepted})
    metrics["merge_verification_rejected"] = len(rejected)
    metrics["different_name_merges"] = len(pairs) - len(rejected)
    return [pair for pair in same if tuple(sorted(pair)) not in rejected], review
