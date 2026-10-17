from __future__ import annotations

import math
from itertools import combinations

import networkx as nx

from .canonical import alias_kind, name_key, unaccented


def unit(vector):
    if not vector or not all(math.isfinite(x) for x in vector):
        raise ValueError("vector tên rỗng hoặc không hữu hạn")
    norm = math.sqrt(sum(x*x for x in vector))
    if not norm:
        raise ValueError("vector tên có độ dài 0")
    return [x / norm for x in vector]


def nomination_graph(groups, vectors, *, k=3, ngram_threshold=.5, resolution=2., seed=42, cap=9,
                     additional=None, deterministic=False):
    if k < 1 or cap < 2 or resolution <= 0 or not 0 < ngram_threshold <= 1:
        raise ValueError("tham số đồ thị A4 không hợp lệ")
    ids = sorted(groups)
    if set(vectors) != set(ids):
        raise ValueError("vector nhóm không đủ")
    if len({len(v) for v in vectors.values()}) > 1:
        raise ValueError("vector nhóm khác số chiều")
    vectors = {key: unit(value) for key, value in vectors.items()}
    similarity = {(a, b): sum(x*y for x, y in zip(vectors[a], vectors[b], strict=True))
                  for a, b in combinations(ids, 2)}
    def cosine(a, b):
        return similarity[tuple(sorted((a, b)))]
    nearest = {a: set(sorted((b for b in ids if b != a), key=lambda b: (-cosine(a, b), b))[:k]) for a in ids}
    def labels(key):
        names = {name_key(e.name) for e in groups[key] if alias_kind(e.name) != "symbol"}
        aliases = {name_key(a.name) for e in groups[key] for a in e.aliases if alias_kind(a.name) != "symbol"}
        return names, aliases
    def grams(key):
        return {text[i:i+3] for e in groups[key] for text in [unaccented(e.name)] for i in range(len(text)-2)}
    labels_by_id, grams_by_id = {i: labels(i) for i in ids}, {i: grams(i) for i in ids}
    added = {tuple(sorted((row["left"], row["right"]))): row["reasons"] for row in additional or []}
    graph, edges = nx.Graph(), []
    for a, b in combinations(ids, 2):
        names_a, alias_a = labels_by_id[a]
        names_b, alias_b = labels_by_id[b]
        channels, weights = [], []
        if alias_a & (names_b | alias_b) or alias_b & names_a:
            channels.append("alias"); weights.append(1.)
        ga, gb = grams_by_id[a], grams_by_id[b]
        if ga | gb and len(ga & gb) / len(ga | gb) >= ngram_threshold:
            channels.append("ngram"); weights.append(max(cosine(a, b), .5))
        if b in nearest[a] and a in nearest[b] and cosine(a, b) > 0:
            channels.append("name"); weights.append(cosine(a, b))
        if (a, b) in added:
            channels.extend(channel for channel in added[a, b] if channel not in channels)
            weights.append(1.)
        if channels:
            weight = max(weights)
            graph.add_edge(a, b, weight=weight)
            edges.append({"source": a, "target": b, "channels": channels, "weight": weight})
    ordered_ids = sorted(graph)
    if deterministic:
        graph = nx.relabel_nodes(graph, {key: index for index, key in enumerate(ordered_ids)})
    def split(component, level):
        if len(component) <= cap:
            return [sorted(component)]
        partitions = nx.community.louvain_communities(graph.subgraph(component), seed=seed, resolution=level)
        if max(map(len, partitions)) == len(component):
            return split(component, level * 2)
        return [part for subset in partitions for part in split(subset, level * 2)]
    initial = nx.community.louvain_communities(graph, seed=seed, resolution=resolution) if graph.number_of_edges() else []
    clusters = [part for component in initial for part in split(component, resolution*2)]
    if deterministic:
        clusters = [sorted(ordered_ids[index] for index in cluster) for cluster in clusters]
    clusters = sorted(clusters, key=lambda c: c[0])
    owner = {item: i for i, cluster in enumerate(clusters) for item in cluster}
    cut = [edge for edge in edges if owner[edge["source"]] != owner[edge["target"]]]
    channels = (("alias", "ngram", "name") if additional is None else
                sorted({"alias", "ngram", "name", *(channel for row in additional for channel in row["reasons"])}))
    return {"edges": edges, "clusters": [c for c in clusters if len(c) > 1], "cut_edges": cut,
            "metrics": {"nomination_edges": len(edges),
                        "nomination_channels": {ch: sum(ch in e["channels"] for e in edges) for ch in channels},
                        "cluster_count": sum(len(c) > 1 for c in clusters),
                        "largest_cluster": max(map(len, clusters), default=0), "cut_edge_count": len(cut)}}
