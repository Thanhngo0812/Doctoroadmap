from __future__ import annotations

from doc2roadmap.application.stage_measurements import measure_stage
from doc2roadmap.application.model_calls import ModelJob, run_model_jobs
from doc2roadmap.application.planning import StagePlan, model_plan
from doc2roadmap.application.prerequisite_prompt import (
    PRICING_SOURCE,
    PRICING_USD_PER_MILLION,
    PROVENANCE_SCHEMA,
    provenance_prompt_hash,
    provenance_system_prompt,
)
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.mentions import build_mention_derivatives, build_mention_map
from doc2roadmap.domain.provenance import (
    quote_is_verbatim,
    select_provenance_candidates,
)


class BuildProvenance:
    def __init__(self, store, model, *, candidate_limit=12, concurrency=4, generation=None):
        if type(concurrency) is not int or concurrency < 1:
            raise ValueError("concurrency phải là số nguyên dương")
        self.store = store
        self.model = model
        self.candidate_limit = candidate_limit
        self.concurrency = concurrency
        self.generation = generation or {"temperature": 0.0, "max_output_tokens": 8192}

    def _mentions(self, doc_id):
        artifact = self.store.load_latest_graph(doc_id)
        while artifact.payload.get("stage") != "mentions":
            if artifact.payload.get("stage") == "clusters":
                raise ValueError("artifact graph không trỏ về stage mentions")
            upstream = artifact.manifest.get("upstream_version")
            if upstream is None:
                raise ValueError("artifact graph không trỏ về stage mentions")
            artifact = self.store.load_graph(doc_id, upstream)
        return artifact

    @staticmethod
    def _validate(value, node_id, candidate_ids):
        if not isinstance(value, dict) or value.get("node_id") != node_id:
            raise ValueError("phán quyết provenance sai node_id")
        if not isinstance(value.get("selections"), list):
            raise ValueError("phán quyết provenance cần selections dạng mảng")
        for selection in value["selections"]:
            if (
                not isinstance(selection, dict)
                or selection.get("chunk_id") not in candidate_ids
                or not isinstance(selection.get("quote"), str)
            ):
                raise ValueError("phán quyết provenance chứa selection không hợp lệ")

    @measure_stage
    def execute(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream)

    def plan(self, doc_id, *, upstream=None):
        return self._run(doc_id, upstream=upstream, planning=True)

    def _run(self, doc_id, *, upstream=None, planning=False):
        mentions = upstream if upstream is not None else self._mentions(doc_id)
        if mentions.payload.get("stage") != "mentions":
            raise ValueError("tầng provenance cần artifact mentions")
        mention_config = mentions.manifest.get("config", {})
        chunks_version = mention_config.get("chunks_version")
        chunks_artifact = (
            self.store.load_chunks(doc_id, chunks_version)
            if chunks_version is not None
            else self.store.load_latest_chunks(doc_id)
        )
        canonical_version = mention_config.get("canonical_version")
        canonical = (
            self.store.load_canonical(doc_id, canonical_version)
            if canonical_version is not None
            else self.store.load_latest_canonical(doc_id)
        )
        prompt_hash = provenance_prompt_hash(self.model.model_id, self.generation)
        config = {
            "algorithm_id": "provenance-refinement-v2",
            "mentions_version": mentions.version,
            "mentions_config_hash": mentions.manifest["config_hash"],
            "chunks_version": chunks_artifact.version,
            "canonical_version": canonical.version,
            "definition_evidence": "a3-or-existing-anchor-verbatim-v1",
            "candidate_channels": ["exact", "dense"],
            "candidate_limit": self.candidate_limit,
            "update_rule": "add-only-v1",
            "model_id": self.model.model_id,
            "generation": self.generation,
            "prompt_hash": prompt_hash,
            "pricing_usd_per_million": PRICING_USD_PER_MILLION,
            "pricing_source": PRICING_SOURCE,
        }
        config_hash = digest(config)
        source_hash = digest(mentions.payload)
        cached = self.store.find_graph(doc_id, source_hash, config_hash)
        if cached is not None:
            return StagePlan("reused", artifact=cached) if planning else (cached, True)

        chunks = chunks_artifact.result.chunks
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        nodes = [dict(node) for node in mentions.payload["nodes"]]
        candidates = {
            node["node_id"]: select_provenance_candidates(
                node,
                chunks,
                mentions.payload["mention_map"],
                limit=self.candidate_limit,
            )
            for node in nodes
            if node.get("learnable")
        }
        inputs = []
        node_by_job = []
        for node in sorted((row for row in nodes if row.get("learnable")), key=lambda row: row["node_id"]):
            rows = candidates[node["node_id"]]
            if not any(row["definition_evidence"] for row in rows):
                continue
            inputs.append({
                "node_id": node["node_id"],
                "name": node.get("name", ""),
                "aliases": [
                    alias.get("name", "") if isinstance(alias, dict) else str(alias)
                    for alias in node.get("aliases", [])
                ],
                "description": node.get("description", ""),
                "candidate_chunks": rows,
            })
            node_by_job.append(node)
        if planning:
            return model_plan(inputs, system_prompt=provenance_system_prompt(), generation=self.generation,
                              unit="concept", metrics=None)
        jobs = [
            ModelJob(
                "provenance",
                self.model,
                provenance_system_prompt(),
                prompt_hash,
                data,
                PROVENANCE_SCHEMA,
                lambda value, node_id=data["node_id"], candidate_ids={row["chunk_id"] for row in data["candidate_chunks"]}: self._validate(value, node_id, candidate_ids),
            )
            for data in inputs
        ]
        values, decision_log, metrics = run_model_jobs(
            jobs,
            [],
            concurrency=self.concurrency,
            max_attempts=1,
        )
        provenance_log = []
        old_first = {node["node_id"]: node.get("first_order_index") for node in nodes}
        for node in nodes:
            node["defining_chunk_ids_source"] = list(node.get("defining_chunk_ids", []))
            node["defining_chunk_ids"] = list(node["defining_chunk_ids_source"])
        for node, value in zip(node_by_job, values, strict=True):
            if value is None:
                provenance_log.append({
                    "node_id": node["node_id"], "chunk_id": None, "channels": [],
                    "definition_signals": [], "quote": None, "verified": False,
                    "status": "invalid_model_response",
                })
                continue
            if not value["selections"]:
                provenance_log.append({
                    "node_id": node["node_id"], "chunk_id": None, "channels": [],
                    "definition_signals": [], "quote": None, "verified": True,
                    "status": "no_selection",
                })
            candidate_by_id = {row["chunk_id"]: row for row in candidates[node["node_id"]]}
            for selection in value["selections"]:
                chunk_id = selection["chunk_id"]
                row = candidate_by_id[chunk_id]
                verified = quote_is_verbatim(selection["quote"], chunk_by_id[chunk_id].text)
                status = "rejected_quote"
                if verified and chunk_id not in node["defining_chunk_ids"]:
                    node["defining_chunk_ids"].append(chunk_id)
                    status = "added"
                elif verified:
                    status = "duplicate_selection"
                provenance_log.append({
                    "node_id": node["node_id"],
                    "chunk_id": chunk_id,
                    "channels": row["channels"],
                    "definition_signals": row["definition_signals"],
                    "quote": selection["quote"],
                    "verified": verified,
                    "status": status,
                })
        for node in nodes:
            node["defining_chunk_ids"] = sorted(
                set(node.get("defining_chunk_ids", [])),
                key=lambda chunk_id: (chunk_by_id[chunk_id].order_index, chunk_id),
            )
            if node["defining_chunk_ids"]:
                node["first_order_index"] = min(
                    chunk_by_id[chunk_id].order_index for chunk_id in node["defining_chunk_ids"]
                )

        exact, dense, dense_scores = {}, {}, {}
        for chunk_id, rows in mentions.payload["mention_map"].items():
            for node_id, row in rows.items():
                channels = set(row.get("channels", []))
                if "exact" in channels:
                    exact.setdefault(chunk_id, set()).add(node_id)
                if "dense" in channels:
                    dense.setdefault(chunk_id, set()).add(node_id)
                    dense_scores[node_id, chunk_id] = float(row.get("dense_z", 0.0))
        mention_map = build_mention_map(nodes, chunks, exact, dense, dense_scores)
        derivatives = build_mention_derivatives(
            nodes,
            chunks,
            mention_map,
            canonical.payload.get("edges", []),
            pair_cluster_top_k=int(mention_config.get("pair_cluster_top_k", 3)),
        )
        changed = sum(old_first.get(node["node_id"]) != node.get("first_order_index") for node in nodes)
        input_tokens = sum(value for key, value in metrics.items() if key.endswith("_input_tokens"))
        output_tokens = sum(value for key, value in metrics.items() if key.endswith("_output_tokens"))
        stats = {
            "concept_considered_count": len(candidates),
            "concept_queried_count": len(jobs),
            "chunk_added_count": sum(row["status"] == "added" for row in provenance_log),
            "rejected_quote_count": sum(row["status"] == "rejected_quote" for row in provenance_log),
            "first_order_changed_node_count": changed,
            "model_calls": metrics.get("provenance_calls", 0),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "usd": input_tokens * PRICING_USD_PER_MILLION["input"] / 1_000_000
            + output_tokens * PRICING_USD_PER_MILLION["output"] / 1_000_000,
        }
        payload = {
            **mentions.payload,
            "stage": "provenance",
            "nodes": nodes,
            "mention_map": mention_map,
            **derivatives,
            "provenance_log": provenance_log,
            "provenance_decision_log": decision_log,
            "stats": stats,
        }
        artifact = self.store.save_graph(
            doc_id,
            source_hash,
            config_hash,
            config,
            payload,
            upstream_version=mentions.version,
            manifest_fields={"stage": "provenance", "stats": stats,
                             "llm_transport": getattr(self.model, "transport", "unknown")},
        )
        return artifact, False
