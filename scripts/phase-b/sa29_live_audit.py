"""Read-only quality diagnostics for the completed SA-29 output."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from doc2roadmap.application.phase_b.naming import NameModulesB, _display, _words
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore


ROOT = Path(__file__).resolve().parents[2]
PINS = {"doc-1": 52, "nhap-mon-ml": 37, "naive-bayes": 37,
        "doc-6": 24, "xstk-ch3-1": 63, "doc-4": 22}
RESULT = ROOT / "tmp/sa29-live-20261018.json"
RECORDING = ROOT / "artifacts/phase_b/recordings/sa29-20261018/module_title.json"


def run() -> dict:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    recording = json.loads(RECORDING.read_text(encoding="utf-8"))
    if result.get("status") != "complete":
        raise RuntimeError("SA-29 result must be complete before audit")
    replies = {}
    for session in recording["sessions"]:
        for call in session["calls"]:
            request = json.loads(call["prompt"])
            node_ids = tuple(sorted(item["node_id"] for item in request["concepts"]))
            replies[node_ids] = call["reply"]["payload"]

    artifacts = JsonArtifactStore(Settings().artifact_dir)
    aggregate = Counter()
    doc_rows, samples, self_reference_samples = [], [], []
    for doc_id, version in PINS.items():
        source = artifacts.load_graph(doc_id, version)
        use_case = NameModulesB(artifacts, settings=BSettings())
        chunks, prepared = use_case._prepare(doc_id, source)
        desc_vocabs, borrowed_vocabs = use_case._description_lexicons(chunks, prepared, source)
        prepared_by_nodes = {tuple(sorted(row[0]["node_ids"])): (index, row)
                             for index, row in enumerate(prepared)}
        document = result["documents"][doc_id]
        modules = document["modules_output"]
        counts = Counter()
        for module in modules:
            counts["modules"] += 1
            counts["title_" + module.get("title_source", "unknown")] += 1
            counts["description_" + module.get("description_source", "unknown")] += 1
            flags = module.get("naming_flags", [])
            counts.update("flag_" + flag for flag in flags)
            description_text = " ".join(str(row.get("text", "")) for row in module.get("description", []))
            if re.search(r"\b(?:module này|chương này|bài này|nội dung)\b", description_text, re.I):
                counts["banned_phrase_hit"] += 1
            if re.search(r"\b(?:module này|chương này|bài này|nội dung này|nội dung của (?:module|chương|bài))\b",
                         description_text, re.I):
                counts["self_reference"] += 1
                if len(self_reference_samples) < 6:
                    self_reference_samples.append({"doc_id": doc_id, "module_id": module["module_id"],
                                                   "description": description_text[:200]})
            if module.get("description_source") == "llm":
                nodes = {node["node_id"]: node for node in source.payload["nodes"]}
                names = {_display(nodes[node_id]).casefold() for node_id in module["node_ids"]}
                pieces = [piece.strip(" .;:") for row in module.get("description", [])
                          for piece in re.split(r",|\bvà\b", str(row.get("text", "")), flags=re.I)]
                if pieces and all(piece.casefold() in names for piece in pieces):
                    counts["list_only_llm_description"] += 1
            if module.get("description_source") == "template":
                key = tuple(sorted(module["node_ids"]))
                index, row = prepared_by_nodes[key]
                reply = replies[key]
                if "description_vocabulary" in flags and len(samples) < 4:
                    sentences = reply.get("description", [])
                    text = " ".join(str(sentence.get("text", "")) for sentence in sentences)
                    missing = sorted(set(_words(text)) - desc_vocabs[index])
                    if len(samples) < 3 or doc_id != "doc-1":
                        samples.append({"doc_id": doc_id, "module_id": module["module_id"],
                                        "retained_title": module["title"], "missing_syllables": missing,
                                        "rejected_description": text[:260]})
        aggregate.update(counts)
        doc_rows.append({"doc_id": doc_id, **dict(counts)})
    return {"status": result["status"], "modules": aggregate["modules"],
            "total_cost_usd": result.get("ledger_usd_final"),
            "transport_attempts": result.get("transport_attempts"),
            "transport_upper_bound_usd": result.get("transport_attempt_upper_bound_usd"),
            "title_llm": aggregate["title_llm"], "title_fallback": aggregate["title_fallback"],
            "description_llm": aggregate["description_llm"],
            "description_template": aggregate["description_template"],
            "self_reference_descriptions": aggregate["self_reference"],
            "descriptions_containing_prompt_banned_terms": aggregate["banned_phrase_hit"],
            "list_only_llm_descriptions": aggregate["list_only_llm_description"],
            "flags": {key.removeprefix("flag_"): count for key, count in aggregate.items()
                      if key.startswith("flag_")},
            "documents": doc_rows, "samples": samples,
            "self_reference_samples": self_reference_samples}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
