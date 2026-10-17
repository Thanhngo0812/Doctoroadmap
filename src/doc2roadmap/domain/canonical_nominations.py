"""Additional gop nominations from names and optional literal A3 evidence."""
from itertools import combinations

from .anchors import _compact
from .identity import identity_candidates


# Preserve the retired description channel's zero bucket in existing payload metrics.
SOURCES = ("shared_name_or_alias", "normalized_name", "generic_prefix", "initialism",
           "same_evidence", "description_similarity")


def additional_nominations(nodes, *, same_evidence_enabled=False):
    text_nodes = [node for node in nodes if not node.get("media_id")]
    rows = identity_candidates(text_nodes)
    pairs = {(row["left"], row["right"]): set(row["reasons"]) for row in rows}
    if same_evidence_enabled:
        evidence = {node["node_id"]: {_compact(span["quote"]) for span in node.get("evidence", [])
                                      if span.get("quote", "").strip()} for node in text_nodes}
        for left, right in combinations(sorted(evidence), 2):
            if evidence[left] & evidence[right]:
                pairs.setdefault((left, right), set()).add("same_evidence")
    return [{"left": left, "right": right, "reasons": sorted(reasons)}
            for (left, right), reasons in sorted(pairs.items())]
