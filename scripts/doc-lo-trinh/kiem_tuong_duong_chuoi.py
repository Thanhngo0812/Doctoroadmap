"""Zero-cost equivalence check: CLI composition against frozen evaluation artifacts."""
import json
import sys

from doc2roadmap.composition import build_learning_graph
from doc2roadmap.application.use_cases.judge_identity import load_identity_review
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

from chay_a8_full_v3 import FinalStore, OUTPUT


class ChainStore(FinalStore):
    def __init__(self, base, output):
        super().__init__(base, output)
        del self.find_graph

    def find_graph(self, doc_id, source_hash, config_hash):
        self.last_lookup = (source_hash, config_hash)
        return (self.output.find_graph(doc_id, source_hash, config_hash)
                or self.base.find_graph(doc_id, source_hash, config_hash))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    _, settings = build_learning_graph()
    base = JsonArtifactStore(settings.artifact_dir)
    final = JsonArtifactStore(OUTPUT)
    store = ChainStore(base, final)
    failed = False
    for doc in ("doc-6", "doc-1"):
        review_path = settings.artifact_dir / "a8-gold" / f"duyet-danh-tinh-{doc}.json"
        review = load_identity_review(review_path, doc_id=doc) if review_path.exists() else None
        pipeline, _ = build_learning_graph(identity_review=review)
        stages = (("clusters", pipeline.clusters), ("mentions", pipeline.mentions),
                  ("provenance", pipeline.provenance), ("teaching", pipeline.teaching),
                  ("identity", pipeline.identity), ("main_edges", pipeline.main_edges),
                  ("secondary_edges", pipeline.secondary_edges), ("validated", pipeline.validator),
                  ("concept_labels", pipeline.concept_labels), ("stages", pipeline.roadmap),
                  ("module_titles", pipeline.module_titles))
        for _, stage in stages:
            stage.store = store
        identity_version = final.load_graph(doc, 1).manifest["config"]["provenance_version"]
        chain = []
        artifact = base.load_graph(doc, identity_version)
        while True:
            chain.append(artifact)
            if artifact.payload["stage"] == "clusters":
                break
            artifact = base.load_graph(doc, artifact.manifest["upstream_version"])
        chain.reverse()
        expected = chain + [final.load_graph(doc, version) for version in (1, 2, 3, 4, 7, 9)]
        previous = None
        for (name, stage), target in zip(stages, expected, strict=True):
            try:
                plan = stage.plan(doc) if name == "clusters" else stage.plan(doc, upstream=previous)
                match = (plan.status == "reused" and plan.artifact.manifest["source_hash"] == target.manifest["source_hash"]
                         and plan.artifact.manifest["config_hash"] == target.manifest["config_hash"])
                cap = getattr(getattr(stage, "model", None), "_max_output_tokens", None)
                expected_cap = target.manifest.get("config", {}).get("generation", {}).get("max_output_tokens")
                if cap is not None and expected_cap is not None:
                    match &= cap == expected_cap
                detail = {"doc": doc, "stage": name, "target_version": target.version,
                          "status": plan.status, "equivalent": match}
                if cap is not None and expected_cap is not None:
                    detail["transport_max_output_tokens"] = cap
                    detail["expected_max_output_tokens"] = expected_cap
                if not match:
                    detail["target_config_hash"] = target.manifest["config_hash"]
                    detail["actual_config_hash"] = store.last_lookup[1]
                    detail["source_equal"] = store.last_lookup[0] == target.manifest["source_hash"]
            except Exception as error:
                match = False
                detail = {"doc": doc, "stage": name, "target_version": target.version,
                          "equivalent": False, "error": str(error)}
            print(json.dumps(detail, ensure_ascii=False), flush=True)
            failed |= not match
            previous = target
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
