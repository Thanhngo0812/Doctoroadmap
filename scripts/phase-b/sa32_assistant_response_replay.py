"""Replay the six saved assistant responses through B2 offline, without prompt matching."""
from __future__ import annotations

import json
from pathlib import Path

from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.scope import module_scope
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "artifacts/phase_b/recordings/acceptance-group2-v2/assistant.json"
OPERATIONS = ROOT / "tmp/phaseb-live-group2-v2.json"
OUTPUT = ROOT / "tmp/sa32-assistant-response-replay.json"
PINS = [
    ("doc-1", 37),
    ("nhap-mon-ml", 37),
    ("naive-bayes", 37),
    ("doc-6", 8),
    ("xstk-ch3-1", 46),
    ("doc-4", 12),
]
ROADMAP_PINS = [("doc-1", 57), ("doc-4", 27)]


class RecordedResponses:
    """Feed saved response events verbatim; deliberately do not validate old prompts."""

    is_replay = True

    def __init__(self, model_id: str, sessions: list[dict]):
        self.model_id = model_id
        self.sessions = sessions
        self.index = 0
        self.events = None

    def start_session(self, prompt, tools):
        if self.index >= len(self.sessions):
            raise RuntimeError("recording has no unused assistant response")
        calls = self.sessions[self.index].get("calls", [])
        if len(calls) != 1 or calls[0].get("kind") != "conversation":
            raise ValueError("each response fixture must contain exactly one conversation call")
        events = calls[0].get("events", [])
        if any(event.get("type") not in {"delta", "done"} for event in events):
            raise ValueError("response fixture contains tool events; response-only replay refused")
        self.events = events
        self.index += 1
        return self

    def stream(self, messages, *, mode):
        for event in self.events:
            if event["type"] == "delta":
                yield Delta(event.get("text", ""))
            else:
                yield Done(event.get("usage", {}), event.get("finish_reason"),
                           event.get("turn_id"), event.get("ttft_ms"))


def _roadmap_sizes(runtime: PhaseBRuntime) -> list[dict]:
    rows = []
    store = InMemoryPhaseBStore()
    for doc_id, version in ROADMAP_PINS:
        graph = runtime.graph(doc_id, version)
        assistant = AssistantUseCase(graph, store, model=None)
        structured = assistant._scope_card(graph, {"kind": "roadmap"}, None)
        compact = assistant._prompt_scope_card(graph, {"kind": "roadmap"}, None)
        from doc2roadmap.application.phase_b.common import stable_json
        rows.append({"doc_id": doc_id, "graph_version": version,
                     "module_count": len(structured["modules"]),
                     "structured_tokens_estimate": len(stable_json(structured)) // 3,
                     "compact_prompt_tokens_estimate": len(stable_json(compact)) // 3})
    return rows


def main() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    operations = json.loads(OPERATIONS.read_text(encoding="utf-8"))
    if fixture.get("fixture_version") != 1 or len(fixture.get("sessions", [])) != 6:
        raise ValueError("expected six recorded assistant responses")
    if operations.get("phase") != "live":
        raise ValueError("expected the saved Group 2 development operation set")
    assistant_ops = [row for row in operations.get("operations", []) if row.get("kind") == "assistant"]
    if [(row.get("doc_id"), row.get("graph_version")) for row in assistant_ops] != PINS:
        raise ValueError("assistant operations do not match the pinned six-document set")

    runtime = PhaseBRuntime(settings=Settings(artifact_dir=Path("artifacts")),
                            b_settings=BSettings(), allow_spend=False, mode="offline")
    store = InMemoryPhaseBStore()
    model = RecordedResponses(fixture["model_id"], fixture["sessions"])
    results = []
    for operation in assistant_ops:
        graph = runtime.graph(operation["doc_id"], operation["graph_version"])
        module_id = graph.nodes[operation["node_id"]].get("module_id")
        session = SessionUseCase(store, graph, settings=runtime.b_settings).create_session(
            "acceptance-group2", operation["doc_id"], module_scope(graph, module_id))
        captured = operation["captured_searches"]
        if len(captured) != 1:
            raise ValueError(f"expected one captured search for {operation['doc_id']}")

        def search(query, *, scope="ưu tiên module", k=4, current_module_id=None, row=captured[0]):
            if query != row["query"]:
                raise ValueError("captured retrieval query does not match operation")
            return row["result"]

        result = AssistantUseCase(graph, store, model, search=search,
                                  settings=runtime.b_settings).ask(
            operation["doc_id"], operation["graph_version"], session["session_id"],
            f"Theo tài liệu, {operation['concept']} là gì?", owner="acceptance-group2")
        results.append({"doc_id": operation["doc_id"],
                        "graph_version": operation["graph_version"],
                        "recorded_status": operation["result"].get("status"),
                        "replay_status": result.get("status"),
                        "citation_count": len(result.get("citations", [])),
                        "model_calls": result.get("usage", {}).get("model_calls"),
                        "cost_usd": result.get("usage", {}).get("usd"),
                        "turn_count": len(SessionUseCase(
                            store, graph, settings=runtime.b_settings).list_turns(
                                "acceptance-group2", session["session_id"]))})

    usage = store.usage_rows()
    if model.index != 6 or len(usage) != 6 or any(row.get("cost_usd", 0) for row in usage):
        raise AssertionError("response replay did not use six zero-cost recorded responses")
    output = {"replay_mode": "recorded_responses_without_prompt_matching",
              "fixture": str(FIXTURE.relative_to(ROOT)),
              "operation_source": str(OPERATIONS.relative_to(ROOT)),
              "fixture_sessions_used": model.index, "ledger_rows": len(usage),
              "ledger_cost_usd": sum(row.get("cost_usd", 0) or 0 for row in usage),
              "results": results, "roadmap_card_sizes": _roadmap_sizes(runtime)}
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fixture_sessions_used": model.index, "ledger_cost_usd": output["ledger_cost_usd"],
                      "statuses": {row["doc_id"]: row["replay_status"] for row in results},
                      "roadmap_card_sizes": output["roadmap_card_sizes"],
                      "output": str(OUTPUT.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
