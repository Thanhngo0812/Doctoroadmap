"""Ticket 23: re-name module titles only, reusing final-evaluation v8 titles."""
import argparse
import json
import sys

from chay_a8_full_v3 import DOCS, OUTPUT, FinalStore
from chay_danh_tinh_v3 import MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.llm import GeminiEntityExtractor


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    output = JsonArtifactStore(OUTPUT)
    store = FinalStore(JsonArtifactStore(settings.artifact_dir), output)
    ledger_path = OUTPUT / "llm-ledger.jsonl"
    prior_rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    before = sum(row["usd"] for row in prior_rows)
    summary_path = OUTPUT / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for doc in DOCS:
        upstream, old = store.load_graph(doc, 7), store.load_graph(doc, 8)
        model = (MeteredGemini(
            settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "dry-run-no-key",
            max_usd=before + 0.05, ledger_path=ledger_path, max_output_tokens=128,
            transport=settings.llm_transport, vertex_project=settings.vertex_project,
            vertex_location=settings.vertex_location) if args.allow_spend else
            GeminiEntityExtractor("dry-run-no-key", settings.roadmap_model_id, max_output_tokens=128))
        stage = NameModules(store, SpendGuard(model, allowed=args.allow_spend),
                            concurrency=settings.llm_max_in_flight, reuse_artifact=old)
        plan = stage.plan(doc, upstream=upstream)
        print(doc, json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
        if not args.allow_spend:
            continue
        titled, _ = stage.execute(doc, upstream=upstream)
        for field in ("sequence", "requires_edges", "nodes"):
            if titled.payload[field] != old.payload[field]:
                raise AssertionError(f"{doc}: {field} changed")
        for before_module, after_module in zip(old.payload["modules"], titled.payload["modules"], strict=True):
            if ({key: value for key, value in before_module.items() if key != "title"}
                    != {key: value for key, value in after_module.items() if key != "title"}):
                raise AssertionError(f"{doc}: module data beyond title changed")
        changed = [(before_module["module_id"], before_module["title"], after_module["title"])
                   for before_module, after_module in zip(old.payload["modules"], titled.payload["modules"], strict=True)
                   if before_module["title"] != after_module["title"]]
        expected = {"Chapter 3", "6B", "7C", "Chapter 7", "Chapter 8"} if doc == "doc-2" else set()
        if {before_title for _, before_title, _ in changed} != expected:
            raise AssertionError(f"{doc}: unexpected changed titles")
        print(doc, "v" + str(titled.version), json.dumps(changed, ensure_ascii=False), flush=True)
        summary[doc]["stages"] = str(titled.path)
        output._write(summary_path, summary)
    if args.allow_spend:
        new_rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()][len(prior_rows):]
        print("new_completed_usage_usd", round(sum(row["usd"] for row in new_rows
                                                   if not row.get("reserved")), 6), flush=True)


if __name__ == "__main__":
    main()
