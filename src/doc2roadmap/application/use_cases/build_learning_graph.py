from __future__ import annotations

from doc2roadmap.application.spend_guard import SpendNotAllowed
from doc2roadmap.application.planning import PRICING_SOURCE, PRICING_USD_PER_MILLION, StagePlan


class BuildLearningGraph:
    STAGES = ("clusters", "mentions", "provenance", "edges", "stages")

    def __init__(self, clusters, mentions, provenance, main_edges, secondary_edges, validator, teaching, identity, roadmap):
        self.clusters = clusters
        self.mentions = mentions
        self.provenance = provenance
        self.main_edges = main_edges
        self.secondary_edges = secondary_edges
        self.validator = validator
        self.teaching = teaching
        self.identity = identity
        self.roadmap = roadmap

    def plan(self, doc_id, *, stop_after="stages"):
        if stop_after not in self.STAGES:
            raise ValueError(f"stage không hợp lệ: {stop_after}")
        chain = [("clusters", self.clusters), ("mentions", self.mentions), ("provenance", self.provenance),
                 ("main_edges", self.main_edges), ("secondary_edges", self.secondary_edges),
                 ("validated", self.validator), ("teaching", self.teaching), ("identity", self.identity),
                 ("stages", self.roadmap)]
        upstream, rows = None, []
        for name, use_case in chain:
            if name == "clusters":
                result = use_case.plan(doc_id)
            elif upstream is None:
                result = StagePlan("unknown", remaining_items=None, calls_estimate=None, usd_estimate=None,
                                   note="Phụ thuộc stage trước chưa có artifact đúng cấu hình; không dùng artifact cũ thay thế.")
            else:
                result = use_case.plan(doc_id, upstream=upstream)
            rows.append({"stage": name, **result.to_dict()})
            upstream = result.artifact
            if name == stop_after or (name == "secondary_edges" and stop_after == "edges"):
                break
        return {"doc_id": doc_id, "dry_run": True, "stages": rows,
                "known_usd_estimate": round(sum(row["usd_estimate"] or 0 for row in rows), 6),
                "estimate_complete": all(row["usd_estimate"] is not None for row in rows),
                "pricing_usd_per_million": PRICING_USD_PER_MILLION, "pricing_source": PRICING_SOURCE,
                "note": "Tổng chỉ gồm phần đã biết, không phải ngân sách tối đa; chạy lại --dry-run sau khi có artifact mới."}

    def execute(self, doc_id, *, stop_after="stages"):
        if stop_after not in self.STAGES:
            raise ValueError(f"stage không hợp lệ: {stop_after}")
        self._current = "clusters"
        try:
            return self._execute(doc_id, stop_after)
        except SpendNotAllowed as error:
            # Gắn tên stage để người chạy biết lần chi nào vừa bị chặn.
            raise SpendNotAllowed(self._current) from error

    def _execute(self, doc_id, stop_after):
        artifact, reused = self.clusters.execute(doc_id)
        if stop_after == "clusters":
            return artifact, reused
        self._current = "mentions"
        artifact, current_reused = self.mentions.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        if stop_after == "mentions":
            return artifact, reused
        self._current = "provenance"
        artifact, current_reused = self.provenance.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        if stop_after == "provenance":
            return artifact, reused
        self._current = "main_edges"
        artifact, current_reused = self.main_edges.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        self._current = "secondary_edges"
        artifact, current_reused = self.secondary_edges.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        if stop_after == "edges":
            return artifact, reused
        self._current = "validated"
        artifact, current_reused = self.validator.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        self._current = "teaching"
        artifact, current_reused = self.teaching.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        self._current = "identity"
        artifact, current_reused = self.identity.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        self._current = "stages"
        artifact, current_reused = self.roadmap.execute(doc_id, upstream=artifact)
        return artifact, reused and current_reused
