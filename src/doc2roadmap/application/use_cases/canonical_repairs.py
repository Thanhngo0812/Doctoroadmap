"""Judge each cut-edge repair independently, with the shared partition validator."""
from doc2roadmap.application.canonical_prompt import PARTITION_SCHEMA
from doc2roadmap.domain.canonical_decisions import validate_partition
from .canonical_a4_rules import DEFAULT_A4_RULES


def run_repairs(reasoning, repairs, group_input, sources, previous_log, logs, metrics):
    rules = getattr(reasoning, "a4_rules", DEFAULT_A4_RULES)
    jobs = [("repair", {"repair_of_cut_edge": True, "groups": [group_input(id) for id in combined]}, PARTITION_SCHEMA,
             lambda value, combined=combined: validate_partition(value, {id: sources[id] for id in combined},
                gop=True, coextensive_identity=rules["coextensive_identity"])) for _, _, combined in repairs]
    before = metrics["repair_calls"]
    values = reasoning.run_calls(jobs, previous_log, logs, metrics)
    # Keep the existing zero/fixed counters in artifact payloads for reader compatibility.
    metrics["repair_batch_count"] = len(jobs)
    metrics["repair_batch_call_count"] = metrics["repair_calls"] - before
    metrics["repair_fallback_items"] = 0
    return values
