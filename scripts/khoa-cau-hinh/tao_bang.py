"""Sinh bảng khoá cấu hình cho vé 07 (T10): commit, mô hình, prompt_hash từng stage, tham số, đầu vào của tập giữ lại.

Chỉ đọc thiết lập không bí mật, chọn đích danh từng trường; không in `.env`. Ghi `task/v2-do-thi-lo-trinh/07b-cau-hinh-khoa.md`.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/khoa-cau-hinh/tao_bang.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.prerequisite_prompt import (  # noqa: E402
    main_prompt_hash,
    provenance_prompt_hash,
    secondary_prompt_hash,
)
from doc2roadmap.application.use_cases import anchor_concepts, judge_identity  # noqa: E402
from doc2roadmap.application.use_cases.anchor_concepts import AnchorConcepts, anchor_prompt_hash  # noqa: E402
from doc2roadmap.domain.sequence import DEFAULT_WEIGHTS  # noqa: E402
from doc2roadmap.application.use_cases.judge_identity import JudgeIdentity, identity_prompt_hash  # noqa: E402
from doc2roadmap.composition import build_learning_graph  # noqa: E402

SETTINGS = ("extraction_model_id", "merge_model_id", "description_model_id", "embedding_model_id", "embedding_dimensions",
            "roadmap_model_id", "topic_neighbors", "topic_edge_quantile", "topic_resolution", "topic_seed",
            "topic_cluster_cap", "mention_dense_top_k", "mention_dense_min_z", "mention_pair_cluster_top_k",
            "roadmap_single_session_limit", "roadmap_stage_cap", "extraction_max_output_tokens")
HELD_OUT = ("xstk-ch3-1", "doc-4")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, encoding="utf-8", check=True).stdout.strip()


def main():
    pipeline, settings = build_learning_graph()
    store = pipeline.teaching.store
    generation = {"temperature": 0.0, "max_output_tokens": settings.extraction_max_output_tokens}
    model_id = settings.roadmap_model_id
    anchor_generation = AnchorConcepts(store, None).generation
    identity_generation = JudgeIdentity(store, None).generation
    dirty = git("status", "--porcelain", "--untracked-files=no")
    lines = [
        "# 07b — Cấu hình khoá cho lần chạy tập giữ lại (T10)", "",
        "Sinh bởi `scripts/khoa-cau-hinh/tao_bang.py`. Chủ dự án duyệt bảng này trước bước 2 của vé 07; từ lúc duyệt, mọi thay đổi",
        "là hậu kiểm, báo tách riêng.", "",
        "## Mã", "",
        f"- commit: `{git('rev-parse', 'HEAD')}` ({git('log', '-1', '--format=%cs %s')[:90]})",
        f"- cây làm việc: {'**có thay đổi chưa commit**' if dirty else 'sạch (chỉ tính tệp đã theo dõi)'}",
        "- chuỗi mặc định: clusters → mentions → provenance → edges (chính + phụ) → validated → teaching (neo C8 v3) → "
        "identity → stages (A10 neo sách)", "",
        "## Mô hình và tham số (thiết lập không bí mật)", "",
        "| thiết lập | giá trị |", "|---|---|",
        *[f"| `{name}` | `{getattr(settings, name)}` |" for name in SETTINGS],
        "", "## prompt_hash từng stage (mô hình và generation đúng như chuỗi mặc định)", "",
        "| stage | prompt_hash |", "|---|---|",
        f"| provenance | `{provenance_prompt_hash(model_id, generation)}` |",
        f"| edges — pass chính | `{main_prompt_hash(model_id, generation)}` |",
        f"| edges — pass phụ | `{secondary_prompt_hash(model_id, generation)}` |",
        f"| teaching — neo C8 v3 | `{anchor_prompt_hash(model_id, anchor_generation)}` |",
        f"| identity | `{identity_prompt_hash(model_id, identity_generation)}` |",
        "", "## Luật cố định trong mã", "",
        f"- neo: {anchor_concepts.CANDIDATES} câu ứng viên, luật gom `nfkc-latex-dash-name+a3-evidence+symbolic-whole-doc`;"
        f" generation {anchor_generation}",
        f"- danh tính: gộp nhóm đã kiểm đủ (`verified-clique-v1`); quyết định người: {sorted(judge_identity.HUMAN_VERDICT)};"
        f" generation {identity_generation}",
        f"- A10: trọng số chia module {DEFAULT_WEIGHTS}; trần module {settings.roadmap_stage_cap}", "",
        "## Đầu vào đã có của tập giữ lại", "",
        "| tài liệu | chunks | candidates (A3) | canonical (A4/A5) |", "|---|---|---|---|",
    ]
    for doc in HELD_OUT:
        chunks = store.load_latest_chunks(doc)
        canonical = store.load_latest_canonical(doc)
        candidates = store.load_candidates(doc, canonical.manifest["upstream_version"])
        parser = chunks.manifest.get("config", {}).get("parser", {})
        lines.append(f"| {doc} | v{chunks.version} (`{parser.get('adapter')}`) | v{candidates.version} | v{canonical.version} |")
    lines += ["", "Ngưỡng: bảng *Tiêu chí nghiệm thu đã chốt* của spec v2 (Q1–Q10 và Q7b, bản tại commit trên).", ""]
    out = Path("task/v2-do-thi-lo-trinh/07b-cau-hinh-khoa.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out}: {len(lines)} dòng")


if __name__ == "__main__":
    main()
