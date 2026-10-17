"""Separately reversible gop A4 rules; v3 never adds these to its config."""
DEFAULT_A4_RULES = {
    "deterministic_clustering": True,
    "same_evidence_enabled": False,
    "ngram_cut_repair_enabled": False,
    "conservative_conflicts": True,
    "normalized_name_merge": True,
    "coextensive_identity": True,
}


def a4_rules_config(rules):
    versions = {
        "deterministic_clustering": "louvain-sorted-integer-ids-v1",
        "same_evidence_enabled": "same-a3-evidence-v1",
        "ngram_cut_repair_enabled": "ngram-only-cut-v1",
        "conservative_conflicts": "retain-normalized-names-v1",
        "normalized_name_merge": "primary-name-identity-v1",
        "coextensive_identity": "coextensive-with-v1",
    }
    return {key: {"enabled": rules[key], "rule": version} for key, version in versions.items()}
