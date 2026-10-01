"""Evaluate v3-09d module names on six existing A10 artifacts; never rerun A8."""
import argparse
import json
from pathlib import Path

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    source = settings.artifact_dir / "v3-05b-a9v10-evaluation"
    root = settings.artifact_dir / "v3-09d-selection-evaluation"
    old_store, output = JsonArtifactStore(source), JsonArtifactStore(root)
    store = EvaluationStore(JsonArtifactStore(settings.artifact_dir), output)
    raw = MeteredGemini(
        settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "dry-run-no-key",
        max_usd=0.0099, ledger_path=root / "spend-vertex.json", max_output_tokens=128,
        transport=settings.llm_transport, vertex_project=settings.vertex_project,
        vertex_location=settings.vertex_location)
    model = SpendGuard(raw, allowed=args.allow_spend)
    previous = json.loads((source / "09c-summary.json").read_text(encoding="utf-8"))
    summary = {}
    for doc_id, old in previous.items():
        upstream = old_store.load_graph(doc_id, int(Path(old["a10_path"]).name[1:]))
        titled = old_store.load_graph(doc_id, int(Path(old["titled_path"]).name[1:]))
        stage = NameModules(store, model, concurrency=1,
                            reuse_artifact=titled)
        plan = stage.plan(doc_id, upstream=upstream)
        row = {"plan": plan.to_dict(), "before": [
            {"module_id": module["module_id"], "title": module["title"]}
            for module in titled.payload["modules"] if module.get("title_source") == "concept"]}
        if args.allow_spend:
            artifact, _ = stage.execute(doc_id, upstream=upstream)
            assert artifact.payload["sequence"] == titled.payload["sequence"]
            assert artifact.payload["requires_edges"] == titled.payload["requires_edges"]
            row["path"] = str(artifact.path)
            row["after"] = [{"module_id": module["module_id"], "title": module["title"],
                             "title_source": module["title_source"]}
                            for module in artifact.payload["modules"]
                            if module.get("title_source") == "model_from_concepts"]
            row["metrics"] = artifact.payload["module_title_metrics"]
        summary[doc_id] = row
        print(doc_id, json.dumps(row, ensure_ascii=True), flush=True)
    if args.allow_spend:
        output._write(root / "09d-summary.json", summary)
        print("Vertex spent USD", sum(row["usd"] for row in raw.ledger if not row.get("reserved")),
              "failed-run reservation USD", sum(row["usd"] for row in raw.ledger if row.get("reserved")),
              flush=True)


if __name__ == "__main__":
    main()
