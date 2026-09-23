from __future__ import annotations


class BuildLearningGraph:
    STAGES = ("clusters", "mentions", "provenance", "edges", "stages")

    def __init__(self, clusters, mentions, provenance, main_edges, secondary_edges, validator, teaching, relations,
                 roadmap):
        self.clusters = clusters
        self.mentions = mentions
        self.provenance = provenance
        self.main_edges = main_edges
        self.secondary_edges = secondary_edges
        self.validator = validator
        self.teaching = teaching
        self.relations = relations
        self.roadmap = roadmap

    def execute(self, doc_id, *, stop_after="stages"):
        if stop_after not in self.STAGES:
            raise ValueError(f"stage không hợp lệ: {stop_after}")
        artifact, reused = self.clusters.execute(doc_id)
        if stop_after == "clusters":
            return artifact, reused
        artifact, current_reused = self.mentions.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        if stop_after == "mentions":
            return artifact, reused
        artifact, current_reused = self.provenance.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        if stop_after == "provenance":
            return artifact, reused
        artifact, current_reused = self.main_edges.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        artifact, current_reused = self.secondary_edges.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        if stop_after == "edges":
            return artifact, reused
        artifact, current_reused = self.validator.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        artifact, current_reused = self.teaching.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        artifact, current_reused = self.relations.execute(doc_id, upstream=artifact)
        reused = reused and current_reused
        artifact, current_reused = self.roadmap.execute(doc_id, upstream=artifact)
        return artifact, reused and current_reused
