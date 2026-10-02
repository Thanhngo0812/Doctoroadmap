"""Sinh bảng khoá cấu hình (T10) cho lần chạy tập giữ lại 07 v2 trên chuỗi v3.

Gồm: commit, mô hình, tham số, prompt_hash từng stage, đầu vào đã có và SHA-256 tệp nhãn của tập giữ lại. Chỉ đọc thiết lập không bí mật,
chọn đích danh từng trường; không in `.env`. Tệp nhãn giữ lại chỉ được **băm**, không mở nội dung.
Bản khoá: `task/v3-lo-trinh-doc-duoc/T10-cau-hinh-khoa.md`. `--nhap` ghi bản nháp vào `tmp/` (chưa phải lúc khoá).
So `prompt_hash` với manifest lượt nghiệm thu vé 12; bản khoá thật từ chối ghi (mã thoát 1) khi lệch hoặc mã chạy chưa commit.
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
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402

SETTINGS = ("extraction_model_id", "merge_model_id", "description_model_id", "embedding_model_id", "embedding_dimensions",
            "roadmap_model_id", "topic_neighbors", "topic_edge_quantile", "topic_resolution", "topic_seed",
            "topic_cluster_cap", "mention_dense_top_k", "mention_dense_min_z", "mention_pair_cluster_top_k",
            "roadmap_single_session_limit", "roadmap_stage_cap", "extraction_max_output_tokens",
            "a8_definition_before", "a8_definition_after")
# Đường gọi, độ song song và bộ giới hạn không đổi kết quả hay khoá cache (vé 19, vé 22 phát lại y hệt); ghi để kiểm toán.
NOT_METHOD = ("llm_transport", "vertex_location", "vertex_concurrency", "roadmap_concurrency", "llm_max_in_flight",
              "llm_tpm_budget", "llm_rpm_budget")
HELD_OUT = ("xstk-ch3-1", "doc-4")
HELD_OUT_LABELS = ("xstk-ch3-1-chuong-10-13-*", "doc-4-chuong-8-*")
CHAIN = ("vai trò vùng (A2, `label-roles`) → clusters → mentions → provenance → teaching (neo C8 v3, vé 05/05b) → identity (vé 10b) → "
         "edges chính → edges phụ (hợp đồng cửa sổ định nghĩa, vé 12) → validated (A9) → concept_labels (vé 11/11b) → stages (A10 neo "
         "sách, vé 07/08/09c/18/20/21) → module_titles (vé 09–09d)")
# Lượt nghiệm thu vé 12: kho đánh giá cuối (edges → module_titles), chuỗi trước A8 nằm ở kho chính. Hai tài liệu đã kiểm tương đương (T10a).
ACCEPTED_STORE = Path("artifacts/v3-r12-final-evaluation")
ACCEPTED_DOCS = ("doc-1", "doc-6")
ACCEPTED_STAGES = ("clusters", "mentions", "provenance", "teaching", "identity", "edges", "edges", "validated", "validated",
                   "stages", "stages")
# Tệp chưa commit ở các đường này đổi mã chạy, nên chặn khoá; tệp khác (tài liệu riêng của chủ dự án) chỉ liệt kê.
RUNTIME_PATHS = ("src/", "scripts/", "pyproject.toml", "uv.lock")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, encoding="utf-8", check=True).stdout.strip()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accepted_hashes(base, final, doc):
    """prompt_hash ghi trong manifest của chuỗi đã nghiệm thu, theo đúng nhãn của bảng; None nếu chuỗi không như mong đợi."""
    chain = [final.load_latest_graph(doc)]
    while chain[-1].version != 1:
        chain.append(final.load_graph(doc, chain[-1].manifest["upstream_version"]))
    current = base.load_graph(doc, chain[-1].manifest["config"]["provenance_version"])
    while True:
        chain.append(current)
        if current.payload["stage"] == "clusters":
            break
        current = base.load_graph(doc, current.manifest["upstream_version"])
    chain.reverse()
    if tuple(artifact.payload["stage"] for artifact in chain) != ACCEPTED_STAGES:
        return None
    config = [artifact.manifest["config"] for artifact in chain]
    chunks = base.load_chunks(doc, config[-1]["chunks_version"]).manifest["config"]["region_roles"]
    return {"vai trò vùng (A2)": chunks["prompt_hash"], "provenance (A7)": config[2]["prompt_hash"],
            "teaching — neo C8 v3": config[3]["prompt_hash"], "teaching — kiểm kiến thức nền": config[3]["prior_verify_prompt_hash"],
            "identity — lượt 1": config[4]["prompt_hash"], "identity — lượt xác minh": config[4]["verify_prompt_hash"],
            "edges — pass chính": config[5]["prompt_hash"], "edges — pass phụ": config[6]["prompt_hash"],
            "concept_labels": config[8]["prompt_hash"], "module_titles": config[10]["prompt_hash"]}


def main():
    draft = "--nhap" in sys.argv
    pipeline, settings = build_learning_graph()
    store = pipeline.teaching.store
    model_id = settings.roadmap_model_id
    generation = {"temperature": 0.0, "max_output_tokens": settings.extraction_max_output_tokens}
    anchor_generation = AnchorConcepts(store, None).generation
    identity_generation = JudgeIdentity(store, None).generation
    label_generation = {"temperature": 0.0, "max_output_tokens": 512}
    # `git()` cắt khoảng trắng đầu chuỗi, nên dòng đầu mất cột trạng thái trống: tách theo khoảng trắng thay vì cắt 3 ký tự.
    dirty = [line.split(maxsplit=1)[1] for line in git("status", "--porcelain", "--untracked-files=no").splitlines()]
    blocking = [path for path in dirty if path.startswith(RUNTIME_PATHS)]
    if blocking:
        tree = "**có thay đổi chưa commit ở mã chạy — không được khoá ở trạng thái này**: " + ", ".join(f"`{p}`" for p in blocking)
    elif dirty:
        tree = ("sạch ở mã chạy (`src/`, `scripts/`, `pyproject.toml`, `uv.lock`); tệp đã theo dõi khác chưa commit, không ảnh hưởng chạy: "
                + ", ".join(f"`{p}`" for p in dirty))
    else:
        tree = "sạch (chỉ tính tệp đã theo dõi)"
    # Trần token đầu ra thật của adapter từng stage: không vào config hash nhưng đổi lời gọi (vé T10a mục 5).
    caps = [(name, getattr(getattr(stage, "model", None), "_max_output_tokens", None))
            for name, stage in (("provenance", pipeline.provenance), ("neo", pipeline.teaching), ("danh tính", pipeline.identity),
                                ("pass chính", pipeline.main_edges), ("pass phụ", pipeline.secondary_edges),
                                ("tên khái niệm", pipeline.concept_labels), ("tên module", pipeline.module_titles))]
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
    final = JsonArtifactStore(ACCEPTED_STORE)
    accepted = {doc: accepted_hashes(store, final, doc) for doc in ACCEPTED_DOCS}
    mismatch = [doc for doc, values in accepted.items() if values is None or any(values[s] != v for s, v in hashes)]
    lines = [
        "# T10 — Cấu hình khoá cho lần chạy tập giữ lại 07 v2 (chuỗi v3)", "",
        "Sinh bởi `scripts/khoa-cau-hinh/tao_bang.py`" + (" — **BẢN NHÁP, chưa phải bản khoá**." if draft else "."),
        "Chủ dự án duyệt bảng này trước bước chạy của [giao thức](T10-07v2-giao-thuc-tap-giu-lai.md); từ lúc duyệt, mọi thay đổi là",
        "hậu kiểm, báo tách riêng, không thay kết quả tập giữ lại.", "",
        "## Mã", "",
        f"- commit: `{git('rev-parse', 'HEAD')}` ({git('log', '-1', '--format=%cs %s')[:90]})",
        f"- cây làm việc: {tree}",
        f"- chuỗi: {CHAIN}", "",
        "## Mô hình và tham số (thiết lập không bí mật)", "",
        "| thiết lập | giá trị |", "|---|---|",
        *[f"| `{name}` | `{getattr(settings, name)}` |" for name in SETTINGS],
        "", "Không thuộc phương pháp (không đổi kết quả hay khoá cache), ghi để kiểm toán: " +
        ", ".join(f"`{name}={getattr(settings, name, None)}`" for name in NOT_METHOD) + ".",
        "", "## prompt_hash từng stage (mô hình và generation đúng như chuỗi mặc định)", "",
        "| stage | prompt_hash | " + " · ".join(ACCEPTED_DOCS) + " |", "|---|---|---|",
        *[f"| {stage} | `{value}` | " + " · ".join("—" if accepted[doc] is None else "khớp" if accepted[doc][stage] == value
                                                    else "**lệch**" for doc in ACCEPTED_DOCS) + " |" for stage, value in hashes],
        "", f"Cột cuối so với `prompt_hash` trong manifest của lượt nghiệm thu vé 12 (`{ACCEPTED_STORE.as_posix()}` và chuỗi trước A8 ở kho "
        "chính). " + ("**Có lệch hoặc không dựng được chuỗi — dừng, không khoá.**" if mismatch else "Mọi stage khớp."),
        "", "## Luật cố định trong mã", "",
        f"- neo: {anchor_concepts.CANDIDATES} câu ứng viên; generation {anchor_generation}",
        f"- danh tính: gộp nhóm đã kiểm đủ; quyết định người: {sorted(judge_identity.HUMAN_VERDICT)}; generation {identity_generation}",
        f"- A8: cửa sổ định nghĩa = câu neo, {settings.a8_definition_before} câu trước, {settings.a8_definition_after} câu sau, trong cùng đoạn của "
        "chunk neo; chỉ `can_de_hieu` là cạnh cứng",
        f"- A10: trọng số chia module {DEFAULT_WEIGHTS}; trần module {settings.roadmap_stage_cap}",
        "- trần token đầu ra thật của adapter: " + ", ".join(f"{name} {cap}" for name, cap in caps), "",
        "## Đầu vào đã có của tập giữ lại (dùng lại — bộ vàng gắn với canonical này)", "",
        "Chunks gắn với A3 là version mà candidates trỏ tới, không phải version mới nhất. Ingest lại cây tham chiếu ở bậc 1 tạo version",
        "mới hơn chỉ dùng để chuyển vai trò và tên mục.", "",
        "| tài liệu | chunks gắn A3 | chunks mới nhất | candidates (A3) | canonical (A4/A5) |", "|---|---|---|---|---|",
    ]
    for doc in HELD_OUT:
        canonical = store.load_latest_canonical(doc)
        candidates = store.load_candidates(doc, canonical.manifest["upstream_version"])
        pinned = store.load_chunks(doc, candidates.manifest["upstream_version"])
        latest = store.load_latest_chunks(doc)
        parser = pinned.manifest.get("config", {}).get("parser", {})
        lines.append(f"| {doc} | v{pinned.version} (`{parser.get('adapter')}`) | v{latest.version} | v{candidates.version} | "
                     f"v{canonical.version} |")
    lines += ["", "## Tệp nhãn của tập giữ lại (chỉ băm, không mở)", "", "| tệp | SHA-256 |", "|---|---|"]
    for pattern in HELD_OUT_LABELS:
        for path in sorted(Path("artifacts/a8-gold").glob(pattern)):
            lines.append(f"| `{path.name}` | `{sha256(path)}` |")
    blind = Path("artifacts/a8-gold/liet-ke-mu-giu-lai.md")
    if blind.exists():
        lines.append(f"| `{blind.name}` (T13) | `{sha256(blind)}` |")
    lines.append("")
    if not draft and (blocking or mismatch):
        print(f"không khoá: mã chạy chưa commit {blocking}; lệch prompt_hash ở {mismatch}")
        return 1
    out = Path("tmp/T10-cau-hinh-khoa-nhap.md") if draft else Path("task/v3-lo-trinh-doc-duoc/T10-cau-hinh-khoa.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out}: {len(lines)} dòng" + (f"; lệch prompt_hash ở {mismatch}" if mismatch else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
