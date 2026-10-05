"""Đo A1 khi chia một tài liệu thành k đoạn trang, parse song song ở k tiến trình rồi ghép (vé v4-10, lượt 2). 0 USD, tại máy.

R-03 đã đo các tuỳ chọn trong **một** lần chạy docling. Đây là đòn bẩy chưa đo: song song nhiều tiến trình trên **một** cuốn, để giảm phút/cuốn.
- Adapter của dự án làm việc ở mức cả tài liệu: nối đoạn qua ranh giới trang, nhận đầu trang lặp, chuỗi mã mục. Vì vậy **ghép
  `DoclingDocument` trước** (`DoclingDocument.concatenate`, theo thứ tự trang), rồi mới adapt **một lần**. Không adapt từng đoạn.
- `concatenate` đánh số lại trang cho liền sau tài liệu trước. Các đoạn phải liền nhau và bắt đầu từ trang 1, như khi parse cả cuốn; script
  kiểm số trang sau ghép.
- Mỗi thợ: nạp mô hình, khởi động bằng một trang (không bấm giờ), parse đoạn của mình, ghi JSON `DoclingDocument` (ảnh nhúng) ra tệp tạm,
  báo thời gian parse và RAM đỉnh.
- Tiến trình chính: ghép, adapt, so **thứ tự mục** và **băm adapter** với mốc (k=1, cấu hình dự án). Báo hai thời gian:
  - "nóng" = thời gian parse lâu nhất trong các thợ + ghép + adapt (máy chủ giữ sẵn thợ đã nạp mô hình);
  - "lạnh" = thời gian tường từ lúc tạo tiến trình.
- Kiểm JSON khứ hồi: thợ của mốc băm adapter ngay trên tài liệu vừa parse; tiến trình chính băm lại sau khi đọc JSON; hai băm phải trùng.
- Cấu hình 4 thợ chỉ chạy khi RAM trống đủ (4 × RAM đỉnh của một thợ + 1 GB).
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/thu-a1/do_a1_chia_doan.py [--trang=40] [--tai-lieu=doc-1,doc-4,xstk] [--cau-hinh=moc,...]
  [--ra=tmp/thu-a1/chia-doan]   (cấu hình đầu tiên được chọn phải là `moc`, làm mốc so)
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from do_a1 import adapter_hash, converter, items  # noqa: E402

DOCS = {"doc-1": ("doc-1.pdf", "docling-parse"), "doc-4": ("doc-4.pdf", "pypdfium2"), "xstk": ("xstk-ch3-1.pdf", "docling-parse"),
        "naive-bayes": ("5_Naive Bayes Classifier.pdf", "docling-parse")}
# (tên, số thợ, số luồng mỗi thợ, OCR). "moc" là cấu hình dự án (docling mặc định 4 luồng, OCR bật).
CONFIGS = (("moc", 1, 4, True), ("moc_k2", 2, 4, True), ("l8_ko", 1, 8, False), ("k2_ko", 2, 4, False), ("k4_ko", 4, 2, False),
           ("moc_lan2", 1, 4, True))


def worker(path, backend, start, end, threads, ocr, out):
    import psutil
    from docling.datamodel.accelerator_options import AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling_core.types.doc import ImageRefMode
    from doc2roadmap.infrastructure.parsing.docling_parser import IMAGE_SCALE

    if threads == 4 and ocr:
        conv = converter("moc", backend)  # đúng `DoclingParser._new_converter` của dự án
    else:
        options = PdfPipelineOptions(images_scale=IMAGE_SCALE, generate_picture_images=True, do_ocr=ocr,
                                     accelerator_options=AcceleratorOptions(num_threads=threads))
        extra = {}
        if backend == "pypdfium2":
            from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
            extra["backend"] = PyPdfiumDocumentBackend
        conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options, **extra)})
    conv.convert(path, page_range=(start, start))  # nạp mô hình, không bấm giờ
    began = time.perf_counter()
    document = conv.convert(path, page_range=(start, end)).document
    seconds = time.perf_counter() - began
    document.save_as_json(Path(out), image_mode=ImageRefMode.EMBEDDED)
    direct = adapter_hash(document, backend, Path(path).name)[0]
    memory = psutil.Process().memory_info()
    Path(out + ".meta.json").write_text(json.dumps({
        "parse_seconds": round(seconds, 2), "pages": end - start + 1, "adapter_direct": direct,
        "peak_rss_gb": round(getattr(memory, "peak_wset", memory.rss) / 1e9, 2)}), encoding="utf-8")


def run_config(key, filename, backend, pages, name, workers, threads, ocr, folder):
    from docling_core.types.doc import DoclingDocument
    bounds = [round(i * pages / workers) for i in range(workers + 1)]
    segments = [(bounds[i] + 1, bounds[i + 1]) for i in range(workers)]
    began = time.perf_counter()
    processes = []
    for index, (a, b) in enumerate(segments):
        out = str(folder / f"{key}-{name}-{index}.json")
        command = [sys.executable, __file__, "--tho", f"--tep={ROOT / filename}", f"--bo-doc={backend}", f"--tu={a}", f"--den={b}",
                   f"--luong={threads}", f"--ocr={int(ocr)}", f"--ra={out}"]
        processes.append((out, subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                                                encoding="utf-8", errors="replace")))
    metas = []
    for out, process in processes:
        _, error = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"{key} {name}: thợ lỗi\n{error[-1500:]}")
        metas.append(json.loads(Path(out + ".meta.json").read_text(encoding="utf-8")))
    merge_began = time.perf_counter()
    parts = [DoclingDocument.load_from_json(Path(out)) for out, _ in processes]
    document = parts[0] if len(parts) == 1 else DoclingDocument.concatenate(parts)
    adapter, nodes = adapter_hash(document, backend, filename)
    finished = time.perf_counter()
    for out, _ in processes:
        Path(out).unlink(missing_ok=True)
    return {"config": name, "workers": workers, "threads": threads, "ocr": ocr, "segments": segments,
            "pages_after_merge": [min(document.pages), max(document.pages), len(document.pages)],
            "warm_seconds": round(max(m["parse_seconds"] for m in metas) + (finished - merge_began), 2),
            "cold_seconds": round(finished - began, 2), "merge_adapt_seconds": round(finished - merge_began, 2),
            "parse_seconds": [m["parse_seconds"] for m in metas], "peak_rss_gb": [m["peak_rss_gb"] for m in metas],
            "adapter": adapter, "adapter_nodes": nodes, "items": items(document),
            "json_roundtrip_ok": len(metas) > 1 or metas[0]["adapter_direct"] == adapter}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    if "--tho" in sys.argv:
        worker(options["tep"], options["bo-doc"], int(options["tu"]), int(options["den"]), int(options["luong"]),
               bool(int(options["ocr"])), options["ra"])
        return
    import psutil
    pages = int(options.get("trang", 40))
    out_dir = Path(options.get("ra", "tmp/thu-a1/chia-doan"))
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for key in options.get("tai-lieu", "doc-1,doc-4,xstk").split(","):
        filename, backend = DOCS[key]
        with tempfile.TemporaryDirectory(dir=out_dir) as folder:
            results = {}
            chosen = options.get("cau-hinh")
            for name, workers, threads, ocr in CONFIGS:
                if chosen and name not in chosen.split(","):
                    continue
                if workers >= 4:
                    peak = max((value for row in results.values() for value in row["peak_rss_gb"]), default=2.0)
                    free = psutil.virtual_memory().available / 1e9
                    if free < workers * peak + 1.0:
                        print(f"{key} {name}: bỏ qua — RAM trống {free:.1f} GB < {workers} × {peak:.1f} + 1 GB", flush=True)
                        continue
                row = run_config(key, filename, backend, pages, name, workers, threads, ocr, Path(folder))
                results[name] = row
                base = results["moc"]
                row["same_items_ordered"] = row["items"] == base["items"]
                row["same_adapter"] = row["adapter"] == base["adapter"]
                print(f"{key} {name}: nóng {row['warm_seconds']}s, lạnh {row['cold_seconds']}s, "
                      f"giây/trang nóng {row['warm_seconds'] / pages:.2f}, RAM đỉnh {row['peak_rss_gb']} GB, "
                      f"trang sau ghép {row['pages_after_merge']}, mục giống {row['same_items_ordered']}, "
                      f"adapter giống {row['same_adapter']}, JSON khứ hồi {row['json_roundtrip_ok']}", flush=True)
                (out_dir / f"{key}-{name}.json").write_text(json.dumps({k: v for k, v in row.items() if k != "items"},
                                                                       ensure_ascii=False, indent=1), encoding="utf-8")
            base = results["moc"]
            for name, row in results.items():
                summary.append({"doc": key, "config": name, "workers": row["workers"], "threads": row["threads"], "ocr": row["ocr"],
                                "warm_s_per_page": round(row["warm_seconds"] / pages, 2),
                                "speedup_warm": round(base["warm_seconds"] / row["warm_seconds"], 2),
                                "speedup_cold": round(base["cold_seconds"] / row["cold_seconds"], 2),
                                "same_items_ordered": row["same_items_ordered"], "same_adapter": row["same_adapter"],
                                "json_roundtrip_ok": row["json_roundtrip_ok"], "peak_rss_gb": max(row["peak_rss_gb"])})
    (out_dir / "tong-hop.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{'tài liệu':<9} {'cấu hình':<9} {'thợ×luồng':>9} {'OCR':>4} {'giây/trang':>10} {'nhanh x nóng':>12} {'x lạnh':>7} "
          f"{'mục':>5} {'adapter':>8} {'RAM GB':>7}")
    for row in summary:
        print(f"{row['doc']:<9} {row['config']:<9} {row['workers']}×{row['threads']:<7} {str(row['ocr'])[0]:>4} "
              f"{row['warm_s_per_page']:>10} {row['speedup_warm']:>12} {row['speedup_cold']:>7} {str(row['same_items_ordered'])[0]:>5} "
              f"{str(row['same_adapter'])[0]:>8} {row['peak_rss_gb']:>7}")


if __name__ == "__main__":
    main()
