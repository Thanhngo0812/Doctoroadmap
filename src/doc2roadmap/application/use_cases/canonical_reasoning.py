from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations

from doc2roadmap.application.canonical_prompt import (
    canonical_prompts, PARTITION_SCHEMA, DESCRIPTION_SCHEMA, SINGLE_SCHEMA,
)
from doc2roadmap.application.ports.extraction import ModelTransportError
from doc2roadmap.domain.canonical import digest, evidence_missing_name, build_nodes
from doc2roadmap.domain.canonical_decisions import (
    ContradictionError, validate_partition, split_relation_edges, guarded_components,
    validate_description, document_language, vietnamese, split_sentences,
)


class CanonicalReasoning:
    def __init__(self, judge, writer, *, generation=None, language_rule="token-majority-prose-vi20-v2", batch_size=10, counter=None, concurrency=4):
        if batch_size < 1:
            raise ValueError("batch_size phải dương")
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        self.concurrency = concurrency
        self.judge, self.writer = judge, writer
        self.generation = generation or {"temperature": 0., "max_output_tokens": 8192}
        self.language_rule, self.batch_size, self.counter = language_rule, batch_size, counter
        self.prompts = canonical_prompts()

    def config(self):
        return {"judge": self.judge.model_id, "writer": self.writer.model_id,
                "generation": self.generation, "prompts": self.prompts,
                "schemas": [PARTITION_SCHEMA, DESCRIPTION_SCHEMA, SINGLE_SCHEMA],
                "language_rule": self.language_rule, "batch_size": self.batch_size,
                "partition_validation": "consistency-v1",
                "description_validation": "sentence-language-v2",
                "source_budget": 4000, "tokenizer": getattr(self.counter, "identifier", None)}

    def prompt_hash(self, stage, schema):
        model = self.writer if stage in {"describe", "check"} else self.judge
        return digest([self.prompts[stage], schema, model.model_id, self.generation,
                       [self.language_rule, "sentence-language-v2"] if stage in {"describe", "check"} else None])

    def execute(self, initial_nodes, groups, chunks, nominations, previous_log, type_aliases):
        chunks_by_id = {c.chunk_id: c for c in chunks.chunks}
        group_map = {node["node_id"]: group for node, group in zip(initial_nodes, groups, strict=True) if not node["media_id"]}
        node_map = {n["node_id"]: n for n in initial_nodes}
        cache = {row["input_hash"]: row for row in previous_log if row.get("valid") and "input_hash" in row}
        logs = []
        metrics = Counter(
            relation_rejected=0, relation_self_removed=0,
            partition_contradictions=0, contradiction_retried_calls=0,
            contradiction_deferred_calls=0, merge_cache_invalid=0,
            repair_cache_invalid=0,
        )
        deferred, extra_edges, deferred_pairs = set(), [], []
        def call(stage, data, schema, validate):
            counts = Counter()
            model = self.writer if stage in {"describe", "check"} else self.judge
            phash = self.prompt_hash(stage, schema)
            key = digest([model.model_id, phash, data])
            cache_invalid_error = None
            if key in cache:
                row = dict(cache[key], reused=True)
                try:
                    validate(row["output"])
                except (ValueError, TypeError, KeyError, IndexError) as exc:
                    cache_invalid_error = str(exc)
                    counts[stage+"_cache_invalid"] += 1
                else:
                    counts[stage+"_reused"] += 1
                    return row["output"], row, counts
            error, attempts, last_exception = None, [], None
            saw_contradiction = False
            for attempt in range(2):
                counts[stage+"_calls"] += 1
                reply = None
                try:
                    session = model.start_session(self.prompts[stage])
                    prompt = json.dumps(data, ensure_ascii=False, sort_keys=True)
                    if error:
                        prompt += "\nCorrect this validation error: " + str(error)
                    reply = session.ask_json(prompt, response_schema=schema)
                    value = reply.payload
                    validate(value)
                except ModelTransportError:
                    raise
                except ContradictionError as exc:
                    last_exception = exc
                    saw_contradiction = True
                    counts["partition_contradictions"] += 1
                    error = str(exc)
                    attempts.append({"error": error, "raw_text": getattr(reply or exc, "raw_text", None)})
                    continue
                except (ValueError, TypeError, KeyError, IndexError, RuntimeError) as exc:
                    last_exception = exc
                    error = str(exc)
                    attempts.append({"error": error, "raw_text": getattr(reply or exc, "raw_text", None)})
                    continue
                if saw_contradiction:
                    counts["contradiction_retried_calls"] += 1
                row = {"stage": stage, "model": model.model_id, "prompt_hash": phash,
                             "input_hash": key, "input": data, "output": value, "valid": True,
                             "reused": False, "retries": attempt, "attempts": attempts}
                if cache_invalid_error is not None:
                    row["cache_invalid_error"] = cache_invalid_error
                return value, row, counts
            if saw_contradiction:
                counts["contradiction_retried_calls"] += 1
            if isinstance(last_exception, ContradictionError):
                counts["contradiction_deferred_calls"] += 1
            row = {"stage": stage, "model": model.model_id, "prompt_hash": phash,
                   "input_hash": key, "input": data, "valid": False, "error": error, "retries": 1,
                   "attempts": attempts}
            if cache_invalid_error is not None:
                row["cache_invalid_error"] = cache_invalid_error
            counts[stage+"_invalid"] += 1
            return None, row, counts

        def run_calls(jobs):
            # Workers own sessions and counters; only the caller mutates graph/log state.
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                results = list(pool.map(lambda job: call(*job), jobs))
            for _, row, counts in results:
                logs.append(row)
                metrics.update(counts)
            return [value for value, _, _ in results]

        def group_input(id):
            node, members = node_map[id], group_map[id]
            evidence = sorted([(chunks_by_id[e.chunk_id].order_index, e) for member in members for e in member.evidence], key=lambda pair: (pair[0], pair[1].char_start))
            context = {c for member in members if evidence_missing_name(member) for c in member.source_chunk_ids}
            return {"group_id": id, "name": node["name"], "aliases": node["aliases"], "symbols": node["symbols"],
                    "source_fingerprint": digest([[member.candidate_id, [(e.chunk_id, e.quote) for e in member.evidence]] for member in members]),
                    "node_types": [member.node_type for member in members],
                    "section_paths": [chunks_by_id[c].section_path for c in node["source_chunk_ids"]],
                    "evidence": [{"chunk_id": e.chunk_id, "quote": e.quote} for _, e in evidence[:3]],
                    "context": [{"chunk_id": c, "text": chunks_by_id[c].text} for c in sorted(context)]}
        sources = {id: node_map[id]["source_chunk_ids"] for id in group_map}
        same, different = [], []
        clusters = [sorted(cluster, key=lambda id: (node_map[id]["first_mention_index"], id)) for cluster in nominations["clusters"]]
        jobs = [("merge", {"groups": [group_input(id) for id in cluster]}, PARTITION_SCHEMA,
                 lambda value, cluster=cluster: validate_partition(value, {id: sources[id] for id in cluster})) for cluster in clusters]
        for cluster, value in zip(clusters, run_calls(jobs), strict=True):
            if value is None:
                deferred.update(cluster)
                different.extend(combinations(cluster, 2))
                continue
            owner = {id: i for i, node in enumerate(value["nodes"]) for id in node["groups"]}
            deferred.update(d["group_id"] for d in value["deferred"])
            for a, b in combinations(cluster, 2):
                (same if a in owner and b in owner and owner[a] == owner[b] else different).append((a, b))
            kept, rejected = split_relation_edges(value, {id: sources[id] for id in cluster})
            extra_edges.extend(kept)
            logs.extend({"stage": "relation_rejected", "edge": edge} for edge in rejected)
            metrics["relation_rejected"] += len(rejected)
        # A group deferred by cluster judgment remains separate. Repair deferral is pair-scoped.
        base_components, _ = guarded_components(list(group_map), same, [])
        base_owner = {id: component for component in base_components for id in component}
        repairs, seen_repairs = [], set()
        for edge in nominations["cut_edges"]:
            a, b = edge["source"], edge["target"]
            if a in deferred or b in deferred:
                different.append((a, b))
                deferred_pairs.append({"pair": [a, b], "reason": "cluster_deferred"})
                continue
            left, right = base_owner[a], base_owner[b]
            if left == right:
                continue
            combined = sorted(set(left) | set(right), key=lambda id: (node_map[id]["first_mention_index"], id))
            key = tuple(combined)
            if key not in seen_repairs:
                seen_repairs.add(key)
                repairs.append((a, b, combined))
        jobs = [("repair", {"repair_of_cut_edge": True, "groups": [group_input(id) for id in combined]}, PARTITION_SCHEMA,
                 lambda value, combined=combined: validate_partition(value, {id: sources[id] for id in combined}))
                for _, _, combined in repairs]
        for (a, b, combined), value in zip(repairs, run_calls(jobs), strict=True):
            if value is None:
                different.append((a, b))
                deferred_pairs.append({"pair": [a, b], "reason": "repair_invalid"})
                continue
            metrics["cut_pairs_judged"] += 1
            kept, rejected = split_relation_edges(value, {id: sources[id] for id in combined})
            extra_edges.extend(kept)
            logs.extend({"stage": "relation_rejected", "edge": edge} for edge in rejected)
            metrics["relation_rejected"] += len(rejected)
            owner = {id: i for i, node in enumerate(value["nodes"]) for id in node["groups"]}
            if value["deferred"]:
                different.append((a, b))
                deferred_pairs.append({"pair": [a, b], "reason": "; ".join(row["reason"] for row in value["deferred"])})
            elif len({owner[id] for id in combined}) == 1:
                same.append((a, b))
                metrics["repair_merged_pairs"] += 1
            else:
                different.append((a, b))
        components, conflicts = guarded_components(list(group_map), same, different)
        for group in conflicts:
            deferred.update(group)
            logs.append({"stage": "transitive_conflict", "groups": group, "reason": "contradictory decisions"})
        final_groups = [[e for id in component for e in group_map[id]] for component in components]
        final_groups += [group for group in groups if group[0].is_media]
        nodes, tie_log, review = build_nodes(final_groups, chunks.normalized_full_text, type_aliases)
        logs.extend(tie_log)
        mapping = {c: n["node_id"] for n in nodes for c in n["members"]}
        group_to_node = {id: mapping[members[0].candidate_id] for id, members in group_map.items()}
        edges = {}
        for row in extra_edges:
            a, b = group_to_node[row["source"]], group_to_node[row["target"]]
            if a == b:
                metrics["relation_self_removed"] += 1
                continue
            key = (a, b, row["edge_type"])
            if key not in edges:
                edges[key] = {"source": a, "target": b, "edge_type": row["edge_type"],
                              "chunk_ids": row["chunk_ids"], "reason": row["reason"],
                              "proposal": True, "confirmed": False, "evidence": [],
                              "source_refs": [], "origins": ["2a"]}
            else:
                edges[key]["chunk_ids"] = sorted(set(edges[key]["chunk_ids"]) | set(row["chunk_ids"]))
        edges = list(edges.values())
        metrics["relation_edges"] = len(edges)
        metrics["relation_types"] = dict(sorted(Counter(edge["edge_type"] for edge in edges).items()))
        language = document_language(chunks.chunks)
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
            for node, value in zip(selected, run_calls(jobs), strict=True):
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
        for batch, value in zip(batches, run_calls(jobs), strict=True):
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
        metrics["transitive_conflicts"] = len(conflicts)
        metrics["deferred_groups"] = len(deferred)
        metrics["deferred_pairs"] = len(deferred_pairs)
        metrics["merged_group_count"] = len(group_map) - len(components)
        logs.extend({"stage": "deferred_pair", **row} for row in deferred_pairs)
        return nodes, edges, logs, review, sorted(deferred), deferred_pairs, {**metrics, "document_language": language}
