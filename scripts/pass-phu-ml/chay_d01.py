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
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = str(ROOT / ".venv/Scripts/doc2roadmap.exe")
LOG = ROOT / "tmp/pass-phu-ml/d01-chay.jsonl"  # `--nhat-ky=<tệp>` khi chạy nhiều luồng song song, mỗi luồng một tệp
INGEST_LOG = ROOT / "tmp/thu-a1/ingest-d01.jsonl"
BUDGET_USD = 75.0  # Chủ dự án cho phép vượt 25 USD ngày 2026-10-06; giữ chốt hữu hạn.
UNMEASURED_HISTORY_RESERVE_USD = 3.0
STALLED_SECONDS = 45 * 60


def budget_snapshot():
    train_ids = {f"d01-{i:02}" for i in range(1, 17)}
    spec = importlib.util.spec_from_file_location("d01_cost", ROOT / "scripts/do-chi-phi/bao_cao.py")
    cost = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cost)
    measured = 0.0
    incomplete = []
    for kind in ("chunks", "candidates", "canonical", "graph", "index"):
        for path in (ROOT / "artifacts" / kind).glob("d01-*/v*/manifest.json"):
            if path.parent.parent.name not in train_ids:
                continue
            value = cost.measure(json.loads(path.read_text(encoding="utf-8")))
            measured += cost.usd(value, 0.25)  # Conservative embedding provision, not billed USD.
            if not value["complete"] and value["model_calls"]:
                incomplete.append(str(path.relative_to(ROOT)))
    pending = {}
    for path in (ROOT / "artifacts/checkpoints/graph").glob("d01-*/*.json"):
        if path.parent.name not in train_ids:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        stats = payload.get("stage_measurements")
        if not stats:
            continue
        # Several checkpoints in one stage contain overlapping cumulative usage.
        key = (path.parent.name, stats["stage"])
        dollars = stats.get("input_tokens", 0) * 0.25 / 1e6 + stats.get("output_tokens", 0) * 1.5 / 1e6
        pending[key] = max(pending.get(key, 0.0), dollars)
    guard = measured + sum(pending.values()) + UNMEASURED_HISTORY_RESERVE_USD
    return {"guard_usd": guard, "artifact_provision_usd": measured, "pending_usd": sum(pending.values()),
            "history_reserve_usd": UNMEASURED_HISTORY_RESERVE_USD, "limit_usd": BUDGET_USD,
            "incomplete_artifacts": incomplete}


def check_budget():
    snapshot = budget_snapshot()
    path = ROOT / "tmp/pass-phu-ml/d01-budget.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    if snapshot["guard_usd"] >= BUDGET_USD:
        raise RuntimeError(f"D-01 chạm trần chi bảo thủ {snapshot['guard_usd']:.4f}/{BUDGET_USD} USD")


def stop_child(process):
    if process.poll() is None:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True)
        else:
            process.terminate()
        process.wait()


def log(row):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def progress_signature(doc):
    paths = list((ROOT / 'artifacts/checkpoints/graph' / doc).glob('*.json'))
    for kind in ('chunks', 'candidates', 'canonical', 'graph', 'index'):
        paths.extend((ROOT / 'artifacts' / kind / doc).glob('v*/manifest.json'))
    result = []
    for path in paths:
        try:
            stat = path.stat()
        except FileNotFoundError:  # A completed stage can remove its checkpoint.
            continue
        result.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(sorted(result))


def run(doc, step, arguments):
    check_budget()
    began = time.perf_counter()
    signature = progress_signature(doc)
    last_progress = began
    output_size = 0
    process = subprocess.Popen([CLI, *arguments], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace")
    try:
        while True:
            try:
                stdout, stderr = process.communicate(timeout=10)
                break
            except subprocess.TimeoutExpired as error:
                check_budget()
                now = time.perf_counter()
                current = progress_signature(doc)
                size = len(error.output or b'') + len(error.stderr or b'')
                if current != signature or size != output_size:
                    signature, output_size, last_progress = current, size, now
                elif now - last_progress >= STALLED_SECONDS:
                    stop_child(process)
                    stdout, stderr = process.communicate()
                    stderr += '\nlỗi tạm thời: không có tiến độ checkpoint/artifact/output trong 45 phút; đã dừng PID con để nối lại.\n'
                    break
    except BaseException:
        stop_child(process)
        raise
    done = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    row = {"doc": doc, "buoc": step, "lenh": " ".join(arguments), "ma_thoat": done.returncode,
           "giay": round(time.perf_counter() - began, 1), "ra": done.stdout[-1500:], "loi": done.stderr[-1500:] if done.returncode else ""}
    log(row)
    check_budget()
    return done


def run_retry(doc, step, arguments, attempts=5):
    """Chạy lại khi lỗi API tạm thời hoặc khi A3 không ghi artifact vì thiếu mục (`coverage_incomplete`).
    Lỗi tạm thời đo được là HTTP 429 RESOURCE_EXHAUSTED của hạn mức dùng chung Vertex; A2 cấu hình 0 lần thử lại trong luồng nên
    hỏng ngay. Chờ tăng gấp đôi 120, 240, 480, 960 giây. Không sửa mã hay cấu hình luồng."""
    for attempt in range(attempts):
        done = run(doc, step if attempt == 0 else f"{step}-lan{attempt + 1}", arguments)
        transient = done.returncode and "tạm thời" in (done.stderr or "")
        incomplete = "coverage_incomplete" in ((done.stdout or "") + (done.stderr or ""))
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
    settings = Settings()
    if settings.llm_transport != "vertex":
        raise SystemExit("đường gọi LLM không phải vertex — dừng (chủ dự án chỉ duyệt chi qua Vertex)")
    if any(getattr(settings, key) != "gemini-3.1-flash-lite" for key in
           ("extraction_model_id", "merge_model_id", "description_model_id", "roadmap_model_id")):
        raise SystemExit("D-01 chỉ được dùng gemini-3.1-flash-lite — dừng trước khi chi tiền")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    if "nhat-ky" in options:
        global LOG
        LOG = ROOT / options["nhat-ky"]
    manifest = json.loads((ROOT / "document-data/manifest.json").read_text(encoding="utf-8"))
    books = [book["id"] for book in manifest["books"] if book["split"] == "train"]
    if "chi" in options:
        requested = list(dict.fromkeys(options["chi"].split(",")))
        if not set(requested) <= set(books):
            raise SystemExit("--chi chỉ nhận ID của 16 sách học D-01")
        books = requested
    failed_docs = []
    for doc in books:
        while not ingested(doc):
            time.sleep(60)
        if not latest_chunks_have_roles(doc):
            if run_retry(doc, "A2", ["label-roles", "--doc-id", doc, "--allow-spend"]).returncode:
                failed_docs.append(doc)
                continue
        if run_retry(doc, "A3", ["a3", "--doc-id", doc]).returncode or not has_candidates(doc):
            log({"doc": doc, "buoc": "A3", "ma_thoat": -1, "giay": 0, "ra": "", "loi": "chưa có artifact candidates sau các lần thử"})
            failed_docs.append(doc)
            continue
        if run_retry(doc, "A4-ten", ["a4", "--doc-id", doc, "--names-only"]).returncode:
            failed_docs.append(doc)
            continue
        if run(doc, "du-toan", ["roadmap", "--doc-id", doc, "--dry-run", "--stop-after", "identity"]).returncode:
            failed_docs.append(doc)
            continue
        if run_retry(doc, "A6-A9", ["roadmap", "--doc-id", doc, "--allow-spend", "--stop-after", "identity"]).returncode:
            failed_docs.append(doc)
    if failed_docs:
        raise SystemExit("D-01 chưa xong: " + ", ".join(failed_docs))


if __name__ == "__main__":
    main()
