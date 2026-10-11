"""Chạy A1 (docling, qua đúng lệnh `ingest` của dự án) cho 16 cuốn học của D-01, lần lượt từng cuốn. 0 USD, không gọi LLM.

- Chỉ đọc `document-data/manifest.json` và lấy sách `split == "train"`. **Không mở sách `test/`** (tập giữ lại T-01).
- Mỗi cuốn một tiến trình `doc2roadmap ingest <tệp> --doc-id <id> --pdf-backend <bộ đọc>`, không `heading_scheme`. Lượt chính dùng
  pypdfium2: docling-parse giải mã hỏng font tiếng Việt của d01-01 (chữ thành "T'p c¡c ph†p bi,n"), như từng tách vỡ âm tiết doc-4. Parse và chunk được lưu ở kho artifact, nên D-01 bước 2 dùng lại được; manifest chunk ghi `parse_runtime_seconds`.
- Cuốn đã có parse thì `ingest` tự tái dùng. Ghi nhật ký thời gian tường từng cuốn ra `tmp/thu-a1/ingest-d01.jsonl`.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/thu-a1/ingest_d01.py [--chi=d01-01,d01-05] [--bo-doc=docling-parse|pypdfium2]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    manifest = json.loads((ROOT / "document-data/manifest.json").read_text(encoding="utf-8"))
    books = [book for book in manifest["books"] if book["split"] == "train"]
    if "chi" in options:
        wanted = set(options["chi"].split(","))
        books = [book for book in books if book["id"] in wanted]
    backend = options.get("bo-doc", "pypdfium2")
    log = ROOT / "tmp/thu-a1/ingest-d01.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    for book in books:
        path = ROOT / "document-data" / book["file"]
        assert "/test/" not in path.as_posix() and book["split"] == "train"
        doc_id = book["id"]  # cùng mã sách; đổi bộ đọc thì `ingest` tạo phiên bản parse mới (khoá cache có tên bộ đọc)
        began = time.perf_counter()
        done = subprocess.run([str(ROOT / ".venv/Scripts/doc2roadmap.exe"), "ingest", str(path), "--doc-id", doc_id,
                               "--a1", "docling", "--pdf-backend", backend], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        row = {"id": book["id"], "doc_id": doc_id, "field": book["field"], "backend": backend, "returncode": done.returncode,
               "wall_seconds": round(time.perf_counter() - began, 1),
               "summary": (done.stdout.strip().splitlines() or [""])[0][:200], "error": done.stderr[-600:] if done.returncode else ""}
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
