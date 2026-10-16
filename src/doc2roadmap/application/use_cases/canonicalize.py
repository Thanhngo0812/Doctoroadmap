from __future__ import annotations

from collections import Counter
from copy import copy

from doc2roadmap.application.stage_measurements import measure_stage, measure_phase
from doc2roadmap.application.planning import StagePlan
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
from doc2roadmap.domain.canonical_nominations import SOURCES, additional_nominations
from doc2roadmap.application.prompt_library import load_prompt
from .canonical_anchors import anchor_config, anchor_nodes, prepare_anchors
from .judge_identity import VERIFY_SCHEMA


class Canonicalize:
    def __init__(self, store, embedding=None, *, graph_config=None, reasoning=None,
                 upstream_chain="v3", anchor_batch_mode="a5", anchor_model=None,
                 nomination_config=None, merge_review=None, merge_review_hash=None):
        self.store, self.embedding = store, embedding
        self.graph_config = graph_config or {"k": 3, "ngram_threshold": .5, "resolution": 2., "seed": 42, "cap": 9}
        reasoning = copy(reasoning) if reasoning is not None and upstream_chain == "gop" else reasoning
        self.reasoning = reasoning
        if upstream_chain not in {"v3", "gop"}:
            raise ValueError("upstream_chain phải là v3 hoặc gop")
        if anchor_batch_mode not in {"single", "a5"}:
            raise ValueError("anchor_batch_mode phải là single hoặc a5")
        if upstream_chain == "gop" and (reasoning is None or embedding is None):
            raise ValueError("chuỗi gop cần A4/A5 đầy đủ; không dùng --names-only hoặc --prepare")
        self.upstream_chain, self.anchor_batch_mode = upstream_chain, anchor_batch_mode
        self.anchor_model = anchor_model or (reasoning.judge if reasoning else None)
        if merge_review is not None and upstream_chain != "gop":
            raise ValueError("--merge-review chỉ dùng ở chuỗi gop; v3 dùng roadmap --identity-review")
        self.merge_review = dict(merge_review or {})
        self.merge_review_hash = merge_review_hash or digest(sorted(
            [sorted(pair), decision] for pair, decision in self.merge_review.items()))
        self.nomination_config = {"semantic_top_k": 3, "semantic_min_similarity": .85,
                                  **(nomination_config or {})}
        if upstream_chain == "gop":
            if (type(self.nomination_config["semantic_top_k"]) is not int or
                    self.nomination_config["semantic_top_k"] < 1 or
                    not 0 <= self.nomination_config["semantic_min_similarity"] <= 1):
                raise ValueError("tham số đề cử mô tả không hợp lệ")
            partition = load_prompt("a4", "partition-gop")
            self.reasoning.prompts = {**self.reasoning.prompts, "merge": partition, "repair": partition}
        if reasoning is not None:
            reasoning.upstream_chain = upstream_chain
        if reasoning and embedding is None:
            raise ValueError("A4 đầy đủ cần embedding tên")

    @measure_stage
    def execute(self, doc_id, *, a4_gold_coverage=None, gold_sheet_id=None,
                declared_language=None):
        return self._run(doc_id, a4_gold_coverage=a4_gold_coverage, gold_sheet_id=gold_sheet_id,
                         declared_language=declared_language)

    def plan(self, doc_id, *, declared_language=None, **options):
        return self._run(doc_id, declared_language=declared_language, planning=True)

    def _run(self, doc_id, *, a4_gold_coverage=None, gold_sheet_id=None,
             declared_language=None, planning=False):
        if declared_language not in {None, "vi", "en"}:
            raise ValueError("ngôn ngữ khai báo phải là vi hoặc en")
        if declared_language and not self.reasoning:
            raise ValueError("chỉ khai ngôn ngữ khi chạy A4/A5 đầy đủ")
        source = self.store.load_latest_candidates(doc_id)
        chunks = self.store.load_chunks(doc_id, source.manifest["upstream_version"])
        role_chunks = (self.store.load_role_chunks(doc_id, source.manifest["upstream_version"])
                       if self.upstream_chain == "gop" else None)
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
        if self.upstream_chain == "gop":
            config.update(upstream_chain="gop", anchor_batch_mode=self.anchor_batch_mode,
                          anchor_chunks_version=role_chunks.version, anchors=anchor_config(self.anchor_model, self.anchor_batch_mode))
            config["additional_nominations"] = {"rule": "identity-names+a3-evidence+stored-draft-vectors-v1",
                                                **self.nomination_config}
            config["merge_review_hash"] = self.merge_review_hash
            config["merge_verification"] = digest([load_prompt("a10", "identity_verify"), VERIFY_SCHEMA,
                                                    self.reasoning.judge.model_id, self.reasoning.generation])
        if alias_kinds_changed(name for e in extraction.entities for name in [e.name, *(a.name for a in e.aliases)]):
            config["name_kind_rule"] = TEXT_RULE_VERSION
        config_hash = digest(config)
        cached = self.store.find_canonical(doc_id, source.manifest["source_hash"], config_hash)
        history = None
        if self.upstream_chain == "gop":
            try:
                history = self.store.load_latest_canonical(doc_id)
            except FileNotFoundError:
                pass
            retired = set(history.payload.get("redirects", {})) if history else set()
            if cached and (retired & {node["node_id"] for node in cached.payload["nodes"]}
                           or not retired <= cached.payload.get("redirects", {}).keys()):
                config["retired_ids"] = sorted(retired)
                config_hash = digest(config)
                cached = self.store.find_canonical(doc_id, source.manifest["source_hash"], config_hash)
        if cached:
            if planning:
                return {phase: StagePlan("reused", artifact=cached) for phase in
                        ("embedding", "merge", "repair", "merge_verify", "describe", "check", "anchor", "anchor_prior_verify")}
            return cached, True
        if planning:
            names = {entity.name for entity in extraction.entities if not entity.is_media}
            return {"embedding": StagePlan("run", remaining_items=len(names), unit="name", calls_estimate=None,
                                             usd_estimate=None, note="Embedding tên; số batch và token phụ thuộc adapter."),
                    **{phase: StagePlan("unknown", remaining_items=None, calls_estimate=None, usd_estimate=None,
                                       note="Phụ thuộc kết quả phần trước; chưa biết.") for phase in
                       ("merge", "repair", "merge_verify", "describe", "check", "anchor", "anchor_prior_verify")}}
        previous = history
        if self.upstream_chain != "gop":
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
            with measure_phase("embedding" if self.upstream_chain == "gop" else None):
                values = self.embedding.embed([EmbeddingRequest(name, "SEMANTIC_SIMILARITY") for name in names]) if names else []
            if len(values) != len(names):
                raise ValueError("embedding tên trả sai số lượng vector")
            by_name = dict(zip(names, map(unit, values), strict=True))
            vectors = {id: unit([sum(column)/len(group) for column in zip(*(by_name[e.name] for e in group), strict=True)])
                       for id, group in text_groups.items()}
            additional = (additional_nominations(nodes, text_groups, extraction.candidate_embeddings,
                                                  **self.nomination_config) if self.upstream_chain == "gop" else None)
            nominations = nomination_graph(text_groups, vectors, additional=additional, **self.graph_config)
            if additional is not None:
                for channel in SOURCES:
                    nominations["metrics"]["nomination_channels"].setdefault(channel, 0)
        extra_edges, deferred, deferred_pairs, reasoning_metrics = [], [], [], {}
        if self.reasoning:
            if self.upstream_chain == "gop":
                self.reasoning.merge_previous = previous.payload if previous else {}
                self.reasoning.merge_review = self.merge_review
            previous_log = [dict(row, origin_version=row.get("origin_version", previous.version))
                            for row in previous.payload["decision_log"]] if previous else []
            if self.upstream_chain == "gop":
                nodes, extra_edges, decisions, additional_review, deferred, deferred_pairs, reasoning_metrics = self.reasoning.merge(
                    nodes, groups, chunks.result, nominations, previous_log, aliases)
                core = prepare_anchors(nodes, role_chunks.result.chunks)
                description_log, description_metrics = self.reasoning.describe(
                    nodes, chunks.result, previous_log, declared_language, anchor_core=core,
                    anchor_batch_mode=self.anchor_batch_mode)
                decisions.extend(description_log)
                decisions.extend({"stage": "deferred_pair", **row} for row in deferred_pairs)
                reasoning_metrics.update(description_metrics)
            else:
                nodes, extra_edges, decisions, additional_review, deferred, deferred_pairs, reasoning_metrics = self.reasoning.execute(
                    nodes, groups, chunks.result, nominations, previous_log, aliases,
                    declared_language=declared_language)
            log.extend(decisions)
            review.extend(additional_review)
        anchor_payload = {}
        if self.upstream_chain == "gop":
            nodes, anchor_payload, anchor_metrics = anchor_nodes(
                nodes, role_chunks.result.chunks, self.anchor_model,
                concurrency=self.reasoning.concurrency, previous=previous.payload if previous else None, core=core)
            reasoning_metrics.update(anchor_metrics)
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
        if self.upstream_chain == "gop":
            phases = {}
            for phase in ("merge", "repair", "merge_verify", "describe", "check", "anchor", "anchor_prior_verify"):
                incoming = reasoning_metrics.get(phase + "_input_tokens", 0)
                outgoing = reasoning_metrics.get(phase + "_output_tokens", 0)
                phases[phase] = {"calls": reasoning_metrics.get(phase + "_calls", 0),
                                 "input_tokens": incoming, "output_tokens": outgoing,
                                 "usd": (incoming * PRICING_USD_PER_MILLION["input"] +
                                         outgoing * PRICING_USD_PER_MILLION["output"]) / 1e6}
            cost_summary.update(phases=phases, total={"calls": sum(p["calls"] for p in phases.values()),
                "input_tokens": input_tokens, "output_tokens": output_tokens, "usd": cost_summary["usd"]})
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
        if self.upstream_chain == "gop":
            payload["merge_review"] = [row for row in log if row.get("stage") == "merge_review"]
        manifest_fields = {
            "text_rules": TEXT_RULE_VERSION,
            "stats": metrics,
            "jaccard_previous": compare_nodes(old, nodes) if previous else None,
            "cost_summary": cost_summary,
        }
        if self.upstream_chain == "gop":
            payload.update(upstream_chain="gop", canonical_has_anchors=True, **anchor_payload)
            manifest_fields.update(upstream_chain="gop", canonical_has_anchors=True)
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
