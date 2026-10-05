"""Đo A1 (docling) tại máy theo giao thức của nghiên cứu R-03 (vé v4-10). 0 USD, không gửi dữ liệu ra ngoài.

- Mỗi cấu hình chạy ở một tiến trình riêng, vì số luồng torch áp cho cả tiến trình.
- Mỗi lần chỉ đổi một yếu tố so với mốc. Mốc dựng bằng chính `DoclingParser._new_converter` của dự án, và chạy hai lần để biết mốc có
  tất định không. Thứ tự chạy xen kẽ: mốc, 8 luồng, tắt OCR, mốc lần 2.
- So đầu ra ba tầng:
  1. `DoclingDocument`: băm `export_to_dict()` bỏ `origin`/`name`, so chặt (`coord_precision=None`) và so nới (2 chữ số);
  2. từng mục `iterate_items(traverse_pictures=True)`: số dòng khác;
  3. đầu ra adapter của dự án (`DoclingParser.adapt`): băm các trường quyết định chunk (loại nút, chữ, cấp, trang, bảng, ảnh, công thức).
  Tầng 3 giống nhau thì chunk giống nhau, các khâu sau không phải chạy lại.
- Thời gian: bật `profile_pipeline_timings`, ghi tổng từng khâu docling và thời gian tường của lượt đo (sau một trang khởi động).
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/thu-a1/do_a1.py [--trang=20] [--ra=tmp/thu-a1/ket-qua] [--lam-lai]
(mặc định giữ cấu hình đã có tệp kết quả, để chạy tiếp lượt bị ngắt; `--lam-lai` đo lại tất cả)
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
# (khoá, tệp, trang bắt đầu, bộ đọc của dự án cho tài liệu đó)
DOCS = (("naive-bayes", "5_Naive Bayes Classifier.pdf", 1, "docling-parse"),
        ("doc-1", "doc-1.pdf", 40, "docling-parse"),
        ("xstk", "xstk-ch3-1.pdf", 1, "docling-parse"),
        ("doc-4", "doc-4.pdf", 100, "pypdfium2"))
ORDER = ("moc", "luong8", "khong_ocr", "moc_lan2")


def converter(config, backend):
    sys.path.insert(0, str(ROOT / "src"))
    from doc2roadmap.infrastructure.parsing.docling_parser import IMAGE_SCALE, DoclingParser
    if config in ("moc", "moc_lan2"):
        return DoclingParser._new_converter(backend)
    from docling.datamodel.accelerator_options import AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    options = {"images_scale": IMAGE_SCALE, "generate_picture_images": True}
    if config == "luong8":
        options["accelerator_options"] = AcceleratorOptions(num_threads=8)
    if config == "khong_ocr":
        options["do_ocr"] = False
    extra = {}
    if backend == "pypdfium2":
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
        extra["backend"] = PyPdfiumDocumentBackend
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=PdfPipelineOptions(**options),
                                                                               **extra)})


def fingerprint(document, precision):
    data = document.export_to_dict(coord_precision=precision)
    for key in ("origin", "name"):
        data.pop(key, None)
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def items(document):
    rows = []
    for item, _ in document.iterate_items(traverse_pictures=True):
        prov = item.prov[0] if getattr(item, "prov", None) else None
        grid = getattr(getattr(item, "data", None), "grid", None)
        rows.append(repr((str(getattr(item.label, "value", item.label)), getattr(item, "text", None), getattr(item, "orig", None),
                          getattr(item, "level", None), prov.page_no if prov else None,
                          tuple(round(value, 1) for value in prov.bbox.as_tuple()) if prov else None,
                          [[cell.text for cell in row] for row in grid] if grid else None)))
    return rows


def adapter_hash(document, backend, filename):
    from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser
    tree = DoclingParser(backend).adapt(document, filename).tree
    rows = [(n.node_type, n.text, n.raw_text, n.level, n.page, n.table_rows, n.image_id, n.formula_id) for n in tree.nodes]
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, default=str).encode("utf-8")).hexdigest(), len(rows)


def run_one(config, path, start, end, backend, out):
    from docling.datamodel.settings import settings
    settings.debug.profile_pipeline_timings = True
    conv = converter(config, backend)
    conv.convert(path, page_range=(start, start))  # nạp mô hình, không bấm giờ
    began = perf_counter()
    result = conv.convert(path, page_range=(start, end))
    wall = perf_counter() - began
    document = result.document
    timings = {}
    for key, value in (getattr(result, "timings", None) or {}).items():
        times = list(getattr(value, "times", []) or [])
        timings[key] = {"total": round(sum(times), 3), "count": len(times)}
    ocr_times = list(getattr((result.timings or {}).get("ocr"), "times", []) or [])
    adapter, nodes = adapter_hash(document, backend, Path(path).name)
    record = {"config": config, "pages": end - start + 1, "page_count": len(document.pages), "wall_seconds": round(wall, 2),
              "timings": timings, "ocr_pages_over_50ms": sum(t > 0.05 for t in ocr_times),
              "strict": fingerprint(document, None), "loose": fingerprint(document, 2), "items": items(document),
              "adapter": adapter, "adapter_nodes": nodes}
    Path(out).write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    if "--chay" in sys.argv:
        run_one(options["cau-hinh"], options["tep"], int(options["tu"]), int(options["den"]), options["bo-doc"], options["ra"])
        return
    pages = int(options.get("trang", 20))
    out_dir = Path(options.get("ra", "tmp/thu-a1/ket-qua"))
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for key, filename, start, backend in DOCS:
        results = {}
        for config in ORDER:
            out = out_dir / f"{key}-{config}.json"
            if out.exists() and "--lam-lai" not in sys.argv:  # lượt trước bị ngắt: giữ cấu hình đã đo xong
                print(f"{key} {config}: dùng kết quả đã có", flush=True)
            else:
                command = [sys.executable, __file__, "--chay", f"--cau-hinh={config}", f"--tep={ROOT / filename}", f"--tu={start}",
                           f"--den={start + pages - 1}", f"--bo-doc={backend}", f"--ra={out}"]
                done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
                if done.returncode != 0:
                    print(f"{key} {config}: LỖI\n{done.stderr[-1500:]}", flush=True)
                    continue
            results[config] = json.loads(out.read_text(encoding="utf-8"))
            row = results[config]
            print(f"{key} {config}: {row['wall_seconds']}s / {row['page_count']} trang", flush=True)
        base = results.get("moc")
        for config, row in results.items():
            same = {}
            if base:
                same = {"chat": row["strict"] == base["strict"], "noi": row["loose"] == base["loose"],
                        "muc_khac": sum(1 for line in set(row["items"]) ^ set(base["items"])),
                        "adapter": row["adapter"] == base["adapter"]}
            top = sorted(((name, value["total"]) for name, value in row["timings"].items() if name != "pipeline_total"),
                         key=lambda pair: -pair[1])[:3]
            summary.append({"doc": key, "config": config, "seconds_per_page": round(row["wall_seconds"] / max(row["page_count"], 1), 2),
                            "speedup": round(base["wall_seconds"] / row["wall_seconds"], 2) if base else None,
                            "ocr_pages": row["ocr_pages_over_50ms"], "top_stages": top, **same})
    (out_dir / "tong-hop.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{'tài liệu':<12} {'cấu hình':<10} {'giây/trang':>10} {'nhanh x':>8} {'trang OCR':>9}  chặt  nới  mục khác  adapter  khâu nặng nhất")
    for row in summary:
        print(f"{row['doc']:<12} {row['config']:<10} {row['seconds_per_page']:>10} {row['speedup']!s:>8} {row['ocr_pages']:>9}  "
              f"{row.get('chat')!s:<5} {row.get('noi')!s:<5} {row.get('muc_khac')!s:>8}  {row.get('adapter')!s:<7}  {row['top_stages']}")


if __name__ == "__main__":
    main()
