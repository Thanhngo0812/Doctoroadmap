"""Gop metadata travels with its pinned canonical; v3 cache keys stay unchanged."""


def artifact_chain(artifact):
    return artifact.manifest.get("config", {}).get("upstream_chain",
        artifact.payload.get("upstream_chain", artifact.manifest.get("upstream_chain", "v3")))


def graph_chain_fields(upstream, canonical=None):
    chain = artifact_chain(upstream)
    if canonical is not None and artifact_chain(canonical) != chain:
        raise ValueError("chuỗi graph không khớp canonical đang dùng")
    if chain != "gop":
        return {}
    source = canonical or upstream
    version = canonical.version if canonical is not None else upstream.manifest.get("config", {}).get(
        "canonical_version", upstream.payload.get("canonical_version"))
    anchored = source.payload.get("canonical_has_anchors", source.manifest.get("canonical_has_anchors",
        source.manifest.get("config", {}).get("canonical_has_anchors", False))) is True
    return {"upstream_chain": "gop", "canonical_version": version, "canonical_has_anchors": anchored}
