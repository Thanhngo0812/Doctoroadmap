"""Vé 22: phát lại pass phụ B=50 từ nhật ký thật, tuyệt đối không gọi mạng."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/doc-lo-trinh")

from chay_danh_tinh_v3 import EvaluationStore  # noqa: E402
from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges  # noqa: E402
from doc2roadmap.domain.canonical import digest  # noqa: E402
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402


ROOT = Path("artifacts/v3-r12-final-evaluation")
DOCS = ("doc-3", "nhap-mon-ml")


class SpeculativeMissModel:
    model_id = "gemini-3.1-flash-lite"

    def __init__(self, old_log):
        self.calls, self.known_invalid = [], 0
        self.old = {json.dumps(row.get("input"), ensure_ascii=False, sort_keys=True): row
                    for row in old_log if isinstance(row.get("input"), dict)}

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        old = self.old.get(json.dumps(data, ensure_ascii=False, sort_keys=True))
        if old is not None:
            self.known_invalid += 1
            return SimpleNamespace(payload=old.get("last_output", {}))
        self.calls.append(data)
        return SimpleNamespace(payload={"pair_id": data["dossier"]["pair_id"], "decision": "defer",
                                        "reason": "speculative_cache_miss",
                                        "flags": [{"kind": "speculative_cache_miss"}]})


def replay(doc_id, temporary_root):
    main = JsonArtifactStore(ROOT).load_graph(doc_id, 1)
    expected = JsonArtifactStore(ROOT).load_graph(doc_id, 2)
    output = JsonArtifactStore(temporary_root)
    store = EvaluationStore(JsonArtifactStore(Path("artifacts")), output)
    model = SpeculativeMissModel(expected.payload["decision_log"])
    use_case = BuildSecondaryEdges(store, model, concurrency=100, window_pairs=50,
                                   generation=main.manifest["config"]["generation"])
    plan = use_case.plan(doc_id, upstream=main)
    output.save_checkpoint(doc_id, plan.checkpoint_id, {
        "source_hash": digest(main.payload),
        "completed_secondary_pairs": [], "secondary_edges": [], "secondary_flags": [],
        "decision_log": expected.payload["decision_log"],
        "executor_log": list(main.payload.get("executor_log", [])), "secondary_log": [],
        "secondary_model_metrics": {},
    })
    actual, _ = use_case.execute(doc_id, upstream=main)
    assert actual.payload["secondary_edges"] == expected.payload["secondary_edges"]
    if actual.payload["secondary_log"] != expected.payload["secondary_log"]:
        mismatch = next((index for index, rows in enumerate(zip(actual.payload["secondary_log"],
                                                                 expected.payload["secondary_log"], strict=True))
                         if rows[0] != rows[1]), None)
        raise AssertionError((doc_id, mismatch, actual.payload["secondary_log"][mismatch],
                              expected.payload["secondary_log"][mismatch]))
    assert not [flag for flag in actual.payload["secondary_flags"] if flag.get("kind") == "speculative_cache_miss"]
    cached_calls = sum(row.get("valid", False) for row in expected.payload["decision_log"])
    miss_rate = len(model.calls) / max(cached_calls, 1)
    assert miss_rate <= .01, (doc_id, len(model.calls), cached_calls)
    return {"doc_id": doc_id, "cache_miss_calls": len(model.calls), "cached_calls": cached_calls,
            "miss_rate": miss_rate, "edges": len(actual.payload["secondary_edges"])}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with TemporaryDirectory(prefix="doc2roadmap-r22-") as directory:
        for doc_id in DOCS:
            print(json.dumps(replay(doc_id, Path(directory)), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
