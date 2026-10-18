"""Offline rule accounting for SA-29 against cached SA-28 replies."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from doc2roadmap.application.phase_b.naming import SCHEMA, _words
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import JsonPhaseBStore
from sa29_replay_support import Sa28RequestReplay, load_sa28_requests


ROOT = Path(__file__).resolve().parents[2]
PINS = {"doc-1": 52, "nhap-mon-ml": 37, "naive-bayes": 37,
        "doc-6": 24, "xstk-ch3-1": 63, "doc-4": 22}
CACHE = ROOT / "artifacts/phase_b/sa28-20261018.json"


def audit() -> dict:
    artifacts = JsonArtifactStore(Settings().artifact_dir)
    phase_store = JsonPhaseBStore(CACHE)
    settings = BSettings()
    recorded_prompt, recorded_requests = load_sa28_requests()
    totals = Counter()
    docs = []
    for doc_id, version in PINS.items():
        source = artifacts.load_graph(doc_id, version)
        use_case = Sa28RequestReplay(artifacts, object(), phase_b_store=phase_store, settings=settings,
                                     recorded_prompt=recorded_prompt, recorded_requests=recorded_requests)
        chunks, prepared = use_case._prepare(doc_id, source)
        description_vocabs, borrowed_vocabs = use_case._description_lexicons(chunks, prepared, source)
        nodes = {node["node_id"]: node for node in source.payload["nodes"]}
        chunk_text = {chunk.chunk_id: chunk.text for chunk in chunks.result.chunks}
        corpus = Counter(word for text in chunk_text.values() for word in _words(text))
        use_case._nodes = nodes
        use_case._function_words = {word for word, count in corpus.most_common(max(1, len(corpus) // 100))
                                    if count >= 3}
        frequent_threshold = max(3, settings.naming_common_chunk_ratio * len(chunk_text))
        document_frequency = Counter(word for text in chunk_text.values() for word in set(_words(text)))
        frequent = {word for word, count in document_frequency.items() if count >= frequent_threshold}
        prompt = use_case._prompt()
        model_id = settings.model_id
        all_titles = [module.get("title", "") for module in source.payload["modules"]]
        counts = Counter()
        for index, (module, _, data, title_vocab, fragments) in enumerate(prepared):
            key = context_hash({"doc_id": doc_id, "input": data, "prompt": prompt, "schema": SCHEMA,
                                "model": model_id, "temperature": settings.naming_temperature,
                                "max_output_tokens": settings.naming_max_output_tokens})
            reply = phase_store.get_cache(key)
            if not isinstance(reply, dict):
                raise RuntimeError(f"missing cached SA-28 response for {doc_id} module {index + 1}")
            title_ok = use_case._validate_title(reply, module, title_vocab, fragments, all_titles, index) is None
            description = reply.get("description")
            description_ok = use_case._validate_description(description, module, description_vocabs[index]) is None
            borrowed = bool(description_ok and any(word in borrowed_vocabs[index]
                                                   for sentence in description for word in _words(sentence["text"])))
            description_after_borrowing_ok = description_ok and not borrowed
            own_teaching = {word for node_id in module["node_ids"]
                            for chunk_id in nodes[node_id].get("teaching_chunk_ids", [])
                            for word in _words(chunk_text.get(chunk_id, ""))}
            historical_ok = use_case._validate(reply, module, title_vocab | own_teaching | frequent,
                                                fragments, all_titles, index) is None
            counts["modules"] += 1
            counts["title_only_pass"] += title_ok
            counts["description_only_pass_before_borrowing"] += description_ok
            counts["description_borrowed"] += borrowed
            counts["description_only_pass_after_borrowing"] += description_after_borrowing_ok
            counts["historical_combined_pass"] += historical_ok
            counts["title_and_description_pass_before_borrowing"] += title_ok and description_ok
            counts["title_and_description_pass_after_borrowing"] += title_ok and description_after_borrowing_ok
        totals.update(counts)
        docs.append({"doc_id": doc_id, **dict(counts)})
    return {"mode": "offline_cache_audit", "provider_calls": 0, "totals": dict(totals), "documents": docs}


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
