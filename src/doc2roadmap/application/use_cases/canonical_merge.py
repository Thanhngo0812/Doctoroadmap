"""A4 partition and repair; called through CanonicalReasoning.merge."""
from collections import Counter
from itertools import combinations

from doc2roadmap.application.canonical_prompt import PARTITION_SCHEMA
from doc2roadmap.domain.canonical import digest, evidence_missing_name, build_nodes
from doc2roadmap.domain.canonical_decisions import (
    is_contradiction_error, validate_partition, split_relation_edges, guarded_components,
)
from .canonical_repairs import run_repairs
from doc2roadmap.domain.canonical_review import (
    review_constraints, reviewed_components, reserve_node_ids, shared_names, shared_primary_name,
)
from .canonical_merge_verify import verify_merges
from .canonical_a4_rules import DEFAULT_A4_RULES


def merge(self, initial_nodes, groups, chunks, nominations, previous_log, type_aliases):
    chunks_by_id = {c.chunk_id: c for c in chunks.chunks}
    group_map = {node["node_id"]: group for node, group in zip(initial_nodes, groups, strict=True) if not node["media_id"]}
    node_map = {n["node_id"]: n for n in initial_nodes}
    logs = []
    metrics = Counter(
        relation_rejected=0, relation_self_removed=0,
        partition_contradictions=0, contradiction_retried_calls=0,
        contradiction_deferred_calls=0, merge_cache_invalid=0,
        repair_cache_invalid=0,
    )
    deferred, extra_edges, deferred_pairs = set(), [], []

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
    rules = getattr(self, "a4_rules", DEFAULT_A4_RULES)
    metrics["ngram_cut_pairs_skipped"] = 0
    human_same, human_different = (review_constraints(getattr(self, "merge_review", {}),
        getattr(self, "merge_previous", {}), initial_nodes))
    clusters = [sorted(cluster, key=lambda id: (node_map[id]["first_mention_index"], id)) for cluster in nominations["clusters"]]
    jobs = [("merge", {"groups": [group_input(id) for id in cluster]}, PARTITION_SCHEMA,
             lambda value, cluster=cluster: validate_partition(value, {id: sources[id] for id in cluster},
                gop=True, coextensive_identity=rules["coextensive_identity"])) for cluster in clusters]
    for cluster, value in zip(clusters, self.run_calls(jobs, previous_log, logs, metrics), strict=True):
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
        if not rules["ngram_cut_repair_enabled"] and set(edge["channels"]) == {"ngram"}:
            different.append((a, b))
            metrics["ngram_cut_pairs_skipped"] += 1
            logs.append({"stage": "repair_skipped", "pair": [a, b], "reason": "ngram_only_cut"})
            continue
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
    values = run_repairs(self, repairs, group_input, sources, previous_log, logs, metrics)
    for (a, b, combined), value in zip(repairs, values, strict=True):
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
    # Counted from the log, reused rows included, so a rerun from cache reports what the decisions went through.
    partition_rows = [row for row in logs if row.get("stage") in {"merge", "repair", "repair_item"}]
    flags = [[is_contradiction_error(a.get("error")) for a in row.get("attempts", [])] for row in partition_rows]
    metrics["partition_contradictions"] = sum(sum(row_flags) for row_flags in flags)
    metrics["contradiction_retried_calls"] = sum(any(row_flags) for row_flags in flags)
    metrics["contradiction_deferred_calls"] = sum(
        not row["valid"] and bool(row_flags) and row_flags[-1] for row, row_flags in zip(partition_rows, flags))
    same, verification_review = verify_merges(self, same, different, node_map, previous_log, logs, metrics)
    logs.extend({"stage": "merge_review", **row} for row in verification_review)
    names_same = [(a, b) for a, b in combinations(group_map, 2) if shared_primary_name(node_map[a], node_map[b])]
    components, conflicts = reviewed_components(list(group_map), same, different, human_same, human_different,
        forced_same=names_same if rules["normalized_name_merge"] else (),
        conflict_same=names_same if rules["conservative_conflicts"] else ())
    logs.extend({"stage": "human_merge", "left": a, "right": b, "decision": decision}
                for decision, pairs in (("same", human_same), ("different", human_different)) for a, b in pairs)
    deferred.difference_update(key for component in components if len(component) > 1 for key in component)
    for group in conflicts:
        row = {"stage": "transitive_conflict", "groups": group, "reason": "contradictory decisions"}
        retained = [pair for component in components if len(component) > 1 and set(component) <= set(group)
                    for pair in combinations(component, 2)]
        row["retained_pairs"] = [list(pair) for pair in sorted(retained)]
        retained_ids = {key for pair in retained for key in pair}
        deferred.update(set(group) - retained_ids)
        logs.append(row)
    final_groups = [[e for id in component for e in group_map[id]] for component in components]
    final_groups += [group for group in groups if group[0].is_media]
    nodes, tie_log, review = build_nodes(final_groups, chunks.normalized_full_text, type_aliases)
    reserve_node_ids(nodes, getattr(self, "merge_previous", {}))
    logs.extend(tie_log)
    mapping = {c: n["node_id"] for n in nodes for c in n["members"]}
    group_to_node = {id: mapping[members[0].candidate_id] for id, members in group_map.items()}
    deferred_pairs = [row for row in deferred_pairs
                      if group_to_node[row["pair"][0]] != group_to_node[row["pair"][1]]]
    metrics["different_name_merges"] = sum(not shared_names(node_map[a], node_map[b])
        for component in components for a, b in combinations(component, 2))
    reviewed = {frozenset((row["left"], row["right"])) for row in verification_review}
    for component in components:
        for left, right in combinations(component, 2):
            if shared_names(node_map[left], node_map[right]) or frozenset((left, right)) in reviewed:
                continue
            profile = lambda key: {field: node_map[key].get(field, []) if field in {"aliases", "evidence"}
                                   else node_map[key].get(field, "")
                                   for field in ("name", "aliases", "description", "evidence")}
            row = {"left": left, "right": right, "first": profile(left), "second": profile(right),
                   "verification": None, "accepted": True, "human_override": True, "merged": True}
            verification_review.append(row)
            logs.append({"stage": "merge_review", **row})
    for row in verification_review:
        row["merged"] = group_to_node[row["left"]] == group_to_node[row["right"]]
    for row in logs:
        if row.get("stage") == "merge_review":
            row["merged"] = group_to_node[row["left"]] == group_to_node[row["right"]]
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
    metrics["transitive_conflicts"] = len(conflicts)
    metrics["deferred_groups"] = len(deferred)
    metrics["deferred_pairs"] = len(deferred_pairs)
    metrics["merged_group_count"] = len(group_map) - len(components)
    for edge in nominations["edges"]:
        left, right = edge["source"], edge["target"]
        relations = [row for row in extra_edges
                     if {row["source"], row["target"]} == {left, right}]
        logs.append({"stage": "nomination_pair", "left": left, "right": right,
                     "sources": edge["channels"],
                     "verdict": ("same" if group_to_node[left] == group_to_node[right] else
                                 "different" if tuple(sorted((left, right))) in human_different else
                                 "deferred" if left in deferred or right in deferred else "different"),
                     "relations": relations,
                     "verification": next((row["verification"] for row in verification_review
                                            if {row["left"], row["right"]} == {left, right}), None)})
    return nodes, edges, logs, review, sorted(deferred), deferred_pairs, dict(metrics)
