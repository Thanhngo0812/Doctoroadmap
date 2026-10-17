"""Recheck R7 on the existing six-document A9v10 evaluation; never rerun A8."""
import argparse
import json
from pathlib import Path

from evaluation_runtime import EvaluationStore, MeteredGemini
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.config import Settings
from doc2roadmap.domain.module_titles import common_content_title, prepare_module_titles
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-spend", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    root = settings.artifact_dir / "v3-05b-a9v10-evaluation"
    previous = json.loads((root / "end-to-end-summary.json").read_text(encoding="utf-8"))
    output = JsonArtifactStore(root)
    store = EvaluationStore(JsonArtifactStore(settings.artifact_dir), output)
    model = SpendGuard(MeteredGemini(
        settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None,
        max_usd=5, ledger_path=root / "spend.json", max_output_tokens=128,
        transport=settings.llm_transport, vertex_project=settings.vertex_project,
        vertex_location=settings.vertex_location), allowed=args.allow_spend)
    rows = {}
    for doc_id, old in previous.items():
        labels_version = int(Path(old["labels_path"]).name[1:])
        old_roadmap = output.load_graph(doc_id, int(Path(old["a10_path"]).name[1:]))
        stage = BuildRoadmap(store, stage_cap=settings.roadmap_stage_cap)
        plan = stage.plan(doc_id, upstream=output.load_graph(doc_id, labels_version))
        roadmap, _ = stage.execute(doc_id, upstream=output.load_graph(doc_id, labels_version))
        assert roadmap.payload["sequence"] == old_roadmap.payload["sequence"], doc_id
        assert roadmap.payload["requires_edges"] == old_roadmap.payload["requires_edges"], doc_id
        try:
            old_titles = output.load_graph(doc_id, 8)
        except FileNotFoundError:
            old_titles = output.load_graph(doc_id, int(Path(old["titled_path"]).name[1:]))
        titles = NameModules(store, model, concurrency=settings.vertex_concurrency,
                             reuse_artifact=old_titles)
        name_plan = titles.plan(doc_id, upstream=roadmap)
        row = {"a10_path": str(roadmap.path), "module_count": len(roadmap.payload["modules"]),
               "a10_plan": plan.to_dict(), "titles_plan": name_plan.to_dict(),
               "sequence_equal": True, "requires_edges_equal": True}
        if args.allow_spend:
            titled, _ = titles.execute(doc_id, upstream=roadmap)
            row["titled_path"] = str(titled.path)
            row["title_flags"] = titled.payload.get("module_title_flags", [])
            title_chunks = store.load_chunks(doc_id, roadmap.manifest["config"]["title_sections_version"])
            sections = {section.section_id: section for section in title_chunks.result.sections}
            cleaned, _ = prepare_module_titles(list(sections.values()), title_chunks.result.chunks)
            def path(section_id):
                result = []
                while section_id in sections and sections[section_id].level > 0:
                    result.append(section_id)
                    section_id = sections[section_id].parent_section_id
                return result[::-1]
            contained = chapter_base = 0
            for module in titled.payload["modules"]:
                section_ids = module["title_section_ids"]
                paths = [path(section_id) for section_id in section_ids]
                contained += bool(paths and all(len(value) >= 2 and value[:2] == paths[0][:2]
                                                for value in paths))
                base = common_content_title(section_ids, sections, cleaned) if all(section_ids) else ""
                chapter_base += bool(base and any(cleaned.get(section_id) == base
                                                    and sections[section_id].level == 1
                                                    for section_id in paths[0]))
            row["within_level2"] = contained
            row["chapter_base"] = chapter_base
            row["titles"] = [module["title"] for module in titled.payload["modules"]]
            gold = {"doc-1": "doc-1-10-12-vang.json", "doc-2": "doc-2-98-115-vang.json"}
            if doc_id in gold:
                score = score_roadmap_order(titled.path / "graph.json",
                                           [settings.artifact_dir / "a8-gold" / gold[doc_id]])
                row["quality"] = {"q6": score["gold_order"],
                                  "q7": score["target_coverage"]["mean_coverage"],
                                  "q7b": score["target_precision"]["mean_precision"]}
        rows[doc_id] = row
        print(doc_id, json.dumps(row, ensure_ascii=True), flush=True)
    output._write(root / "09c-summary.json", rows)


if __name__ == "__main__":
    main()
