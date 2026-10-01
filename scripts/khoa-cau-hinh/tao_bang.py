"""Sinh bảng khoá cấu hình (T10) cho lần chạy tập giữ lại 07 v2 trên chuỗi v3.

Gồm: commit, mô hình, tham số, prompt_hash từng stage, đầu vào đã có và SHA-256 tệp nhãn của tập giữ lại. Chỉ đọc thiết lập không bí mật,
chọn đích danh từng trường; không in `.env`. Tệp nhãn giữ lại chỉ được **băm**, không mở nội dung.
Bản khoá: `task/v3-lo-trinh-doc-duoc/T10-cau-hinh-khoa.md`. `--nhap` ghi bản nháp vào `tmp/` (chưa phải lúc khoá).
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/khoa-cau-hinh/tao_bang.py [--nhap]
"""
import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.prerequisite_prompt import (  # noqa: E402
    main_prompt_hash,
    provenance_prompt_hash,
    secondary_prompt_hash,
)
from doc2roadmap.application.prompt_library import load_prompt  # noqa: E402
from doc2roadmap.application.use_cases import anchor_concepts, judge_identity  # noqa: E402
from doc2roadmap.application.use_cases.anchor_concepts import PRIOR_SCHEMA, AnchorConcepts, anchor_prompt_hash  # noqa: E402
from doc2roadmap.application.use_cases.judge_identity import VERIFY_SCHEMA, JudgeIdentity, identity_prompt_hash  # noqa: E402
from doc2roadmap.application.use_cases.label_chunk_roles import ROLE_SCHEMA  # noqa: E402
from doc2roadmap.application.use_cases.name_concept_labels import DISPLAY_SCHEMA  # noqa: E402
from doc2roadmap.application.use_cases.name_modules import GENERATION as TITLE_GENERATION  # noqa: E402
from doc2roadmap.application.use_cases.name_modules import SCHEMA as TITLE_SCHEMA  # noqa: E402
from doc2roadmap.composition import build_learning_graph  # noqa: E402
from doc2roadmap.domain.canonical import digest  # noqa: E402
from doc2roadmap.domain.sequence import DEFAULT_WEIGHTS  # noqa: E402

SETTINGS = ("extraction_model_id", "merge_model_id", "description_model_id", "embedding_model_id", "embedding_dimensions",
            "roadmap_model_id", "topic_neighbors", "topic_edge_quantile", "topic_resolution", "topic_seed",
            "topic_cluster_cap", "mention_dense_top_k", "mention_dense_min_z", "mention_pair_cluster_top_k",
            "roadmap_single_session_limit", "roadmap_stage_cap", "extraction_max_output_tokens",
            "a8_definition_before", "a8_definition_after")
# Đường gọi và độ song song không đổi kết quả hay khoá cache (vé 19); ghi để kiểm toán.
NOT_METHOD = ("llm_transport", "vertex_location", "vertex_concurrency", "roadmap_concurrency")
HELD_OUT = ("xstk-ch3-1", "doc-4")
HELD_OUT_LABELS = ("xstk-ch3-1-chuong-10-13-*", "doc-4-chuong-8-*")
CHAIN = ("vai trò vùng (A2, `label-roles`) → clusters → mentions → provenance → teaching (neo C8 v3, vé 05/05b) → identity (vé 10b) → "
         "edges chính → edges phụ (hợp đồng cửa sổ định nghĩa, vé 12) → validated (A9) → concept_labels (vé 11/11b) → stages (A10 neo "
         "sách, vé 07/08/09c/18) → module_titles (vé 09–09d)")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, encoding="utf-8", check=True).stdout.strip()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    draft = "--nhap" in sys.argv
    pipeline, settings = build_learning_graph()
    store = pipeline.teaching.store
    model_id = settings.roadmap_model_id
    generation = {"temperature": 0.0, "max_output_tokens": settings.extraction_max_output_tokens}
    anchor_generation = AnchorConcepts(store, None).generation
    identity_generation = JudgeIdentity(store, None).generation
    label_generation = {"temperature": 0.0, "max_output_tokens": 512}
    dirty = git("status", "--porcelain", "--untracked-files=no")
    hashes = [
        ("vai trò vùng (A2)", digest([load_prompt("a2", "region-roles"), ROLE_SCHEMA])),
        ("provenance (A7)", provenance_prompt_hash(model_id, generation)),
        ("teaching — neo C8 v3", anchor_prompt_hash(model_id, anchor_generation)),
        ("teaching — kiểm kiến thức nền", digest([load_prompt("a10", "prior_verify"), PRIOR_SCHEMA, model_id, anchor_generation])),
        ("identity — lượt 1", identity_prompt_hash(model_id, identity_generation)),
        ("identity — lượt xác minh", digest([load_prompt("a10", "identity_verify"), VERIFY_SCHEMA, model_id, identity_generation])),
        ("edges — pass chính", main_prompt_hash(model_id, generation)),
        ("edges — pass phụ", secondary_prompt_hash(model_id, generation)),
        ("concept_labels", digest([load_prompt("a10", "display_name"), DISPLAY_SCHEMA, model_id, label_generation])),
        ("module_titles", digest([load_prompt("a10", "module_title"), TITLE_SCHEMA, model_id, TITLE_GENERATION])),
    ]
    lines = [
        "# T10 — Cấu hình khoá cho lần chạy tập giữ lại 07 v2 (chuỗi v3)", "",
        "Sinh bởi `scripts/khoa-cau-hinh/tao_bang.py`" + (" — **BẢN NHÁP, chưa phải bản khoá**." if draft else "."),
        "Chủ dự án duyệt bảng này trước bước chạy của [giao thức](T10-07v2-giao-thuc-tap-giu-lai.md); từ lúc duyệt, mọi thay đổi là",
        "hậu kiểm, báo tách riêng, không thay kết quả tập giữ lại.", "",
        "## Mã", "",
        f"- commit: `{git('rev-parse', 'HEAD')}` ({git('log', '-1', '--format=%cs %s')[:90]})",
        f"- cây làm việc: {'**có thay đổi chưa commit — không được khoá ở trạng thái này**' if dirty else 'sạch (chỉ tính tệp đã theo dõi)'}",
        f"- chuỗi: {CHAIN}", "",
        "## Mô hình và tham số (thiết lập không bí mật)", "",
        "| thiết lập | giá trị |", "|---|---|",
        *[f"| `{name}` | `{getattr(settings, name)}` |" for name in SETTINGS],
        "", "Không thuộc phương pháp (không đổi kết quả hay khoá cache), ghi để kiểm toán: " +
        ", ".join(f"`{name}={getattr(settings, name, None)}`" for name in NOT_METHOD) + ".",
        "", "## prompt_hash từng stage (mô hình và generation đúng như chuỗi mặc định)", "",
        "| stage | prompt_hash |", "|---|---|",
        *[f"| {stage} | `{value}` |" for stage, value in hashes],
        "", "Lúc khoá, đối chiếu với `prompt_hash` ghi trong manifest của lượt nghiệm thu vé 12 trên tài liệu phát triển: lệch là dừng.",
        "", "## Luật cố định trong mã", "",
        f"- neo: {anchor_concepts.CANDIDATES} câu ứng viên; generation {anchor_generation}",
        f"- danh tính: gộp nhóm đã kiểm đủ; quyết định người: {sorted(judge_identity.HUMAN_VERDICT)}; generation {identity_generation}",
        f"- A8: cửa sổ định nghĩa = câu neo, {settings.a8_definition_before} câu trước, {settings.a8_definition_after} câu sau, trong cùng đoạn của "
        "chunk neo; chỉ `can_de_hieu` là cạnh cứng",
        f"- A10: trọng số chia module {DEFAULT_WEIGHTS}; trần module {settings.roadmap_stage_cap}", "",
        "## Đầu vào đã có của tập giữ lại (dùng lại — bộ vàng gắn với canonical này)", "",
        "| tài liệu | chunks | candidates (A3) | canonical (A4/A5) |", "|---|---|---|---|",
    ]
    for doc in HELD_OUT:
        chunks = store.load_latest_chunks(doc)
        canonical = store.load_latest_canonical(doc)
        candidates = store.load_candidates(doc, canonical.manifest["upstream_version"])
        parser = chunks.manifest.get("config", {}).get("parser", {})
        lines.append(f"| {doc} | v{chunks.version} (`{parser.get('adapter')}`) | v{candidates.version} | v{canonical.version} |")
    lines += ["", "## Tệp nhãn của tập giữ lại (chỉ băm, không mở)", "", "| tệp | SHA-256 |", "|---|---|"]
    for pattern in HELD_OUT_LABELS:
        for path in sorted(Path("artifacts/a8-gold").glob(pattern)):
            lines.append(f"| `{path.name}` | `{sha256(path)}` |")
    blind = Path("artifacts/a8-gold/liet-ke-mu-giu-lai.md")
    if blind.exists():
        lines.append(f"| `{blind.name}` (T13) | `{sha256(blind)}` |")
    lines.append("")
    out = Path("tmp/T10-cau-hinh-khoa-nhap.md") if draft else Path("task/v3-lo-trinh-doc-duoc/T10-cau-hinh-khoa.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out}: {len(lines)} dòng")


if __name__ == "__main__":
    main()
