"""Kiểm nghiệm thu vé T-01a mà không lộ nội dung sách: chỉ in phiên bản, cấu hình và số đếm của artifact.
Không in tên khái niệm, tiêu đề mục hay câu chữ. Chỉ dùng thư viện chuẩn.

Chạy:  .venv/Scripts/python.exe -I scripts/t01/kiem_t01a.py [d01-t01 d01-t02] [--artifacts artifacts]
Thoát mã 1 nếu một điều kiện của vé không đạt.
"""
import argparse
import json
import sys
from pathlib import Path

ADAPTER, ADAPTER_VERSION = "docling:2.114.0+pypdfium2", 11      # giống 16 cuốn D-01 (vd. d01-03 chunks v2)
A4_GOLD_SHEET = "473a003957560b36d6fb16790066e6e6b2f8c6cd62786d9aa67cb72d0b30051e"  # tests/fixtures/a4/gold-blind.json
MODEL = "gemini-3.1-flash-lite"
STATS = ("runtime_seconds", "model_calls", "input_tokens", "output_tokens",
         "embedding_model_calls", "embedding_input_tokens", "usage_responses",
         "token_usage_complete", "measurement_history_complete", "section_count",
         "completed_section_count", "failed_section_count", "empty_section_count")
COST = ("input_tokens", "output_tokens", "usd")
ROLES = ("noi_dung", "bai_tap", "cuoi_sach", "de_cuong", "mo_dau")


def numbers(value, fields):
    """Only explicitly allowed numeric scalars; metadata may contain book text."""
    if value is None:
        return None
    return {key: value[key] for key in fields
            if key in value and isinstance(value[key], (int, float, bool))}


def latest(folder):
    versions = sorted((int(p.name[1:]) for p in folder.glob("v*") if p.name[1:].isdigit()), reverse=True)
    return versions[0] if versions else None


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(root, doc):
    errors, info = [], {"doc_id": doc}
    canon_v = latest(root / "canonical" / doc)
    if canon_v is None:
        return info, ["chưa có canonical"]
    canon_dir = root / "canonical" / doc / f"v{canon_v}"
    canon_m = load(canon_dir / "manifest.json")
    payload = load(canon_dir / "canonical.json")
    info["canonical"] = {"version": canon_v, "stage": payload.get("stage"), "so_nut": len(payload.get("nodes", [])),
                         "gold_sheet_id": (canon_m.get("gold_sheet_id") or "")[:12], "a4_gold_coverage": canon_m.get("a4_gold_coverage"),
                         "ngon_ngu": canon_m.get("config", {}).get("declared_language"), "chi": numbers(canon_m.get("cost_summary"), COST)}
    cand_v = canon_m.get("upstream_version")
    cand_m = load(root / "candidates" / doc / f"v{cand_v}" / "manifest.json")
    info["candidates"] = {"version": cand_v, "model_id": cand_m.get("model_id"), "llm_transport": cand_m.get("llm_transport"),
                          "stats": numbers(cand_m.get("stats"), STATS), "chi": numbers(cand_m.get("cost_summary"), COST)}
    chunk_v = cand_m.get("upstream_version")
    chunk_m = load(root / "chunks" / doc / f"v{chunk_v}" / "manifest.json")
    parser = chunk_m.get("config", {}).get("parser", {})
    info["chunks"] = {"version": chunk_v, "parser": parser, "llm_transport": chunk_m.get("llm_transport"),
                      "stats": numbers(chunk_m.get("stats"), STATS), "role_counts": numbers(chunk_m.get("role_counts"), ROLES)}
    info["graph_ton_tai"] = (root / "graph" / doc).exists()

    if parser.get("adapter") != ADAPTER or parser.get("adapter_version") != ADAPTER_VERSION:
        errors.append(f"A1 không giống D-01: cần {ADAPTER} adapter {ADAPTER_VERSION}")
    if set(parser) - {"adapter", "adapter_version", "image_scale"}:
        errors.append(f"cờ đọc PDF khác mặc định của D-01: {sorted(set(parser) - {'adapter', 'adapter_version', 'image_scale'})}")
    if payload.get("stage") != "complete":
        errors.append("canonical chưa qua A5 (stage khác complete)")
    if canon_m.get("gold_sheet_id") != A4_GOLD_SHEET or canon_m.get("a4_gold_coverage") != "none":
        errors.append("a4 không chạy với --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc")
    if info["canonical"]["ngon_ngu"] != "vi":
        errors.append("a4 thiếu --language vi")
    if cand_m.get("model_id") != MODEL or cand_m.get("llm_transport") != "vertex":
        errors.append(f"A3 không chạy {MODEL} qua Vertex")
    if info["graph_ton_tai"]:
        errors.append("đã có artifact graph: vé không cho chạy roadmap (A6 trở đi)")
    return info, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="*", default=["d01-t01", "d01-t02"])
    ap.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    failed = False
    for doc in args.docs:
        info, errors = check(args.artifacts, doc)
        print(json.dumps(info, ensure_ascii=False))
        for error in errors:
            print("LỖI", doc, error)
        print(doc, "ĐẠT" if not errors else f"KHÔNG ĐẠT: {len(errors)} lỗi")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
