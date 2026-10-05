"""D-01 bước 2: chạy luồng A2 → A9'' (dừng trước A8) trên 16 cuốn học, để xuất phiếu gán nhãn. Có tốn tiền Gemini qua Vertex.

Chủ dự án duyệt ngày 2026-10-05: "duyệt chi tất cả tiền miễn là dùng vertex"; đã tự kiểm định quyền dùng 16 cuốn; đồng ý bỏ A8 pass chính.
Theo đúng chuỗi v3 của tài liệu tiếng Việt (doc-4, xstk):
1. chờ `ingest` của cuốn đó xong (`scripts/thu-a1/ingest_d01.py`, bộ đọc pypdfium2, sơ đồ tiêu đề mặc định);
2. `label-roles --allow-spend` (A2) trên bản chunk mới nhất, bỏ qua nếu bản mới nhất đã có vai trò;
3. `a3` (A3 trích ứng viên và chỉ mục A3'; lệnh này không có dry-run);
4. `a4 --names-only` (A4 lớp tên, không gọi mô hình);
5. `roadmap --dry-run --stop-after identity`, ghi dự toán; rồi `roadmap --allow-spend --stop-after identity` (A6 → A7 → C8 → A9'').
- Kiểm trước khi chạy: đường gọi LLM phải là `vertex`, không thì dừng hẳn.
- Lỗi API tạm thời và A3 thiếu mục thì chạy lại bước đó (tối đa 4 lần, chờ tăng dần); A3 phải để lại artifact candidates mới sang A4.
- **Không mở sách `test/`.** Lỗi ở bước nào thì ghi và bỏ qua cuốn đó, không sửa mã hay cấu hình giữa chừng.
- Nhật ký từng bước: `tmp/pass-phu-ml/d01-chay.jsonl`.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/pass-phu-ml/chay_d01.py [--chi=d01-01,d01-02] [--nhat-ky=tmp/pass-phu-ml/d01-chay-a.jsonl]
Không bọc lệnh bằng `timeout`: một cuốn có thể chạy quá 30 phút (lượt thử đầu bị ngắt giữa A6 → A9'' vì thế).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = str(ROOT / ".venv/Scripts/doc2roadmap.exe")
LOG = ROOT / "tmp/pass-phu-ml/d01-chay.jsonl"  # `--nhat-ky=<tệp>` khi chạy nhiều luồng song song, mỗi luồng một tệp
INGEST_LOG = ROOT / "tmp/thu-a1/ingest-d01.jsonl"


def log(row):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def run(doc, step, arguments):
    began = time.perf_counter()
    done = subprocess.run([CLI, *arguments], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    row = {"doc": doc, "buoc": step, "lenh": " ".join(arguments), "ma_thoat": done.returncode,
           "giay": round(time.perf_counter() - began, 1), "ra": done.stdout[-1500:], "loi": done.stderr[-1500:] if done.returncode else ""}
    log(row)
    return done


def run_retry(doc, step, arguments, attempts=5):
    """Chạy lại khi lỗi API tạm thời hoặc khi A3 không ghi artifact vì thiếu mục (`coverage_incomplete`; A3 tự nối từ điểm lưu).
    Lỗi tạm thời đo được là HTTP 429 RESOURCE_EXHAUSTED của hạn mức dùng chung Vertex; A2 cấu hình 0 lần thử lại trong luồng nên
    hỏng ngay. Chờ tăng gấp đôi 120, 240, 480, 960 giây. Không sửa mã hay cấu hình luồng."""
    for attempt in range(attempts):
        done = run(doc, step if attempt == 0 else f"{step}-lan{attempt + 1}", arguments)
        transient = done.returncode and "tạm thời" in (done.stderr or "")
        incomplete = done.returncode == 0 and "coverage_incomplete" in (done.stdout or "")
        if not transient and not incomplete:
            return done
        if attempt < attempts - 1:
            time.sleep(120 * 2 ** attempt)
    return done


def has_candidates(doc):
    folder = ROOT / "artifacts/candidates" / doc
    return folder.exists() and any(p.name.startswith("v") for p in folder.iterdir())


def ingested(doc):
    if not INGEST_LOG.exists():
        return False
    for line in INGEST_LOG.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["id"] == doc and row["backend"] == "pypdfium2" and row["returncode"] == 0:
            return True
    return False


def latest_chunks_have_roles(doc):
    folder = ROOT / "artifacts/chunks" / doc
    versions = sorted((p for p in folder.iterdir() if p.name.startswith("v")), key=lambda p: int(p.name[1:]))
    manifest = json.loads((versions[-1] / "manifest.json").read_text(encoding="utf-8"))
    return bool(manifest.get("semantic_roles"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(ROOT / "src"))
    from doc2roadmap.config import Settings
    if Settings().llm_transport != "vertex":
        raise SystemExit("đường gọi LLM không phải vertex — dừng (chủ dự án chỉ duyệt chi qua Vertex)")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    if "nhat-ky" in options:
        global LOG
        LOG = ROOT / options["nhat-ky"]
    manifest = json.loads((ROOT / "document-data/manifest.json").read_text(encoding="utf-8"))
    books = [book["id"] for book in manifest["books"] if book["split"] == "train"]
    if "chi" in options:
        books = [doc for doc in books if doc in set(options["chi"].split(","))]
    for doc in books:
        while not ingested(doc):
            time.sleep(60)
        if not latest_chunks_have_roles(doc):
            if run_retry(doc, "A2", ["label-roles", "--doc-id", doc, "--allow-spend"]).returncode:
                continue
        if run_retry(doc, "A3", ["a3", "--doc-id", doc]).returncode or not has_candidates(doc):
            log({"doc": doc, "buoc": "A3", "ma_thoat": -1, "giay": 0, "ra": "", "loi": "chưa có artifact candidates sau các lần thử"})
            continue
        if run_retry(doc, "A4-ten", ["a4", "--doc-id", doc, "--names-only"]).returncode:
            continue
        if run(doc, "du-toan", ["roadmap", "--doc-id", doc, "--dry-run", "--stop-after", "identity"]).returncode:
            continue
        run_retry(doc, "A6-A9", ["roadmap", "--doc-id", doc, "--allow-spend", "--stop-after", "identity"])


if __name__ == "__main__":
    main()
