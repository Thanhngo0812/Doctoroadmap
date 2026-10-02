"""Rebuild A10 and module titles from the six frozen final-evaluation label artifacts."""
import argparse
import json
import sys
from pathlib import Path

from chay_a8_full_v3 import DOCS, OUTPUT, FinalStore
from chay_danh_tinh_v3 import MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def dangling(payload):
    ids = {node["node_id"] for key in ("nodes", "mentioned_nodes", "merged_nodes", "excluded_nodes",
                                         "non_learnable_nodes") for node in payload.get(key, [])}
    return sum(any(edge[side] not in ids for side in ("source", "target"))
               for edge in payload.get("open_edges", []))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    output = JsonArtifactStore(OUTPUT)
    store = FinalStore(JsonArtifactStore(settings.artifact_dir), output)
    summary_path = OUTPUT / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = {}
    for doc in DOCS:
        old = store.load_graph(doc, 6)
        labels = store.load_graph(doc, 4)
        roadmap_stage = BuildRoadmap(store, stage_cap=settings.roadmap_stage_cap)
        plan = roadmap_stage.plan(doc, upstream=labels)
        if not args.allow_spend:
            print(doc, plan.to_dict())
            continue
        roadmap, _ = roadmap_stage.execute(doc, upstream=labels)
        model = SpendGuard(MeteredGemini(
            settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "dry-run-no-key",
            max_usd=50, ledger_path=OUTPUT / "llm-ledger.jsonl", max_output_tokens=128,
            transport=settings.llm_transport, vertex_project=settings.vertex_project,
            vertex_location=settings.vertex_location), allowed=True)
        titled, _ = NameModules(store, model, concurrency=settings.llm_max_in_flight,
                                reuse_artifact=old).execute(doc, upstream=roadmap)
        for field in ("sequence", "requires_edges"):
            if titled.payload[field] != old.payload[field]:
                raise AssertionError(f"{doc}: {field} changed")
        if titled.payload["nodes"] != old.payload["nodes"]:
            raise AssertionError(f"{doc}: learning nodes changed")
        before_modules = [{key: value for key, value in module.items() if key != "mentioned_node_ids"}
                          for module in old.payload["modules"]]
        after_modules = [{key: value for key, value in module.items() if key != "mentioned_node_ids"}
                         for module in titled.payload["modules"]]
        if before_modules != after_modules:
            raise AssertionError(f"{doc}: modules changed beyond mentioned-node placement")
        report[doc] = {"old": old.version, "new": titled.version,
                       "dangling_before": dangling(old.payload), "dangling_after": dangling(titled.payload),
                       "overview_before": len(old.payload.get("overview_mentioned_node_ids", [])),
                       "overview_groups": {key: len(value) for key, value in titled.payload["overview_groups"].items()},
                       "sequence_equal": True, "requires_edges_equal": True}
        if report[doc]["dangling_after"]:
            raise AssertionError(f"{doc}: dangling open edges remain")
        summary[doc]["stages"] = str(titled.path)
        output._write(summary_path, summary)
        print(doc, json.dumps(report[doc], ensure_ascii=False), flush=True)
    if args.allow_spend:
        output._write(OUTPUT / "a10-20-21-report.json", report)


if __name__ == "__main__":
    main()
