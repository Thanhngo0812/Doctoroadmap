from __future__ import annotations

from doc2roadmap.application.spend_guard import SpendNotAllowed
from doc2roadmap.application.planning import PRICING_SOURCE, PRICING_USD_PER_MILLION, StagePlan
from doc2roadmap.application.graph_chain import artifact_chain


class BuildLearningGraph:
    STAGES = ("clusters", "mentions", "edges", "stages")

    def __init__(self, clusters, mentions, main_edges, secondary_edges, validator,
                 roadmap, module_titles=None, concept_labels=None):
        self.clusters, self.mentions = clusters, mentions
        self.main_edges, self.secondary_edges, self.validator = main_edges, secondary_edges, validator
        self.roadmap, self.module_titles, self.concept_labels = roadmap, module_titles, concept_labels

    def _chain(self, doc_id, stop_after):
        if stop_after not in self.STAGES:
            raise ValueError(f"stage không hợp lệ hoặc đã gỡ: {stop_after}")
        store = getattr(self.clusters, "store", None)
        selected = artifact_chain(store.load_latest_canonical(doc_id)) if store is not None else "gop"
        if selected != "gop":
            raise ValueError("Đường chạy mới cần canonical gop; chạy lại A4. Artifact v3 cũ vẫn đọc được trực tiếp.")
        chain = [("clusters", self.clusters), ("mentions", self.mentions),
                 ("main_edges", self.main_edges), ("secondary_edges", self.secondary_edges),
                 ("validated", self.validator)]
        if self.concept_labels is not None:
            chain.append(("concept_labels", self.concept_labels))
        chain.append(("stages", self.roadmap))
        if stop_after == "stages" and self.module_titles is not None:
            chain.append(("module_titles", self.module_titles))
        return chain

    def plan(self, doc_id, *, stop_after="stages"):
        chain = self._chain(doc_id, stop_after)
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
            if (name == stop_after and (name != "stages" or self.module_titles is None)
                    or (name == "secondary_edges" and stop_after == "edges")):
                break
        return {"doc_id": doc_id, "dry_run": True, "stages": rows,
                "known_usd_estimate": round(sum(row["usd_estimate"] or 0 for row in rows), 6),
                "estimate_complete": all(row["usd_estimate"] is not None for row in rows),
                "pricing_usd_per_million": PRICING_USD_PER_MILLION, "pricing_source": PRICING_SOURCE,
                "note": "Tổng chỉ gồm phần đã biết, không phải ngân sách tối đa; chạy lại --dry-run sau khi có artifact mới."}

    def execute(self, doc_id, *, stop_after="stages"):
        chain = self._chain(doc_id, stop_after)
        self._current = "clusters"
        try:
            return self._execute(doc_id, stop_after, chain)
        except SpendNotAllowed as error:
            # Gắn tên stage để người chạy biết lần chi nào vừa bị chặn.
            raise SpendNotAllowed(self._current) from error

    def _execute(self, doc_id, stop_after, chain):
        artifact, reused = None, True
        for name, use_case in chain:
            self._current = name
            artifact, current_reused = (use_case.execute(doc_id) if name == "clusters" else
                                       use_case.execute(doc_id, upstream=artifact))
            reused = reused and current_reused
            if (name == stop_after and (name != "stages" or self.module_titles is None)
                    or (name == "secondary_edges" and stop_after == "edges")):
                break
        return artifact, reused
