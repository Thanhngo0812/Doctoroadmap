"""Restore exact, unchanged SA-28 requests for offline SA-29 validation replays."""
from __future__ import annotations

import json
from pathlib import Path

from doc2roadmap.application.phase_b.naming import NameModulesB


ROOT = Path(__file__).resolve().parents[2]
RECORDING = ROOT / "artifacts/phase_b/recordings/sa28-20261018/module_title.json"


def load_sa28_requests() -> tuple[str, dict[tuple[str, ...], dict]]:
    fixture = json.loads(RECORDING.read_text(encoding="utf-8"))
    requests = {}
    prompts = set()
    for session in fixture["sessions"]:
        prompts.add(session["system_prompt"])
        for call in session["calls"]:
            value = json.loads(call["prompt"])
            node_ids = tuple(sorted(item["node_id"] for item in value["concepts"]))
            requests[node_ids] = value
    if len(prompts) != 1:
        raise RuntimeError(f"expected one unchanged SA-28 system prompt, found {len(prompts)}")
    if len(requests) != 160:
        raise RuntimeError(f"expected 160 unique SA-28 requests, found {len(requests)}")
    return next(iter(prompts)), requests


class Sa28RequestReplay(NameModulesB):
    def __init__(self, *args, recorded_prompt, recorded_requests, split_only=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._recorded_prompt = recorded_prompt
        self._recorded_requests = recorded_requests
        self._split_only = split_only

    def _prepare(self, doc_id, upstream):
        chunks, prepared = super()._prepare(doc_id, upstream)
        restored = []
        for module, fallback, _, vocabulary, fragments in prepared:
            key = tuple(sorted(module["node_ids"]))
            try:
                data = self._recorded_requests[key]
            except KeyError as error:
                raise RuntimeError(f"SA-28 request is missing for {doc_id} {key}") from error
            restored.append((module, fallback, data, vocabulary, fragments))
        return chunks, restored

    def _prompt(self):
        return self._recorded_prompt

    def _description_lexicons(self, chunks, prepared, upstream):
        if self._split_only:
            return ([row[3] for row in prepared], [set() for _ in prepared])
        return super()._description_lexicons(chunks, prepared, upstream)
