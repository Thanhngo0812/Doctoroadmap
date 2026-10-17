"""Cổng 19l: kiểm doc-1 canonical v5 (sinh từ thư mục làm việc trước commit) có tái lập được bằng mã commit đã ghim không.

Chép kho chính của doc-1 (không có canonical v5, không có graph) sang tmp/v4-19l/tai-lap/kho, chạy A4 chuỗi gộp bằng mã worktree sạch
tmp/v4-19l/ma. Mọi lời gọi mô hình phải có sẵn trong nhật ký của v5 (tái dùng theo input_hash, kể cả lời kết thúc sai schema); thiếu một lời
là dừng, nên không tốn USD mô hình. Embedding tên vẫn gọi thật (vài trăm tên ngắn). So payload với v5, bỏ các trường chỉ khác do tái dùng.
Chạy từ gốc repo: .venv/Scripts/python.exe scripts/gop-khau/cong-19l/tai_lap_doc1.py
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
WT = ROOT / "tmp/v4-19l/ma"
sys.path.insert(0, str(WT / "src"))
import doc2roadmap  # noqa: E402
assert Path(doc2roadmap.__file__).resolve().is_relative_to(WT.resolve()), doc2roadmap.__file__

DOC, MAIN = "doc-1", ROOT / "artifacts"
KHO = ROOT / "tmp/v4-19l/tai-lap/kho"
if KHO.exists():
    shutil.rmtree(KHO)
for kind in ("candidates", "chunks", "parse_tree", "retrieval"):
    shutil.copytree(MAIN / kind / DOC, KHO / kind / DOC)
for version in range(1, 5):
    shutil.copytree(MAIN / "canonical" / DOC / f"v{version}", KHO / "canonical" / DOC / f"v{version}")
v5 = json.loads((MAIN / "canonical" / DOC / "v5" / "canonical.json").read_text(encoding="utf-8"))
replay = {row["input_hash"]: row for key in ("decision_log", "anchor_decision_log", "anchor_prior_verify_decision_log")
          for row in v5.get(key, []) if "input_hash" in row}

from doc2roadmap.application import model_calls  # noqa: E402
from doc2roadmap.domain.canonical import digest  # noqa: E402
original = model_calls.run_model_jobs
missing = []


def strict(jobs, previous_log, **kwargs):
    jobs = list(jobs)
    for job in jobs:
        key = digest([job.model.model_id, job.prompt_hash, job.data])
        if key not in replay:
            missing.append({"stage": job.stage, "key": key})
    if missing:
        raise SystemExit(f"lời gọi không có trong nhật ký v5: {missing[:5]} (tổng {len(missing)})")
    rows = [replay[digest([j.model.model_id, j.prompt_hash, j.data])] for j in jobs]
    return original(jobs, [*previous_log, *(r for r in rows if r.get("valid"))], **kwargs,
                    **({} if "completed_log" in kwargs else {"completed_log": [r for r in rows if r.get("valid") is False]}))


import importlib  # noqa: E402
for name in ("anchor_core", "use_cases.canonical_describe", "use_cases.canonical_merge_verify", "use_cases.canonical_reasoning",
             "use_cases.canonical_repairs", "use_cases.check_teaching"):
    module = importlib.import_module("doc2roadmap.application." + name)
    if getattr(module, "run_model_jobs", None) is original:
        module.run_model_jobs = strict

os.environ["DOC2ROADMAP_ARTIFACT_DIR"] = str(KHO)
from doc2roadmap.application.use_cases.a4_gold import load_gold  # noqa: E402
from doc2roadmap.composition import build_canonical  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402
gold = load_gold(MAIN / "a4-gold.json", JsonArtifactStore(MAIN), require_complete=True)
assert DOC not in gold["documents"]
use_case = build_canonical(upstream_chain="gop", allow_spend=True)
artifact, reused = use_case.execute(DOC, a4_gold_coverage="none", gold_sheet_id=gold["sheet_id"], declared_language="vi")
new = artifact.payload
volatile = {"reused", "origin_version"}
clean = lambda rows: [{k: v for k, v in row.items() if k not in volatile} for row in rows]  # noqa: E731
result = {"commit": "f4871fd83aa8169d771b8cbfe40d0a61d7baf56a", "reused_artifact": reused, "new_version": artifact.version,
          "keys_only_in_v5": sorted(set(v5) - set(new)), "keys_only_in_new": sorted(set(new) - set(v5)), "same": {}, "missing_calls": len(missing)}
for key in sorted(set(v5) & set(new)):
    if key.endswith("decision_log"):
        result["same"][key] = clean(v5[key]) == clean(new[key])
    else:
        result["same"][key] = digest(v5[key]) == digest(new[key])
result["config_hash_same"] = artifact.manifest["config_hash"] == json.loads(
    (MAIN / "canonical" / DOC / "v5" / "manifest.json").read_text(encoding="utf-8"))["config_hash"]
(ROOT / "tmp/v4-19l/tai-lap/ket-qua.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
