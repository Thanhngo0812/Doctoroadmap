"""SA-29 six-book runner. Defaults to a read-only preflight; spending is explicit."""
from __future__ import annotations

import json
import hashlib
import os
import re
import sys
import threading
import time
from collections import Counter
from pathlib import Path
from urllib.request import Request

from doc2roadmap.application.phase_b.common import stable_json
from doc2roadmap.application.phase_b.naming import NameModulesB, SCHEMA, _display
from doc2roadmap.composition_phase_b import DEVELOPMENT_DOCS, PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.phase_b_pricing import estimate_cost
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore
import doc2roadmap.infrastructure.llm.phase_b as phase_b_transport


ROOT = Path(__file__).resolve().parents[2]
PINS = {"doc-1": (52, 53), "nhap-mon-ml": (37, 46), "naive-bayes": (37, 45),
        "doc-6": (24, 25), "xstk-ch3-1": (63, 64), "doc-4": (22, 23)}
CAP_USD = 0.50
MODEL_ID = "gemini-3.1-flash-lite"
STORE_PATH = ROOT / "artifacts/phase_b/sa29-20261018.json"
RECORD_DIR = ROOT / "artifacts/phase_b/recordings/sa29-20261018"
RESULT_PATH = ROOT / "tmp/sa29-live-20261018.json"
NAMING_FIELDS = {"title", "description", "title_source", "description_source", "naming_flags", "section_code"}


class BudgetGate:
    """Reserve a byte-based upper estimate before every transport attempt."""
    def __init__(self, cap: float):
        self.cap = cap
        self.reserved = 0.0
        self.attempts = 0
        self.bytes = 0
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
                raise PermissionError(f"SA-29 hard cap reached before transport attempt (${self.cap:.2f})")
            self.reserved += cost
            self.attempts += 1
            self.bytes += len(request.data)
        return cost


def install_budget_gate(gate: BudgetGate):
    original = phase_b_transport.urlopen

    def guarded_urlopen(request, timeout=None):
        gate.reserve_request(request)
        return original(request, timeout=timeout)

    phase_b_transport.urlopen = guarded_urlopen
    return original


def _request_body(system_prompt: str, user_prompt: str, settings: BSettings) -> bytes:
    body = {"systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": settings.naming_temperature,
                                 "maxOutputTokens": settings.naming_max_output_tokens,
                                 "responseMimeType": "application/json", "responseJsonSchema": SCHEMA}}
    return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def preflight() -> dict:
    if tuple(PINS) != tuple(DEVELOPMENT_DOCS):
        raise RuntimeError("pinned documents differ from the Phase B dev-only allowlist")
    artifacts = JsonArtifactStore(Settings().artifact_dir)
    settings = BSettings(model_id=MODEL_ID)
    docs = []
    total_modules = total_bytes = 0
    total_cost = 0.0
    for doc_id, (source_version, baseline_version) in PINS.items():
        source = artifacts.load_graph(doc_id, source_version)
        baseline = artifacts.load_graph(doc_id, baseline_version)
        if source.version != source_version or source.payload.get("stage") != "stages":
            raise RuntimeError(f"{doc_id}: pinned A10 source mismatch")
        if not source.payload.get("modules"):
            raise RuntimeError(f"{doc_id} v{source_version} has no A10 modules")
        use_case = NameModulesB(artifacts, object(), phase_b_store=InMemoryPhaseBStore(), settings=settings)
        plan = use_case.plan(doc_id, upstream=source)
        if plan.calls_estimate != len(source.payload["modules"]):
            raise RuntimeError(f"{doc_id}: expected {len(source.payload['modules'])} requests, got {plan.calls_estimate}")
        chunks, prepared = use_case._prepare(doc_id, source)
        prompt = use_case._prompt()
        request_sizes = [len(_request_body(prompt, stable_json(row[2]), settings)) for row in prepared]
        cost = sum(estimate_cost(MODEL_ID, size, settings.naming_max_output_tokens) for size in request_sizes)
        modules = len(source.payload["modules"])
        total_modules += modules
        total_bytes += sum(request_sizes)
        total_cost += cost
        baseline_sources = Counter(module.get("description_source", "unknown") for module in baseline.payload["modules"])
        docs.append({"doc_id": doc_id, "source_a10": source_version, "named_baseline": baseline_version,
                     "modules": modules, "planned_calls": plan.calls_estimate,
                     "request_bytes_total": sum(request_sizes), "request_bytes_min": min(request_sizes),
                     "request_bytes_max": max(request_sizes), "estimated_usd_upper": round(cost, 8),
                     "baseline_description_sources": dict(baseline_sources)})
    if total_modules != 160:
        raise RuntimeError(f"expected 160 pinned modules, found {total_modules}")
    if total_cost > CAP_USD:
        raise RuntimeError(f"preflight estimate ${total_cost:.6f} exceeds hard cap ${CAP_USD:.2f}")
    return {"mode": "preflight_no_calls_no_writes", "model_id": MODEL_ID, "cap_usd": CAP_USD,
            "planned_calls": total_modules, "request_bytes_total": total_bytes,
            "estimated_usd_upper": round(total_cost, 8), "docs": docs}


def without_naming(payload: dict) -> dict:
    value = json.loads(json.dumps(payload, ensure_ascii=False))
    value.pop("module_naming_contract", None)
    value["modules"] = [{key: item for key, item in module.items() if key not in NAMING_FIELDS}
                         for module in value.get("modules", [])]
    return value


def cache_check() -> dict:
    if not STORE_PATH.is_file() or not RESULT_PATH.is_file():
        raise RuntimeError("SA-29 live ledger and result are required for cache check")
    ledger_before = hashlib.sha256(STORE_PATH.read_bytes()).hexdigest()
    artifacts = JsonArtifactStore(Settings().artifact_dir)
    phase_store = JsonPhaseBStore(STORE_PATH)
    settings = BSettings(model_id=MODEL_ID)
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    rows = []
    if result.get("status") != "complete":
        raise RuntimeError(f"SA-29 result is {result.get('status')}, not complete")
    for doc_id, (source_version, _) in PINS.items():
        source = artifacts.load_graph(doc_id, source_version)
        use_case = NameModulesB(artifacts, object(), phase_b_store=phase_store, settings=settings)
        plan = use_case.plan(doc_id, upstream=source)
        if plan.calls_estimate != 0:
            raise RuntimeError(f"{doc_id}: cache check found {plan.calls_estimate} misses")
        named_version = result["documents"][doc_id]["output_graph"]
        named = artifacts.load_graph(doc_id, named_version)
        if without_naming(source.payload) != without_naming(named.payload):
            raise RuntimeError(f"{doc_id}: non-naming graph fields changed")
        rows.append({"doc_id": doc_id, "source_a10": source_version, "output_graph": named_version,
                     "modules": len(named.payload["modules"]), "calls_estimate": plan.calls_estimate,
                     "source_invariants_exact": True})
    ledger_after = hashlib.sha256(STORE_PATH.read_bytes()).hexdigest()
    if ledger_before != ledger_after:
        raise RuntimeError("cache check changed SA-29 ledger bytes")
    usage = phase_store.usage_rows()
    if len(usage) != 160:
        raise RuntimeError(f"expected 160 usage rows, found {len(usage)}")
    return {"mode": "read_only_cache_and_invariant_check", "provider_calls": 0,
            "ledger_sha256_unchanged": True, "usage_rows": len(usage),
            "usage_cost_usd": round(sum(float(row.get("cost_usd", 0) or 0) for row in usage), 8),
            "failed_usage_rows": sum(bool(row.get("error")) for row in usage), "documents": rows}


def save_result(result: dict) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = RESULT_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, RESULT_PATH)


def run_paid() -> dict:
    for path in (STORE_PATH, RECORD_DIR, RESULT_PATH):
        if path.exists():
            raise RuntimeError(f"SA-29 paid output already exists; refusing duplicate run: {path}")
    if tuple(PINS) != tuple(DEVELOPMENT_DOCS):
        raise RuntimeError("pinned documents differ from the Phase B dev-only allowlist")
    initial = preflight()
    settings = Settings()
    if settings.llm_transport != "vertex":
        raise RuntimeError(f"SA-29 requires the approved Vertex transport; configured: {settings.llm_transport}")
    b_settings = BSettings(model_id=MODEL_ID)
    runtime = PhaseBRuntime(settings=settings, b_settings=b_settings, allow_spend=True, mode="gemini",
                            store_path=STORE_PATH, record_dir=RECORD_DIR)
    gate = BudgetGate(CAP_USD)
    original_urlopen = install_budget_gate(gate)
    output = {"status": "running", "task": "SA-29", "model_id": MODEL_ID, "cap_usd": CAP_USD,
              "preflight": initial, "documents": {}, "transport_attempts": 0,
              "transport_attempt_upper_bound_usd": 0.0}
    save_result(output)
    try:
        for doc_id, (source_version, baseline_version) in PINS.items():
            started = time.perf_counter()
            source = runtime.artifacts.load_graph(doc_id, source_version)
            baseline = runtime.artifacts.load_graph(doc_id, baseline_version)
            if source.version != source_version:
                raise RuntimeError(f"{doc_id}: source pin mismatch")
            model = runtime.model("module_title")
            use_case = NameModulesB(runtime.artifacts, model, phase_b_store=runtime.store, settings=b_settings,
                                    allow_spend=True, concurrency=1)
            plan = use_case.plan(doc_id, upstream=source)
            if plan.calls_estimate != len(source.payload["modules"]):
                raise RuntimeError(f"{doc_id}: expected a fresh cache for {len(source.payload['modules'])} modules")
            named, _ = use_case.execute(doc_id, upstream=source)
            invariant_ok = without_naming(source.payload) == without_naming(named.payload)
            if not invariant_ok:
                raise RuntimeError(f"{doc_id}: non-naming graph fields changed")
            modules = named.payload["modules"]
            title_sources = Counter(module.get("title_source", "unknown") for module in modules)
            description_sources = Counter(module.get("description_source", "unknown") for module in modules)
            flags = Counter(flag for module in modules for flag in module.get("naming_flags", []))
            output["documents"][doc_id] = {
                "source_a10": source_version, "named_baseline": baseline_version,
                "output_graph": named.version, "modules": len(modules),
                "title_sources": dict(title_sources), "description_sources": dict(description_sources),
                "flags": dict(flags), "source_invariants_exact": invariant_ok,
                "ledger_usd": round(sum(float(row.get("cost_usd", 0) or 0)
                                         for row in runtime.store.usage_rows(doc_id)), 8),
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "modules_output": modules,
            }
            output["transport_attempts"] = gate.attempts
            output["transport_request_bytes"] = gate.bytes
            output["transport_attempt_upper_bound_usd"] = round(gate.reserved, 8)
            save_result(output)
        output["status"] = "complete"
    except BaseException as error:
        output["status"] = "failed"
        output["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        phase_b_transport.urlopen = original_urlopen
        output["transport_attempts"] = gate.attempts
        output["transport_request_bytes"] = gate.bytes
        output["transport_attempt_upper_bound_usd"] = round(gate.reserved, 8)
        output["usage_rows_final"] = runtime.store.usage_rows()
        output["ledger_usd_final"] = round(sum(float(row.get("cost_usd", 0) or 0)
                                                for row in runtime.store.usage_rows()), 8)
        save_result(output)
    return output


if __name__ == "__main__":
    if "--cache-check" in sys.argv:
        result = cache_check()
    elif "--allow-spend" in sys.argv:
        result = run_paid()
    else:
        result = preflight()
    if result.get("mode") == "preflight_no_calls_no_writes":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get("mode") == "read_only_cache_and_invariant_check":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"status": result.get("status"), "documents": list(result.get("documents", {})),
                          "transport_attempts": result.get("transport_attempts"),
                          "transport_request_bytes": result.get("transport_request_bytes"),
                          "transport_attempt_upper_bound_usd": result.get("transport_attempt_upper_bound_usd"),
                          "ledger_usd_final": result.get("ledger_usd_final"),
                          "elapsed_ms": result.get("elapsed_ms")}, ensure_ascii=False, indent=2))
