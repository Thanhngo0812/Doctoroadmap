"""Read-only audit of doc-6 caches; all writes go to a new temporary store."""
import json
import shutil
import sqlite3
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from doc2roadmap.composition_build import build_document_runner
from doc2roadmap.config import Settings
from doc2roadmap.application.use_cases.label_chunk_roles import LabelChunkRoles
from doc2roadmap.application.use_cases.extract_entities import _build_contexts


root = Path.cwd()
target = Path(tempfile.mkdtemp(prefix="w13-cache-audit-", dir=root / "tmp"))
source = root / "artifacts"
for kind in ("parse_tree", "chunks", "candidates", "retrieval", "canonical", "graph", "checkpoints/graph"):
    folder = source / kind / "doc-6"
    if folder.exists():
        shutil.copytree(folder, target / "artifacts" / kind / "doc-6")

with ExitStack() as stack:
    guards = [stack.enter_context(patch(name, side_effect=AssertionError("network forbidden"))) for name in (
        "doc2roadmap.infrastructure.llm.gemini.urlopen",
        "doc2roadmap.infrastructure.embedding.gemini.urlopen",
        "doc2roadmap.infrastructure.google_auth.VertexCredentials.headers",
    )]
    settings = Settings(_env_file=None, artifact_dir=target / "artifacts",
                        llm_transport="vertex", vertex_project="offline-acceptance")
    runner = build_document_runner(settings)
    result = runner.execute(root / "doc-6.pdf", "doc-6")
    pipeline = runner.pipeline
    stored = pipeline.store.load_latest_chunks("doc-6")
    model = pipeline._extractor(settings.roadmap_model_id, temperature=0, max_output_tokens=16384)
    roles = LabelChunkRoles(pipeline.store, model).plan("doc-6")
    contexts = _build_contexts(pipeline.store, stored)
    with sqlite3.connect(settings.artifact_dir / "builds.sqlite3") as connection:
        ledger = connection.execute("SELECT status, model_calls, spent_usd FROM build_runs").fetchall()
    assert result.status == "failed" and result.error["error_type"] == "SpendNotAllowed"
    assert result.completed_steps == ["doc_reading"]
    assert result.model_calls == result.spent_usd == 0
    assert all(guard.call_count == 0 for guard in guards)
    assert roles.status == "run"
    row = {"scratch_root": str(target), "result": result.to_dict(), "role_plan": roles.to_dict(),
           "new_chunk_version": stored.version, "new_chunk_config_hash": stored.manifest["config_hash"],
           "new_section_count": len(stored.result.sections), "new_chunk_count": len(stored.result.chunks),
           "a3_context_count": len(contexts), "a3_image_count": sum(len(c.images) for c in contexts),
           "database_rows": ledger, "network_attempts": sum(g.call_count for g in guards)}
    print(json.dumps(row, ensure_ascii=False, indent=2))
    (target / "audit.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
