"""Offline v4-01 acceptance: recorded replies only, no transport or credentials."""
import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.domain.canonical import digest
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges
from doc2roadmap.application.use_cases.validate_graph import ValidateGraph
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
from doc2roadmap.application.use_cases.name_modules import NameModules


class RecordedModel:
    def __init__(self, model_id, rows):
        self.model_id = model_id
        self.rows = {digest(row["input"]): row for row in rows}
        self.calls = 0

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        key = digest(data)
        if key not in self.rows:
            previous = next((row["input"] for row in self.rows.values()
                             if row["input"].get("session_id") == data.get("session_id")), {})
            differences = [field for field in data.get("dossier", {})
                           if data["dossier"][field] != previous.get("dossier", {}).get(field)]
            raise AssertionError("Unrecorded input: " + data.get("session_id", str(data)) + " changed: " + str(differences))
        row = self.rows[key]
        self.calls += 1
        return SimpleNamespace(payload=row.get("output", row.get("last_output", {})))


class ReplayStore(JsonArtifactStore):
    def __init__(self, root, version):
        super().__init__(root)
        self.version, self.saved = version, {}

    def load_chunks(self, doc_id, version):
        if (self.root / "chunks" / doc_id / f"v{version}").exists():
            return super().load_chunks(doc_id, version)
        return JsonArtifactStore(Path("artifacts")).load_chunks(doc_id, version)

    def load_role_chunks(self, doc_id, version):
        if not (self.root / "chunks" / doc_id).exists():
            return JsonArtifactStore(Path("artifacts")).load_role_chunks(doc_id, version)
        return super().load_role_chunks(doc_id, version)

    def load_canonical(self, doc_id, version):
        if not (self.root / "canonical" / doc_id / f"v{version}").exists():
            return JsonArtifactStore(Path("artifacts")).load_canonical(doc_id, version)
        return super().load_canonical(doc_id, version)

    def find_graph(self, *args):
        return None

    def load_checkpoint(self, *args):
        return None

    def save_checkpoint(self, *args):
        pass

    def clear_checkpoint(self, *args):
        pass

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.version += 1
        artifact = SimpleNamespace(payload=payload, version=self.version, path=None,
            manifest={"config": config, "config_hash": config_hash,
                      "source_hash": source_hash, "upstream_version": kwargs["upstream_version"]})
        self.saved[self.version] = artifact
        return artifact

    def load_graph(self, doc_id, version):
        if version in self.saved:
            return self.saved[version]
        if self.root != Path("artifacts"):
            return JsonArtifactStore(Path("artifacts")).load_graph(doc_id, version)
        if not (self.root / "graph" / doc_id / f"v{version}").exists():
            return JsonArtifactStore(Path("artifacts")).load_graph(doc_id, version)
        return super().load_graph(doc_id, version)


def replay(root, doc_id, secondary_version, concurrency, window_pairs=None):
    original = JsonArtifactStore(root)
    old = original.load_graph(doc_id, secondary_version)
    main = original.load_graph(doc_id, old.manifest["upstream_version"])
    final = original.load_graph(doc_id, secondary_version + 4)
    store = ReplayStore(root, main.version)
    model = RecordedModel(old.manifest["config"]["model_id"], old.payload["decision_log"])
    new, _ = BuildSecondaryEdges(store, model, concurrency=concurrency,
        window_pairs=window_pairs or old.manifest.get("execution_limits", {}).get("window_pairs", 1),
        generation=old.manifest["config"]["generation"]).execute(doc_id, upstream=main)
    assert new.payload["secondary_edges"] == old.payload["secondary_edges"], "secondary_edges changed"
    old_flags = Counter(digest(row) for row in old.payload["secondary_flags"])
    new_flags = Counter(digest(row) for row in new.payload["secondary_flags"])
    assert not (new_flags - old_flags), "new secondary flags"
    left_final = {row["input"]["session_id"].removeprefix("secondary_").removesuffix("_left")
               for row in old.payload["decision_log"]
               if row["input"]["session_id"].endswith("_left") and row.get("valid")
               and row.get("output", {}).get("decision") != "create"}
    left_no = {row["input"]["session_id"].removeprefix("secondary_").removesuffix("_left")
               for row in old.payload["decision_log"]
               if row["input"]["session_id"].endswith("_left") and row.get("valid")
               and row.get("output", {}).get("decision") == "no_direct_relation"}
    right_invalid = {row["input"]["session_id"].removeprefix("secondary_").removesuffix("_right")
                     for row in old.payload["decision_log"]
                     if row["input"]["session_id"].endswith("_right") and not row.get("valid")}
    allowed_flags = Counter(digest(row) for row in old.payload["secondary_flags"]
                            if row.get("kind") == "outside_or_invalid_secondary_edge"
                            and row.get("pair_id") in left_final & right_invalid)
    unexpected = (old_flags - new_flags) - allowed_flags
    assert not unexpected, "unexpected removed flags: " + str([
        (row, [item.get("output", {}).get("decision") for item in old.payload["decision_log"]
               if row.get("pair_id", "MISSING") in item["input"]["session_id"]])
        for row in old.payload["secondary_flags"] if digest(row) in unexpected])
    validated, _ = ValidateGraph(store).execute(doc_id, upstream=new)
    labels_model = RecordedModel(model.model_id, final.payload.get("concept_display_name_decision_log", []))
    labeled, _ = NameConceptLabels(store, labels_model, concurrency=concurrency).execute(doc_id, upstream=validated)
    original_roadmap = original.load_graph(doc_id, secondary_version + 3)
    roadmap_type = BuildRoadmap
    if original_roadmap.manifest["config"]["algorithm_id"] == "a10-book-anchored-sequence-v2":
        # These artifacts predate tickets 20/21. Freeze downstream A10 so the
        # acceptance isolates v4-01, rather than measuring the unrelated v2 -> v3 placement change.
        namespace = {"__name__": "doc2roadmap.application.use_cases.build_roadmap"}
        source = subprocess.check_output(["git", "show", "4e358ae:src/doc2roadmap/application/use_cases/build_roadmap.py"], encoding="utf-8")
        exec(compile(source, "historical-a10-v2", "exec"), namespace)
        roadmap_type = namespace["BuildRoadmap"]
    roadmap, _ = roadmap_type(store, stage_cap=original_roadmap.manifest["config"]["module_cap"]).execute(doc_id, upstream=labeled)
    title_model = RecordedModel(model.model_id, final.payload.get("module_title_decision_log", []))
    title_type = NameModules
    original_titles = final.payload.get("module_title_decision_log", [])
    if original_titles and not any("numbering_only" in row["input"] for row in original_titles):
        namespace = {"__name__": "doc2roadmap.application.use_cases.name_modules"}
        source = subprocess.check_output(["git", "show", "4e358ae:src/doc2roadmap/application/use_cases/name_modules.py"], encoding="utf-8")
        exec(compile(source, "historical-module-titles", "exec"), namespace)
        title_type = namespace["NameModules"]
    named, _ = title_type(store, title_model, concurrency=concurrency).execute(doc_id, upstream=roadmap)
    for key in ("sequence", "requires_edges", "modules"):
        assert named.payload[key] == final.payload[key], key + " changed"
    return {"doc_id": doc_id, "secondary_edges_identical": True, "downstream_identical": True,
            "old_records": len(old.payload["decision_log"]),
            "new_records": len(new.payload["decision_log"]),
            "removed_flags": sum((old_flags - new_flags).values()),
            "removed_flags_other_noncreate": sum(1 for row in old.payload["secondary_flags"]
                if digest(row) in old_flags - new_flags and row.get("pair_id") not in left_no),
            "a10_algorithm": original_roadmap.manifest["config"]["algorithm_id"],
            "model_calls_replayed": model.calls, "usd": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("doc_id")
    parser.add_argument("secondary_version", type=int)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--window-pairs", type=int)
    args = parser.parse_args()
    print(json.dumps(replay(args.root, args.doc_id, args.secondary_version, args.concurrency, args.window_pairs), ensure_ascii=False))
