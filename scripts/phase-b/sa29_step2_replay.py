"""SA-29 step 2: replay SA-28 replies through book and teaching vocab rules."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from doc2roadmap.composition_phase_b import DEVELOPMENT_DOCS
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import JsonPhaseBStore
from sa29_replay_support import Sa28RequestReplay, load_sa28_requests


ROOT = Path(__file__).resolve().parents[2]
PINS = {"doc-1": 52, "nhap-mon-ml": 37, "naive-bayes": 37,
        "doc-6": 24, "xstk-ch3-1": 63, "doc-4": 22}
PHASE_B_CACHE = ROOT / "artifacts/phase_b/sa28-20261018.json"
RESULT = ROOT / "artifacts/phase_b/sa29-step2-20261018.json"
NAMING_FIELDS = {"title", "description", "title_source", "description_source", "naming_flags", "section_code"}


def without_naming(payload: dict) -> dict:
    value = json.loads(json.dumps(payload, ensure_ascii=False))
    value.pop("module_naming_contract", None)
    value["modules"] = [{key: row for key, row in module.items() if key not in NAMING_FIELDS}
                         for module in value["modules"]]
    return value


def run() -> dict:
    if tuple(PINS) != tuple(DEVELOPMENT_DOCS):
        raise RuntimeError("pinned documents differ from the dev-only allowlist")
    if not PHASE_B_CACHE.is_file():
        raise RuntimeError("isolated SA-28 cache is required")
    if RESULT.exists():
        raise RuntimeError(f"refusing to overwrite {RESULT}")
    artifacts = JsonArtifactStore(Settings().artifact_dir)
    phase_store = JsonPhaseBStore(PHASE_B_CACHE)
    recorded_prompt, recorded_requests = load_sa28_requests()
    reports = []
    totals = Counter()
    for doc_id, source_version in PINS.items():
        source = artifacts.load_graph(doc_id, source_version)
        if source.version != source_version or source.payload.get("stage") != "stages":
            raise RuntimeError(f"{doc_id}: pinned A10 source mismatch")
        use_case = Sa28RequestReplay(artifacts, object(), phase_b_store=phase_store, settings=BSettings(),
                                     recorded_prompt=recorded_prompt, recorded_requests=recorded_requests)
        plan = use_case.plan(doc_id, upstream=source)
        if plan.calls_estimate != 0:
            raise RuntimeError(f"{doc_id}: expected complete SA-28 cache, found misses")
        named, _ = use_case.execute(doc_id, upstream=source)
        if without_naming(source.payload) != without_naming(named.payload):
            raise RuntimeError(f"{doc_id}: non-naming graph fields changed")
        modules = named.payload["modules"]
        title_sources = Counter(module.get("title_source", "unknown") for module in modules)
        description_sources = Counter(module.get("description_source", "unknown") for module in modules)
        flags = Counter(flag for module in modules for flag in module.get("naming_flags", []))
        totals.update({"modules": len(modules), "llm_titles": title_sources["llm"],
                       "llm_descriptions": description_sources["llm"],
                       "template_descriptions": description_sources["template"]})
        reports.append({"doc_id": doc_id, "source_a10": source_version, "output_graph": named.version,
                        "modules": len(modules), "title_sources": dict(title_sources),
                        "description_sources": dict(description_sources), "flags": dict(flags),
                        "source_invariants_exact": True})
    if totals["modules"] != 160 or totals["llm_titles"] != 144:
        raise RuntimeError(f"unexpected independent title-validation counts: {dict(totals)}")
    result = {"task": "SA-29 step 2", "mode": "sa28_cache_only", "provider_calls": 0,
              "estimated_cost_usd": 0.0, "totals": dict(totals), "documents": reports}
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
