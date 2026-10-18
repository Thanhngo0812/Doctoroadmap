from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from collections import Counter
from pathlib import Path
from urllib.request import Request

from doc2roadmap.application.phase_b.naming import NameModulesB, SCHEMA, _display
from doc2roadmap.application.phase_b.common import stable_json
from doc2roadmap.composition_phase_b import DEVELOPMENT_DOCS, PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.phase_b_pricing import estimate_cost
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore
import doc2roadmap.infrastructure.llm.phase_b as phase_b_transport


ROOT = Path(__file__).resolve().parents[2]
PINS = {
    "doc-1": (52, 53), "nhap-mon-ml": (37, 46), "naive-bayes": (37, 45),
    "doc-6": (24, 25), "xstk-ch3-1": (63, 64), "doc-4": (22, 23),
}
CAP_USD = 0.50
MODEL_ID = "gemini-3.1-flash-lite"
STORE_PATH = ROOT / "artifacts/phase_b/sa28-20261018.json"
RECORD_DIR = ROOT / "artifacts/phase_b/recordings/sa28-20261018"
RESULT_PATH = ROOT / "tmp/sa28-live-20261018.json"
NAMING_FIELDS = {"title", "description", "title_source", "description_source", "naming_flags", "section_code"}


class BudgetGate:
    """Conservative upper bound charged once for each actual transport attempt."""
    def __init__(self, cap: float):
        self.cap = cap
        self.reserved = 0.0
        self._lock = threading.Lock()

    def reserve_request(self, request: Request) -> float:
        if not isinstance(request.data, (bytes, bytearray)):
            raise RuntimeError("cannot estimate Gemini request body; refusing network call")
        try:
            body = json.loads(request.data)
            output_tokens = int(body["generationConfig"]["maxOutputTokens"])
        except (ValueError, KeyError, TypeError) as error:
            raise RuntimeError("cannot inspect Gemini request budget; refusing network call") from error
        cost = estimate_cost(MODEL_ID, len(request.data), output_tokens)
        with self._lock:
            if self.reserved + cost > self.cap:
                raise PermissionError(f"SA-28 hard cap reached before transport attempt (${self.cap:.2f})")
            self.reserved += cost
        return cost


def install_budget_gate(gate: BudgetGate):
    original = phase_b_transport.urlopen

    def guarded_urlopen(request, timeout=None):
        gate.reserve_request(request)
        return original(request, timeout=timeout)

    phase_b_transport.urlopen = guarded_urlopen
    return original


def save_result(result: dict) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = RESULT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, RESULT_PATH)


def payload_without_naming(payload: dict) -> dict:
    value = json.loads(json.dumps(payload, ensure_ascii=False))
    value.pop("module_naming_contract", None)
    value["modules"] = [{key: item for key, item in module.items() if key not in NAMING_FIELDS}
                         for module in value.get("modules", [])]
    return value


def list_only_count(payload: dict) -> tuple[int, int]:
    nodes = {node["node_id"]: node for node in payload["nodes"]}
    llm_count = list_only = 0
    for module in payload["modules"]:
        if module.get("description_source") != "llm":
            continue
        llm_count += 1
        names = {_display(nodes[node_id]).casefold() for node_id in module["node_ids"]}
        fragments = [part.strip(" .;:") for row in module.get("description", [])
                     for part in re.split(r",|\bvà\b", str(row.get("text", "")), flags=re.I)]
        if fragments and all(fragment.casefold() in names for fragment in fragments):
            list_only += 1
    return list_only, llm_count


def _estimated_request_cost(system_prompt: str, user_prompt: str, settings: BSettings) -> float:
    body = {"systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": settings.naming_temperature,
                                 "maxOutputTokens": settings.naming_max_output_tokens,
                                 "responseMimeType": "application/json", "responseJsonSchema": SCHEMA}}
    encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return estimate_cost(settings.model_id, len(encoded), settings.naming_max_output_tokens)


def preflight() -> dict:
    artifacts = JsonArtifactStore(Settings().artifact_dir)
    settings = BSettings(model_id=MODEL_ID)
    result = []
    total_modules = 0
    total_cost = 0.0
    for doc_id, (source_version, baseline_version) in PINS.items():
        source = artifacts.load_graph(doc_id, source_version)
        baseline = artifacts.load_graph(doc_id, baseline_version)
        if source.payload.get("stage") != "stages" or not source.payload.get("modules"):
            raise RuntimeError(f"{doc_id} v{source_version} is not a completed A10 graph")
        use_case = NameModulesB(artifacts, object(), phase_b_store=InMemoryPhaseBStore(), settings=settings)
        chunks, prepared = use_case._prepare(doc_id, source)
        prompt = use_case._prompt()
        requests_cost = sum(_estimated_request_cost(prompt, stable_json(row[2]), settings) for row in prepared)
        baseline_list_only, baseline_llm = list_only_count(baseline.payload)
        modules = len(source.payload["modules"])
        total_modules += modules
        total_cost += requests_cost
        result.append({"doc_id": doc_id, "source_a10": source_version, "named_baseline": baseline_version,
                       "modules": modules, "planned_calls": modules,
                       "estimated_cost_usd": round(requests_cost, 8),
                       "baseline_list_only": baseline_list_only, "baseline_llm_descriptions": baseline_llm})
    if total_modules != 160:
        raise RuntimeError(f"expected 160 pinned modules, found {total_modules}")
    return {"mode": "preflight_no_calls_no_writes", "model_id": MODEL_ID, "cap_usd": CAP_USD,
            "planned_calls": total_modules, "estimated_cost_usd": round(total_cost, 8), "docs": result}


def cache_check() -> dict:
    if not STORE_PATH.exists():
        raise RuntimeError("SA-28 ledger is missing; cache check requires the completed isolated run")
    artifacts = JsonArtifactStore(Settings().artifact_dir)
    phase_store = JsonPhaseBStore(STORE_PATH)
    settings = BSettings(model_id=MODEL_ID)
    rows = []
    for doc_id, (source_version, _) in PINS.items():
        source = artifacts.load_graph(doc_id, source_version)
        use_case = NameModulesB(artifacts, object(), phase_b_store=phase_store, settings=settings)
        plan = use_case.plan(doc_id, upstream=source)
        rows.append({"doc_id": doc_id, "source_a10": source_version,
                     "modules": len(source.payload["modules"]), "calls_estimate": plan.calls_estimate,
                     "usd_estimate": plan.usd_estimate})
    if any(row["calls_estimate"] for row in rows):
        raise RuntimeError("cached SA-28 plan unexpectedly requires provider calls")
    return {"mode": "cache_replay_plan_only_no_provider_no_writes", "planned_calls": 0,
            "usd_estimate": 0.0, "docs": rows}


def main() -> None:
    if "--preflight" in sys.argv:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))
        return
    if "--cache-check" in sys.argv:
        print(json.dumps(cache_check(), ensure_ascii=False, indent=2))
        return
    if STORE_PATH.exists() or RECORD_DIR.exists() or RESULT_PATH.exists():
        raise RuntimeError("SA-28 isolated output already exists; refusing to overwrite or duplicate a run")
    if tuple(PINS) != tuple(DEVELOPMENT_DOCS):
        raise RuntimeError("pinned documents differ from the Phase B dev-only allowlist")

    started = time.perf_counter()
    settings = Settings()
    if settings.llm_transport == "developer_api" and not settings.gemini_api_key:
        raise RuntimeError("Gemini API key is not configured")
    b_settings = BSettings(model_id=MODEL_ID)
    runtime = PhaseBRuntime(settings=settings, b_settings=b_settings, allow_spend=True, mode="gemini",
                            store_path=STORE_PATH, record_dir=RECORD_DIR)
    tracker = BudgetGate(CAP_USD)
    original_urlopen = install_budget_gate(tracker)
    output = {"status": "running", "task": "SA-28", "cap_usd": CAP_USD, "model_id": MODEL_ID,
              "documents": {}, "transport_attempt_upper_bound_usd": 0.0,
              "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    save_result(output)
    try:
        for doc_id, (source_version, baseline_version) in PINS.items():
            doc_started = time.perf_counter()
            source = runtime.artifacts.load_graph(doc_id, source_version)
            baseline = runtime.artifacts.load_graph(doc_id, baseline_version)
            if source.version != source_version or source.payload.get("stage") != "stages":
                raise RuntimeError(f"{doc_id}: pinned A10 source mismatch")
            # Exact upstream from the pin; module naming runs serially to make the gate auditable.
            model = runtime.model("module_title")
            use_case = NameModulesB(runtime.artifacts, model, phase_b_store=runtime.store, settings=b_settings,
                                    allow_spend=True, concurrency=1)
            plan = use_case.plan(doc_id, upstream=source)
            if plan.calls_estimate != len(source.payload["modules"]):
                raise RuntimeError(f"{doc_id}: isolated v4 cache unexpectedly reduced the plan")
            named, _ = use_case.execute(doc_id, upstream=source)
            invariant_ok = payload_without_naming(source.payload) == payload_without_naming(named.payload)
            if not invariant_ok:
                raise RuntimeError(f"{doc_id}: non-naming graph fields changed")
            rows = named.payload["modules"]
            flags = Counter(flag for module in rows for flag in module.get("naming_flags", []))
            title_sources = Counter(module.get("title_source", "unknown") for module in rows)
            listonly_after, llm_after = list_only_count(named.payload)
            listonly_before, llm_before = list_only_count(baseline.payload)
            usage = runtime.store.usage_rows(doc_id)
            doc_cost = sum(float(row.get("cost_usd", 0) or 0) for row in usage)
            if tracker.reserved > CAP_USD or doc_cost > CAP_USD:
                raise RuntimeError("SA-28 budget cap exceeded")
            details = {"source_a10": source_version, "named_baseline": baseline_version,
                       "output_graph": named.version, "modules": len(rows),
                       "title_sources": dict(title_sources), "fallback_flags": dict(flags),
                       "baseline_list_only": [listonly_before, llm_before],
                       "after_list_only": [listonly_after, llm_after],
                       "description_ids": sum(bool(re.search(r"\b(?:module|node)_\w+", item.get("text", ""), re.I))
                                               for module in rows for item in module.get("description", [])),
                       "source_invariants_exact": invariant_ok, "usage_rows": usage,
                       "ledger_usd": round(doc_cost, 8), "transport_attempt_upper_bound_usd": round(tracker.reserved, 8),
                       "elapsed_ms": round((time.perf_counter() - doc_started) * 1000),
                       "modules_output": rows}
            output["documents"][doc_id] = details
            output["transport_attempt_upper_bound_usd"] = round(tracker.reserved, 8)
            save_result(output)
        output["status"] = "complete"
    except BaseException as error:
        output["status"] = "failed"
        output["error"] = f"{type(error).__name__}: {error}"
        output["transport_attempt_upper_bound_usd"] = round(tracker.reserved, 8)
        output["usage_rows_final"] = runtime.store.usage_rows()
        save_result(output)
        raise
    finally:
        phase_b_transport.urlopen = original_urlopen
        output["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
        output["ledger_usd_final"] = round(sum(float(row.get("cost_usd", 0) or 0)
                                                for row in runtime.store.usage_rows()), 8)
        output["usage_rows_final"] = runtime.store.usage_rows()
        save_result(output)
    print(json.dumps({"status": output["status"], "docs": list(output["documents"]),
                      "transport_attempt_upper_bound_usd": output["transport_attempt_upper_bound_usd"],
                      "ledger_usd_final": output["ledger_usd_final"], "elapsed_ms": output["elapsed_ms"]}, indent=2))


if __name__ == "__main__":
    main()
