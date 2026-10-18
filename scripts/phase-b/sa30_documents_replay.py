from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.llm.phase_b import ReplayToolModel


LIVE = ROOT / "tmp/phaseb-live-group2-v2.json"
BASE = ROOT / "artifacts/phase_b/recordings/acceptance-group2-v2"
MERGED_DIR = ROOT / "tmp/phaseb-sa30-recordings"
SAMPLE_DIR = ROOT / "tmp/phaseb-sa30-documents"
OUTPUT = ROOT / "tmp/phaseb-sa30-documents-replay.json"
OWNER = "acceptance-group2"


def _merge_document_fixture() -> Path:
    paths = [BASE / "document.json", BASE / "resume" / "document.json"]
    fixtures = [json.loads(path.read_text(encoding="utf-8")) for path in paths if path.is_file()]
    if not fixtures:
        raise FileNotFoundError("no saved Group 2 document replay fixtures")
    first = fixtures[0]
    identity = (first.get("prompt_hash"), first.get("model_id"), first.get("fixture_version"))
    if any((row.get("prompt_hash"), row.get("model_id"), row.get("fixture_version")) != identity
           for row in fixtures[1:]):
        raise ValueError("incompatible saved document fixtures")
    first["sessions"] = [session for row in fixtures for session in row.get("sessions", [])]
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    path = MERGED_DIR / "document.json"
    path.write_text(json.dumps(first, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _document_search(operation: dict):
    searches = operation.get("captured_searches", [])
    if len(searches) != 1:
        raise ValueError(f"expected one captured document search for {operation['doc_id']}")
    row = searches[0]

    class StaticSearch:
        def search(self, query, **kwargs):
            if query != row["query"]:
                raise ValueError("document replay search query mismatch")
            return row["result"]

    return StaticSearch()


def _payload(model: ReplayToolModel, prior_sessions: set[int]) -> dict:
    new_sessions = model._reserved - prior_sessions
    if len(new_sessions) != 1:
        raise AssertionError(f"expected one consumed document session; got {len(new_sessions)}")
    session = model._sessions[next(iter(new_sessions))]
    return session["calls"][0]["reply"]["payload"]


def main() -> None:
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    fixture = _merge_document_fixture()
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ROOT / "artifacts"),
                            b_settings=BSettings(), allow_spend=False, mode="offline")
    recorded_settings = asdict(runtime.b_settings)
    for key in ("lecture_duplicate_jaccard_threshold", "lecture_validator_version",
                "connector_sentence_max_chars", "naming_common_chunk_ratio"):
        recorded_settings.pop(key, None)
    model = ReplayToolModel(fixture, prompt_hash=context_hash(["phase-b-v1", "document", recorded_settings]))
    store = InMemoryPhaseBStore()
    operations = [row for row in live["operations"] if row["kind"] == "document"]
    if len(operations) != 6:
        raise RuntimeError(f"expected six Group 2 document operations; found {len(operations)}")
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for operation in operations:
        graph = runtime.graph(operation["doc_id"], operation["graph_version"])
        request = f"Tạo bản ôn tập ngắn về {operation['concept']}, mỗi ý có trích dẫn."
        before_sessions = set(model._reserved)
        result = DocumentUseCase(model, store, settings=runtime.b_settings,
                                 retriever=_document_search(operation)).create(
            operation["doc_id"], str(operation["graph_version"]), graph, request,
            operation["node_id"], owner=OWNER, allow_spend=True)
        payload = _payload(model, before_sessions)
        stem = f"{operation['doc_id']}-document"
        (SAMPLE_DIR / f"{stem}.md").write_text(str(result.get("markdown", "")), encoding="utf-8")
        (SAMPLE_DIR / f"{stem}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        results.append({
            "doc_id": operation["doc_id"], "graph_version": operation["graph_version"],
            "concept": operation["concept"], "before_status": operation["result"].get("status"),
            "after_status": result.get("status"), "result": result,
            "raw_model_citation_count": len(payload.get("citations", [])),
            "repaired_citation_count": sum(
                row.get("quote") not in {item.get("quote") for item in payload.get("citations", [])
                         if item.get("label") == row.get("label")}
                for row in result.get("citations", [])),
        })
    ledger = store.usage_rows()
    output = {"source": str(LIVE.relative_to(ROOT)), "fixture": str(fixture.relative_to(ROOT)),
              "results": results, "usage_rows": ledger,
              "total_replay_cost_usd": sum(float(row.get("cost_usd", 0) or 0) for row in ledger)}
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents": len(results),
                      "before_statuses": {status: sum(row["before_status"] == status for row in results)
                                          for status in sorted({row["before_status"] for row in results})},
                      "after_statuses": {status: sum(row["after_status"] == status for row in results)
                                         for status in sorted({row["after_status"] for row in results})},
                      "repaired_citations": sum(row["repaired_citation_count"] for row in results),
                      "replay_usage_rows": len(ledger), "replay_cost_usd": output["total_replay_cost_usd"],
                      "samples": str(SAMPLE_DIR.relative_to(ROOT)),
                      "output": str(OUTPUT.relative_to(ROOT))}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
