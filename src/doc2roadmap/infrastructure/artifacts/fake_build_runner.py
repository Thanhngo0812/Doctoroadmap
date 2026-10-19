from __future__ import annotations

import json
import shutil
from pathlib import Path

from doc2roadmap.application.phase_b.retrieval import load_learning_graph
from doc2roadmap.application.ports.build import BUILD_STEPS, BuildRejected, BuildResult
from doc2roadmap.application.use_cases.ingest_document import validate_doc_id
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


class FakeBuildRunner:
    """Copy known development artifacts under a new document ID without model calls."""

    SOURCES = {"doc-1", "xstk-ch3-1", "doc-4", "nhap-mon-ml", "naive-bayes", "doc-6"}
    ARTIFACTS = ("parse_tree", "chunks", "candidates", "canonical", "retrieval", "graph")
    REQUIRED = {"parse_tree", "chunks", "candidates", "canonical", "retrieval", "graph"}

    def __init__(self, artifact_dir: Path, source_doc_id: str,
                 pipeline_version: str = "fake-v1", recorder=None):
        if source_doc_id not in self.SOURCES:
            raise ValueError("fake source is not an approved development document")
        self.root = Path(artifact_dir)
        self.source_doc_id = source_doc_id
        self.pipeline_version = pipeline_version
        self.recorder = recorder

    def execute(self, file_path: Path, doc_id: str, *, language: str = "vi",
                progress=None, cancelled=None, dry_run: bool = False) -> BuildResult:
        result = BuildResult(doc_id, "failed", self.pipeline_version)
        stage = BUILD_STEPS[0]
        try:
            validate_doc_id(doc_id)
            if doc_id == self.source_doc_id:
                raise ValueError("target doc_id must differ from fake source")
            if language != "vi":
                raise BuildRejected("ngon_ngu_khong_ho_tro", f"unsupported language: {language}")
            for name in self.ARTIFACTS:
                if (self.root / name / doc_id).exists():
                    raise FileExistsError(f"artifacts already exist for {doc_id}")
            formula_target = self.root / "phase_b" / "formula_images" / doc_id
            if formula_target.exists():
                raise FileExistsError(f"formula image artifacts already exist for {doc_id}")
            sources = {name: self.root / name / self.source_doc_id for name in self.ARTIFACTS}
            required = {"parse_tree", "chunks"} if dry_run else self.REQUIRED
            missing = required - {name for name, path in sources.items() if path.is_dir()}
            if missing:
                raise FileNotFoundError(f"missing required source artifacts: {', '.join(sorted(missing))}")

            stages = {
                "doc_reading": ("parse_tree", "chunks"),
                "concepts": ("candidates", "canonical", "retrieval"),
                "graph": ("graph",),
                "learning_prep": (),
            }
            for index, stage in enumerate(BUILD_STEPS):
                if cancelled and cancelled():
                    result.status = "cancelled"
                    break
                self._progress(progress, stage, "started", {"remaining": list(BUILD_STEPS[index:])})
                for name in stages[stage]:
                    source = sources[name]
                    target = self.root / name / doc_id
                    if source.is_dir():
                        shutil.copytree(source, target)
                        for path in target.rglob("*.json"):
                            self._remap(path, self.source_doc_id, doc_id)
                result.completed_steps.append(stage)
                details = {"artifacts_copied": list(stages[stage])}
                if stage == "graph":
                    graph = load_learning_graph(JsonArtifactStore(self.root), doc_id)
                    result.graph_version = graph.payload["graph_version"]
                    details["graph_version"] = result.graph_version
                elif stage == "learning_prep":
                    source = self.root / "phase_b" / "formula_images" / self.source_doc_id
                    target = self.root / "phase_b" / "formula_images" / doc_id
                    if source.is_dir():
                        shutil.copytree(source, target)
                        for path in target.rglob("*.json"):
                            self._remap(path, self.source_doc_id, doc_id)
                        details["formula_images_copied"] = True
                    else:
                        details["formula_images_copied"] = False
                result.step_details[stage] = details
                self._progress(progress, stage, "completed", details)
                if stage == "learning_prep" and cancelled and cancelled():
                    result.status = "cancelled"
                    break
                if stage == "doc_reading" and dry_run:
                    result.status = "dry_run"
                    for remaining in BUILD_STEPS[index + 1:]:
                        following = BUILD_STEPS[BUILD_STEPS.index(remaining) + 1:]
                        self._progress(progress, remaining, "planned", {"remaining": list(following)})
                    break
            else:
                result.status = "succeeded"
        except BuildRejected as exc:
            result.status = "rejected"
            result.error = {"code": exc.code, "message": str(exc), "stage": stage, "retryable": False}
        except Exception as exc:
            result.status = "failed"
            result.error = {"code": "loi_noi_bo", "error_type": type(exc).__name__,
                            "message": str(exc), "stage": stage, "retryable": False}
        if self.recorder:
            self.recorder(result)
        return result

    @staticmethod
    def _progress(callback, step, status, details):
        if callback:
            callback(step, {"status": status, **details})

    @staticmethod
    def _remap(path: Path, source_doc_id: str, target_doc_id: str) -> None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return

        def update(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "doc_id" and child == source_doc_id:
                        value[key] = target_doc_id
                    else:
                        update(child)
            elif isinstance(value, list):
                for child in value:
                    update(child)

        update(payload)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
