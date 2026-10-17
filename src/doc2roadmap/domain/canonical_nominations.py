"""Additional gop nominations, using A3 vectors without embedding or merging."""
from itertools import combinations

from .anchors import _compact
from .identity import identity_candidates
from .nomination import unit


SOURCES = ("shared_name_or_alias", "normalized_name", "generic_prefix", "initialism",
           "same_evidence", "description_similarity")


def additional_nominations(nodes, groups, embeddings, *, semantic_top_k=3, semantic_min_similarity=.85,
                           same_evidence_enabled=False):
    text_nodes = [node for node in nodes if not node.get("media_id")]
    vectors = {}
    for node in text_nodes:
        members = groups[node["node_id"]]
        if not all(member.candidate_id in embeddings for member in members):
            continue
        values = [unit(embeddings[member.candidate_id]) for member in members]
        vectors[node["node_id"]] = unit([sum(column) / len(values) for column in zip(*values, strict=True)])
    rows = identity_candidates(text_nodes, vectors=vectors, semantic_top_k=semantic_top_k,
                               semantic_min_similarity=semantic_min_similarity)
    pairs = {(row["left"], row["right"]): set(row["reasons"]) for row in rows}
    if same_evidence_enabled:
        evidence = {node["node_id"]: {_compact(span["quote"]) for span in node.get("evidence", [])
                                      if span.get("quote", "").strip()} for node in text_nodes}
        for left, right in combinations(sorted(evidence), 2):
            if evidence[left] & evidence[right]:
                pairs.setdefault((left, right), set()).add("same_evidence")
    return [{"left": left, "right": right, "reasons": sorted(reasons)}
            for (left, right), reasons in sorted(pairs.items())]
