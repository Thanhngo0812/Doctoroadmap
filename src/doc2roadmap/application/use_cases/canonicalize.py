from __future__ import annotations

from collections import Counter

from doc2roadmap.application.stage_measurements import measure_stage
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.application.prerequisite_prompt import (
    PRICING_SOURCE,
    PRICING_USD_PER_MILLION,
)
from doc2roadmap.application.use_cases.extract_entities import DocumentExtraction
from doc2roadmap.domain.canonical import (
    digest, name_key, group_names, build_nodes, remap_edges, compare_nodes, redirects, candidate_warnings, alias_kinds_changed,
)
from doc2roadmap.domain.unicode_text import TEXT_RULE_VERSION
from doc2roadmap.domain.canonical_decisions import find_subtype_conflicts
from doc2roadmap.domain.nomination import nomination_graph, unit


class Canonicalize:
    def __init__(self, store, embedding=None, *, graph_config=None, reasoning=None):
        self.store, self.embedding = store, embedding
        self.graph_config = graph_config or {"k": 3, "ngram_threshold": .5, "resolution": 2., "seed": 42, "cap": 9}
        self.reasoning = reasoning
        if reasoning and embedding is None:
            raise ValueError("A4 đầy đủ cần embedding tên")

    @measure_stage
    def execute(self, doc_id, *, a4_gold_coverage=None, gold_sheet_id=None,
                declared_language=None):
        if declared_language not in {None, "vi", "en"}:
            raise ValueError("ngôn ngữ khai báo phải là vi hoặc en")
        if declared_language and not self.reasoning:
            raise ValueError("chỉ khai ngôn ngữ khi chạy A4/A5 đầy đủ")
        source = self.store.load_latest_candidates(doc_id)
        chunks = self.store.load_chunks(doc_id, source.manifest["upstream_version"])
        extraction = DocumentExtraction.from_payload(source.payload)
        if extraction.coverage_incomplete:
            raise ValueError("A4 cần pool ứng viên hoàn chỉnh")
        aliases = self.store.load_type_aliases()
        config = {"algorithm_id": "a4-names-v3", "candidate_version": source.version,
                  "candidate_config_hash": source.manifest["config_hash"], "type_aliases": aliases,
                  "embedding_model_id": self.embedding.embedding_model_id if self.embedding else None,
                  "embedding_text": "candidate.name", "vector_formula": "unit(mean(unit(member_vectors)))",
                  "graph": self.graph_config, "reasoning": self.reasoning.config() if self.reasoning else None,
                  "subtype_rule": "a3-conflict-log-v1",
                  "relation_rule": "open-v1",
                  "stage": "complete" if self.reasoning else "nominations" if self.embedding else "names"}
        if declared_language:
            config["declared_language"] = declared_language
        if alias_kinds_changed(name for e in extraction.entities for name in [e.name, *(a.name for a in e.aliases)]):
            config["name_kind_rule"] = TEXT_RULE_VERSION
        config_hash = digest(config)
        cached = self.store.find_canonical(doc_id, source.manifest["source_hash"], config_hash)
        if cached:
            return cached, True
        previous = None
        try:
            previous = self.store.load_latest_canonical(doc_id)
        except FileNotFoundError:
            pass
        groups = group_names(extraction.entities)
        nodes, log, review = build_nodes(groups, chunks.result.normalized_full_text, aliases)
        for group, node in zip(groups, nodes, strict=True):
            if len(group) > 1:
                log.append({"action": "exact_name", "name_key": name_key(group[0].name),
                            "members": node["members"], "node_id": node["node_id"]})
        nominations = {"edges": [], "clusters": [], "cut_edges": [], "metrics": {}}
        if self.embedding:
            text_groups = {n["node_id"]: group for n, group in zip(nodes, groups, strict=True) if not n["media_id"]}
            names = sorted({e.name for group in text_groups.values() for e in group})
            values = self.embedding.embed([EmbeddingRequest(name, "SEMANTIC_SIMILARITY") for name in names]) if names else []
            if len(values) != len(names):
                raise ValueError("embedding tên trả sai số lượng vector")
            by_name = dict(zip(names, map(unit, values), strict=True))
            vectors = {id: unit([sum(column)/len(group) for column in zip(*(by_name[e.name] for e in group), strict=True)])
                       for id, group in text_groups.items()}
            nominations = nomination_graph(text_groups, vectors, **self.graph_config)
        extra_edges, deferred, deferred_pairs, reasoning_metrics = [], [], [], {}
        if self.reasoning:
            previous_log = [dict(row, origin_version=row.get("origin_version", previous.version))
                            for row in previous.payload["decision_log"]] if previous else []
            nodes, extra_edges, decisions, additional_review, deferred, deferred_pairs, reasoning_metrics = self.reasoning.execute(
                nodes, groups, chunks.result, nominations, previous_log, aliases,
                declared_language=declared_language)
            log.extend(decisions)
            review.extend(additional_review)
        edges, edge_metrics = remap_edges(nodes, extraction.edges)
        subtype_conflicts = find_subtype_conflicts(edges, extra_edges)
        log.extend({"stage": "subtype_conflicts_a3", "edge": edge} for edge in subtype_conflicts)
        a3_triples = {(e["source"], e["target"], e["edge_type"]) for e in edges}
        a3_pairs = {frozenset((e["source"], e["target"])) for e in edges}
        relation_same_as_a3 = relation_same_type_reversed_a3 = 0
        relation_other_type_than_a3 = relation_new_pair = 0
        for extra in extra_edges:
            triple = (extra["source"], extra["target"], extra["edge_type"])
            if triple in a3_triples:
                relation_same_as_a3 += 1
            elif (extra["target"], extra["source"], extra["edge_type"]) in a3_triples:
                relation_same_type_reversed_a3 += 1
            elif frozenset((extra["source"], extra["target"])) in a3_pairs:
                relation_other_type_than_a3 += 1
            else:
                relation_new_pair += 1
            existing = next((e for e in edges if (e["source"], e["target"], e["edge_type"]) == triple), None)
            if existing is None:
                edges.append(extra)
            else:
                existing.setdefault("chunk_ids", [])
                existing["chunk_ids"] = sorted(set(existing["chunk_ids"]) | set(extra["chunk_ids"]))
                existing["origins"] = sorted(set(existing["origins"]) | set(extra["origins"]))
                existing.setdefault("reason", extra["reason"])
        quality = candidate_warnings(extraction.entities, {c.chunk_id: c.parent_section_id for c in chunks.result.chunks})
        old = previous.payload["nodes"] if previous else []
        redirect = redirects(old, nodes, previous.payload.get("redirects") if previous else None)
        metrics = {"candidate_count": len(extraction.entities), "name_group_count": len(groups),
                   "duplicate_description_count": quality["duplicate_description_count"],
                   "duplicate_description_name_count": quality["duplicate_description_name_count"],
                   "evidence_missing_name_count": quality["evidence_missing_name_count"],
                   "text_node_count": sum(not n["media_id"] for n in nodes),
                   "media_node_count": sum(bool(n["media_id"]) for n in nodes), "node_count": len(nodes),
                   "merge_ratio": 1 - len(nodes)/len(extraction.entities) if extraction.entities else 0,
                   "single_chunk_ratio": sum(len(n["source_chunk_ids"]) == 1 for n in nodes)/len(nodes) if nodes else 0,
                   "type_tie_count": sum(row.get("action") == "type_tie" for row in log),
                   "redirect_count": len(redirect), **edge_metrics, **nominations["metrics"], **reasoning_metrics,
                   "final_edge_count": len(edges), "subtype_conflicts_a3": len(subtype_conflicts),
                   "relation_same_as_a3": relation_same_as_a3,
                   "relation_same_type_reversed_a3": relation_same_type_reversed_a3,
                   "relation_other_type_than_a3": relation_other_type_than_a3,
                   "relation_new_pair": relation_new_pair,
                   "deferred_ratio": len(deferred)/len(groups) if groups else 0}
        input_tokens = sum(
            int(value) for key, value in reasoning_metrics.items()
            if key.endswith("_input_tokens")
        )
        output_tokens = sum(
            int(value) for key, value in reasoning_metrics.items()
            if key.endswith("_output_tokens")
        )
        cost_summary = {
            "model_id": self.reasoning.judge.model_id if self.reasoning else None,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "usd": (
                input_tokens * PRICING_USD_PER_MILLION["input"]
                + output_tokens * PRICING_USD_PER_MILLION["output"]
            ) / 1_000_000,
            "pricing_usd_per_million": PRICING_USD_PER_MILLION,
            "pricing_source": PRICING_SOURCE,
        }
        for id in set(previous.payload.get("redirects", {})) & {n["node_id"] for n in nodes} if previous else []:
            log.append({"action": "restore_id", "node_id": id})
        payload = {"schema_version": 1, "doc_id": doc_id, "stage": config["stage"], "nodes": nodes,
                   "members": {n["node_id"]: n["members"] for n in nodes}, "edges": edges,
                   "edge_types": dict(Counter(e["edge_type"] for e in edges)),
                   "decision_log": log, "review": review, "deferred": deferred, "redirects": redirect,
                   "deferred_pairs": deferred_pairs,
                   "nominations": nominations, "stats": metrics, "candidate_quality": quality,
                   "cost_summary": cost_summary,
                   "source_candidates": source.payload["entities"]}
        manifest_fields = {
            "text_rules": TEXT_RULE_VERSION,
            "stats": metrics,
            "jaccard_previous": compare_nodes(old, nodes) if previous else None,
            "cost_summary": cost_summary,
        }
        if self.reasoning:
            manifest_fields["document_language"] = reasoning_metrics["document_language"]
            manifest_fields["language_decision"] = reasoning_metrics["language_decision"]
            manifest_fields["llm_transport"] = getattr(self.reasoning.judge, "transport", "unknown")
        if a4_gold_coverage is not None:
            manifest_fields["a4_gold_coverage"] = a4_gold_coverage
            manifest_fields["gold_sheet_id"] = gold_sheet_id
        artifact = self.store.save_canonical(doc_id, source.manifest["source_hash"], config_hash, config,
            payload, upstream_version=source.version,
            manifest_fields=manifest_fields)
        return artifact, False
