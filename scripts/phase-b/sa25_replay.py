from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.phase_b.postcheck import check_text
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.llm.phase_b import ReplayToolModel


ROOT = Path.cwd()
LIVE = ROOT / "tmp/phaseb-live-group2-v2.json"
BASE = ROOT / "artifacts/phase_b/recordings/acceptance-group2-v2"
RESUME = BASE / "resume"
MERGED = ROOT / "tmp/phaseb-sa25-recordings"
OUTPUT = ROOT / "tmp/phaseb-sa25-replay.json"
SAMPLE_DIR = ROOT / "tmp/phaseb-sa25-documents"
OWNER = "acceptance-group2"


def _merge(kind: str) -> Path:
    paths = [directory / f"{kind}.json" for directory in (BASE, RESUME)]
    fixtures = [json.loads(path.read_text(encoding="utf-8")) for path in paths if path.is_file()]
    if not fixtures:
        raise FileNotFoundError(f"no saved {kind} replay fixture")
    first = fixtures[0]
    identity = (first.get("prompt_hash"), first.get("model_id"), first.get("fixture_version"))
    if any((item.get("prompt_hash"), item.get("model_id"), item.get("fixture_version")) != identity
           for item in fixtures[1:]):
        raise ValueError(f"incompatible saved {kind} fixtures")
    first["sessions"] = [session for item in fixtures for session in item["sessions"]]
    MERGED.mkdir(parents=True, exist_ok=True)
    path = MERGED / f"{kind}.json"
    path.write_text(json.dumps(first, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _counts(check: dict) -> dict:
    return dict(check.get("counts", check))


def _assistant_search(operation: dict):
    captured = operation["captured_searches"]
    if len(captured) != 1:
        raise ValueError(f"expected one captured assistant search for {operation['doc_id']}")
    row = captured[0]

    def search(query, *, scope="ưu tiên module", k=4, current_module_id=None):
        if query != row["query"]:
            raise ValueError("assistant replay search query mismatch")
        return row["result"]

    return search


def _document_search(operation: dict):
    captured = operation["captured_searches"]
    if len(captured) != 1:
        raise ValueError(f"expected one captured document search for {operation['doc_id']}")
    row = captured[0]

    class StaticSearch:
        def search(self, query, **kwargs):
            if query != row["query"]:
                raise ValueError("document replay search query mismatch")
            return row["result"]

    return StaticSearch()


def _raw_replay_value(model: ReplayToolModel, previous_sessions: set[int], *, purpose: str) -> object:
    new_sessions = model._reserved - previous_sessions
    if len(new_sessions) != 1:
        raise AssertionError(f"expected one consumed {purpose} session; got {len(new_sessions)}")
    session = model._sessions[next(iter(new_sessions))]
    call = session["calls"][0]
    if purpose == "assistant":
        return "".join(event.get("text", "") for event in call["events"] if event["type"] == "delta")
    return call["reply"]["payload"]


def _assistant_source_map(graph, operation: dict) -> dict[str, dict]:
    registry = graph.new_source_registry() if hasattr(graph, "new_source_registry") else graph.sources
    result = {}
    for row in operation["captured_searches"][0]["result"]:
        chunk_id = row.get("chunk_id")
        if chunk_id in graph.chunks:
            label = registry.label(chunk_id)
            result[label] = registry.citation(label)
    return result


def _document_source_map(graph, operation: dict, settings: BSettings, payload: dict,
                         final_document: dict) -> dict[str, dict]:
    # Use the same pinned scope assembly and captured retrieval labels as the
    # document request; keep only source citations that passed quote checks.
    from doc2roadmap.application.phase_b.lectures import _assemble

    registry = graph.new_source_registry() if hasattr(graph, "new_source_registry") else graph.sources
    assembled, _, _ = _assemble(graph, operation["node_id"], settings, registry)
    known_chunks = {row.get("chunk_id") for row in assembled.get("sources", {}).values()}
    for row in operation["captured_searches"][0]["result"]:
        chunk_id = row.get("chunk_id")
        if chunk_id in graph.chunks and chunk_id not in known_chunks:
            registry.label(chunk_id, "S")
            known_chunks.add(chunk_id)
    return {str(row["label"]): row for row in final_document.get("citations", [])
            if isinstance(row, dict) and row.get("label")}


def main() -> None:
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    assistant_fixture = _merge("assistant")
    document_fixture = _merge("document")
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=Path("artifacts")),
                            b_settings=BSettings(), allow_spend=False, mode="offline")
    store = InMemoryPhaseBStore()
    # These three validator-only fields were added after the saved Group 2
    # recordings. Use the recorded settings fingerprint, while ReplayToolModel
    # still verifies the exact system prompt, tools, messages, schema, and call.
    recorded_settings = asdict(runtime.b_settings)
    for key in ("lecture_duplicate_jaccard_threshold", "lecture_validator_version",
                "connector_sentence_max_chars"):
        recorded_settings.pop(key, None)
    assistant_model = ReplayToolModel(
        assistant_fixture, prompt_hash=context_hash(["phase-b-v1", "assistant", recorded_settings]))
    document_model = ReplayToolModel(
        document_fixture, prompt_hash=context_hash(["phase-b-v1", "document", recorded_settings]))
    operations = [row for row in live["operations"] if row["kind"] in {"assistant", "document"}]
    if len(operations) != 12 or sum(row["kind"] == "assistant" for row in operations) != 6:
        raise RuntimeError("expected the saved 6-assistant / 6-document Group 2 scope")
    results = []
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    for operation in operations:
        graph = runtime.graph(operation["doc_id"], operation["graph_version"])
        if operation["kind"] == "assistant":
            search = _assistant_search(operation)
            before_sessions = set(assistant_model._reserved)
            use_case = AssistantUseCase(graph, store, assistant_model, search=search,
                                        settings=runtime.b_settings)
            result = use_case.ask(
                operation["doc_id"], operation["graph_version"],
                f"acceptance-group2-{operation['doc_id']}",
                graph.nodes[operation["node_id"]].get("module_id"),
                f"Theo tài liệu, {operation['concept']} là gì?", owner=OWNER,
                client_turn_id=f"group2-{operation['doc_id']}", allow_spend=True,
            )
            raw = _raw_replay_value(assistant_model, before_sessions, purpose="assistant")
            citations_by_label = _assistant_source_map(graph, operation)
            if str(raw).lstrip().startswith("KHONG_DU"):
                before = {"counts": {"unsourced_sentence": 0, "labels_removed": 0,
                                     "outside_blocks_removed": 0, "sourced_sentences": 0}, "warnings": []}
            else:
                before = check_text(raw, graph=graph, settings=runtime.b_settings,
                                    citations_by_label=citations_by_label)
            if result.get("status") == "insufficient_context":
                after = {"counts": {"unsourced_sentence": 0, "labels_removed": 0,
                                    "outside_blocks_removed": 0, "sourced_sentences": 0}, "warnings": []}
            else:
                after = check_text(result.get("answer", ""), graph=graph, settings=runtime.b_settings,
                                   citations_by_label=citations_by_label)
            record = {
                "kind": "assistant", "doc_id": operation["doc_id"],
                "graph_version": operation["graph_version"], "concept": operation["concept"],
                "before_status": operation["result"].get("status"), "after_status": result.get("status"),
                "precheck_counts": _counts(before), "postcheck_counts": _counts(after),
                "postcheck_removed": _counts(before), "postcheck_residual": _counts(after),
                "postcheck_residual_warnings": after.get("warnings", []),
                "warnings": result.get("warnings", []), "outside_document_blocks": result.get("outside_document_blocks", 0),
                "answer": result.get("answer", ""), "usage": result.get("usage", {}),
            }
            results.append(record)
        else:
            request = f"Tạo bản ôn tập ngắn về {operation['concept']}, mỗi ý có trích dẫn."
            before_sessions = set(document_model._reserved)
            use_case = DocumentUseCase(document_model, store, settings=runtime.b_settings,
                                       retriever=_document_search(operation))
            result = use_case.create(operation["doc_id"], str(operation["graph_version"]), graph,
                                     request, operation["node_id"], owner=OWNER, allow_spend=True)
            payload = _raw_replay_value(document_model, before_sessions, purpose="document")
            citations_by_label = _document_source_map(graph, operation, runtime.b_settings,
                                                       payload, result)
            before = check_text(str(payload.get("markdown", "")), graph=graph, settings=runtime.b_settings,
                                citations_by_label=citations_by_label,
                                outside_blocks=payload.get("outside_document_blocks", []))
            after = check_text(str(result.get("markdown", "")), graph=graph, settings=runtime.b_settings,
                               citations_by_label=citations_by_label)
            sample = {key: result.get(key) for key in (
                "contract_version", "document_id", "owner", "doc_id", "graph_version", "request",
                "scope", "title", "markdown", "citations", "outside_document_blocks", "status",
                "reason", "warnings", "postcheck", "usage")}
            stem = f"{operation['doc_id']}-document"
            (SAMPLE_DIR / f"{stem}.md").write_text(str(sample.get("markdown", "")), encoding="utf-8")
            (SAMPLE_DIR / f"{stem}.json").write_text(
                json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            results.append({
                "kind": "document", "doc_id": operation["doc_id"],
                "graph_version": operation["graph_version"], "concept": operation["concept"],
                "before_status": operation["result"].get("status"), "after_status": result.get("status"),
                "precheck_counts": _counts(before), "postcheck_counts": _counts(result.get("postcheck", {})),
                "postcheck_removed": _counts(result.get("postcheck") or before),
                "residual_counts": _counts(after), "warnings": result.get("warnings", []),
                "residual_warnings": after.get("warnings", []),
                "residual_text": after.get("text", ""),
                "outside_document_blocks": result.get("outside_document_blocks", 0),
                "markdown_sample": str(sample.get("markdown", ""))[:1200],
                "usage": result.get("usage", {}),
            })
    usage = store.usage_rows()
    output = {
        "source": str(LIVE.relative_to(ROOT)),
        "fixture_sources": [str(assistant_fixture.relative_to(ROOT)), str(document_fixture.relative_to(ROOT))],
        "results": results,
        "usage_rows": usage,
        "total_cost_usd": sum(float(row.get("cost_usd", 0) or 0) for row in usage),
    }
    output["postcheck_totals"] = {
        "unsourced_sentences_removed": sum(row["postcheck_removed"].get("unsourced_sentence", 0)
                                            for row in results),
        "labels_removed": sum(row["postcheck_removed"].get("labels_removed", 0) for row in results),
        "outside_blocks_removed": sum(row["postcheck_removed"].get("outside_blocks_removed", 0)
                                       for row in results),
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"results": len(results),
                      "assistant_statuses": {status: sum(row["after_status"] == status
                          for row in results if row["kind"] == "assistant")
                          for status in sorted({row["after_status"] for row in results if row["kind"] == "assistant"})},
                      "document_statuses": {status: sum(row["after_status"] == status
                          for row in results if row["kind"] == "document")
                          for status in sorted({row["after_status"] for row in results if row["kind"] == "document"})},
                      "samples": str(SAMPLE_DIR.relative_to(ROOT)),
                      "ledger_rows": len(usage), "cost_usd": output["total_cost_usd"],
                      "postcheck_totals": output["postcheck_totals"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
