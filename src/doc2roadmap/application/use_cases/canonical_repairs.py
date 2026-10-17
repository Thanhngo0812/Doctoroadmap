"""Gop repair batches retain each valid partition and retry only invalid items."""
from doc2roadmap.application.canonical_prompt import PARTITION_SCHEMA
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.stage_measurements import measure_phase
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.canonical_decisions import validate_partition
from .canonical_a4_rules import DEFAULT_A4_RULES


BATCH_INSTRUCTION = """
Judge every item independently using the partition rules above. Return one item_id
and partition for each input item. Never merge or relate groups from different items.
Each partition contains nodes, relations and deferred, as for a single judgment.
"""
BATCH_SCHEMA = {"type": "object", "properties": {"items": {"type": "array", "items": {
    "type": "object", "properties": {"item_id": {"type": "string"}, "partition": PARTITION_SCHEMA},
    "required": ["item_id", "partition"]}}}, "required": ["items"]}


def repair_config(size):
    return {"batch_size": size, "schema": BATCH_SCHEMA, "instruction": BATCH_INSTRUCTION,
            "validation": "independent-partition-v1"}


def run_repairs(reasoning, repairs, group_input, sources, previous_log, logs, metrics):
    gop = getattr(reasoning, "upstream_chain", "v3") == "gop"
    rules = getattr(reasoning, "a4_rules", DEFAULT_A4_RULES)
    jobs = [("repair", {"repair_of_cut_edge": True, "groups": [group_input(id) for id in combined]}, PARTITION_SCHEMA,
             lambda value, combined=combined: validate_partition(value, {id: sources[id] for id in combined},
                gop=gop, coextensive_identity=rules["coextensive_identity"]))
            for _, _, combined in repairs]
    if not gop or reasoning.repair_batch_size == 1:
        before = metrics["repair_calls"]
        values = reasoning.run_calls(jobs, previous_log, logs, metrics)
        if getattr(reasoning, "upstream_chain", "v3") == "gop":
            metrics["repair_batch_count"] = len(jobs)
            metrics["repair_batch_call_count"] = metrics["repair_calls"] - before
            metrics["repair_fallback_items"] = 0
        return values
    size, model = reasoning.repair_batch_size, reasoning.judge
    system = reasoning.prompts["repair"] + BATCH_INSTRUCTION
    prompt_hash = digest([system, BATCH_SCHEMA, model.model_id, reasoning.generation])
    batches = [list(range(start, min(start + size, len(jobs)))) for start in range(0, len(jobs), size)]
    def validate_envelope(value):
        if not isinstance(value, dict) or not isinstance(value.get("items"), list):
            raise ValueError("lô phán sửa cần danh sách items")
    batch_jobs = [ModelJob("repair", model, system, prompt_hash,
        {"items": [{"item_id": digest(repairs[index][2]), **jobs[index][1]} for index in indices]},
        BATCH_SCHEMA, validate_envelope) for indices in batches]
    with measure_phase("repair"):
        values, rows, counts = run_model_jobs(batch_jobs, previous_log, concurrency=reasoning.concurrency,
                                              max_attempts=1)
    logs.extend(rows)
    metrics.update(counts)
    metrics["repair_batch_count"] = len(batches)
    metrics["repair_batch_call_count"] = counts["repair_calls"]
    output, invalid, item_logs = [None] * len(jobs), [], {}
    for indices, value in zip(batches, values, strict=True):
        returned = {}
        for row in (value or {}).get("items", []):
            if isinstance(row, dict) and isinstance(row.get("item_id"), str):
                returned.setdefault(row["item_id"], []).append(row)
        for index in indices:
            item_id = digest(repairs[index][2])
            attempts = []
            try:
                matches = returned.get(item_id, [])
                if len(matches) != 1:
                    raise ValueError("mục phán sửa thiếu hoặc lặp item_id")
                partition = matches[0].get("partition")
                jobs[index][3](partition)
            except (ValueError, TypeError, KeyError, IndexError) as error:
                invalid.append(index)
                attempts.append({"error": str(error)})
                partition = None
            else:
                output[index] = partition
            item_logs[index] = {"stage": "repair_item", "item_id": item_id,
                                "input": jobs[index][1], "output": partition,
                                "attempts": attempts, "valid": partition is not None}
    metrics["repair_fallback_items"] = len(invalid)
    retry_values = reasoning.run_calls([jobs[index] for index in invalid], previous_log, logs, metrics)
    for index, value in zip(invalid, retry_values, strict=True):
        output[index] = value
        item_logs[index]["output"] = value
        item_logs[index]["valid"] = value is not None
    logs.extend(item_logs.values())
    return output
