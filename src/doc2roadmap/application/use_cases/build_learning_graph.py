from __future__ import annotations

from doc2roadmap.application.spend_guard import SpendNotAllowed


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
