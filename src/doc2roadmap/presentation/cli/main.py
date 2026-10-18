from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from doc2roadmap.application.use_cases import (
    compare_candidate_versions,
    evaluate_gold,
    report_candidates,
)
from doc2roadmap.composition import (
    build_a3,
    build_artifact_store,
    build_extract,
    build_index,
    build_ingest,
    build_inspect,
    build_search,
    build_canonical,
    build_learning_graph,
    build_region_roles,
)
from doc2roadmap.application.use_cases.report_a3 import review_candidate_types
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.domain.canonical import compare_nodes
from doc2roadmap.application.use_cases.a4_gold import gold_items, write_gold_sheet, load_gold, evaluate_canonical
from doc2roadmap.application.use_cases import a8_score
from doc2roadmap.infrastructure.parsing.docling_parser import PipelineConfig
from doc2roadmap.application.use_cases.build_roadmap import render_roadmap_html, target_roadmap
from doc2roadmap.application.use_cases.a8_gold import (
    adjudication_rows,
    chapters_from_store,
    read_adjudication_sheet,
    write_adjudication_sheet,
    read_annotation_sheet,
    scope_from_store,
    write_annotation_sheet,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doc2roadmap")
    commands = parser.add_subparsers(dest="command", required=True)
    roles = commands.add_parser('label-roles', help='gán vai trò vùng sau A2; không đổi ID/text chunk')
    roles.add_argument('--doc-id', required=True)
    roles.add_argument('--chunks-version', type=int)
    roles.add_argument('--transfer-from-chunks-version', type=int)
    roles.add_argument('--dry-run', action='store_true')
    roles.add_argument('--allow-spend', action='store_true')
    features = commands.add_parser('a8-secondary-features', help='xuất CSV 82 đặc trưng E5 từ pass chính, không gọi mô hình')
    features.add_argument('--doc-id', required=True)
    features.add_argument('--main-version', type=int, required=True)
    features.add_argument('--output-dir', type=Path, required=True)
    features.add_argument('--artifacts', type=Path, help='kho graph; mặc định artifact_dir')
    features.add_argument('--chunks-artifacts', type=Path, help='kho chunk nếu nằm ngoài kho graph')
    canonical = commands.add_parser("a4", help="hợp nhất thực thể và mô tả chuẩn (cần --gold); --names-only/--prepare không gọi mô hình phán")
    canonical.add_argument("--doc-id", required=True)
    mode = canonical.add_mutually_exclusive_group()
    mode.add_argument("--names-only", action="store_true", help="chỉ lớp tên, không mạng")
    mode.add_argument("--prepare", action="store_true", help="chỉ đề cử bằng embedding, chưa phán")
    canonical.add_argument("--gold", type=Path, help="bộ vàng đã gán mù, bắt buộc trước khi gọi LLM")
    canonical.add_argument("--language", choices=("vi", "en"), help="khai ngôn ngữ tài liệu cho A5")
    canonical.add_argument("--merge-review", type=Path,
                           help="quyết định duyệt gộp ở A4 chuỗi gop, định dạng quyết định theo cặp node")
    canonical.add_argument("--allow-spend", action="store_true", help="cho phép mô hình/embedding của chuỗi gop")
    canonical.add_argument("--dry-run", action="store_true", help="dự toán từng phần; không gọi mô hình hay embedding")
    canonical.add_argument(
        "--no-gold-for-doc",
        action="store_true",
        help="cho phép tài liệu mới không nằm trong bộ vàng; vẫn kiểm bộ vàng hoàn chỉnh",
    )
    comparison = commands.add_parser("a4-compare", help="so hai phiên bản canonical")
    comparison.add_argument("--doc-id", required=True)
    comparison.add_argument("--first", type=int, required=True)
    comparison.add_argument("--second", type=int, required=True)
    gold_sheet = commands.add_parser("a4-gold-sheet", help="sinh HTML gán mù từ artifact đề cử")
    gold_sheet.add_argument("--doc-id", action="append", required=True)
    gold_sheet.add_argument("--output", type=Path, default=Path("artifacts/a4-gold.html"))
    prereq_sheet = commands.add_parser("a8-gold-sheet", help="sinh file Excel gán mù quan hệ tiên quyết cho một chương")
    prereq_sheet.add_argument("--doc-id", required=True)
    prereq_sheet.add_argument("--chapter", help="số thứ tự, dải như 10-13, danh sách như 2,4, hoặc section_id")
    prereq_sheet.add_argument("--chapter-level", type=int, default=1, help="cấp heading được coi là chương")
    prereq_sheet.add_argument("--canonical-version", type=int)
    prereq_sheet.add_argument("--annotator", help="mã người gán, ví dụ A1")
    prereq_sheet.add_argument("--output", type=Path)
    prereq_sheet.add_argument("--list-chapters", action="store_true", help="chỉ liệt kê chương và số khái niệm đích")
    prereq_sheet.add_argument("--graph", type=Path, help="graph.json của stage provenance: nơi dạy theo provenance đã vá")
    prereq_sheet.add_argument("--force", action="store_true", help="ghi đè file đã có (có thể làm mất nhãn đã gán)")
    prereq_score = commands.add_parser("a8-score", help="chấm E1 và E2 từ bộ vàng; không gọi mô hình")
    prereq_score.add_argument("--doc-id", required=True)
    prereq_score.add_argument("--graph", type=Path, required=True, help="graph.json của một phiên bản artifact graph")
    prereq_score.add_argument("--gold", type=Path, action="append", required=True,
                              help="JSON từ a8-gold-check; lặp lại tham số cho người gán thứ hai")
    prereq_score.add_argument("--gold-mode", choices=("union", "intersection"), default="union",
                              help="cách gộp khi có hai người gán")
    prereq_score.add_argument("--bootstrap", type=int, default=2000, help="số lần lấy mẫu lại; 0 để bỏ khoảng tin cậy")
    prereq_score.add_argument("--seed", type=int, default=20260918)
    prereq_score.add_argument("--provenance", choices=("patched", "source"), default="patched",
                              help="chấm theo provenance đã vá, hoặc bản gốc A3/A4 để so trước sau")
    prereq_score.add_argument("--output", type=Path, help="ghi báo cáo đầy đủ ra JSON")
    prereq_score.add_argument("--remap-gold-ids", action="store_true",
                              help="quy id vàng qua chuyển hướng canonical của graph trước khi chấm")
    prereq_score.add_argument("--gold-graph", type=Path,
                              help="graph gán vàng gốc nếu vàng dùng provenance đã vá; cần --remap-gold-ids")
    roadmap_score = commands.add_parser(
        "a8-roadmap-score",
        help="chấm thứ tự lộ trình: tau so mục lục và tỉ lệ vi phạm cạnh vàng; không gọi mô hình")
    roadmap_score.add_argument("--graph", type=Path, required=True,
                               help="graph.json ở stage stages")
    roadmap_score.add_argument("--gold", type=Path, action="append", default=[],
                               help="JSON từ a8-gold-check; lặp lại cho người gán thứ hai")
    roadmap_score.add_argument("--gold-mode", choices=("union", "intersection"), default="union")
    roadmap_score.add_argument("--remap-gold-ids", action="store_true",
                               help="quy id vàng qua chuyển hướng canonical của graph trước khi chấm")
    roadmap_score.add_argument("--output", type=Path, help="ghi báo cáo đầy đủ ra JSON")
    roadmap_target = commands.add_parser(
        "roadmap-target", help="lộ trình tới một hoặc vài khái niệm đích; không gọi mô hình")
    roadmap_target.add_argument("--graph", type=Path, required=True, help="graph.json ở stage stages")
    roadmap_target.add_argument("--concept", action="append", required=True,
                                help="tên, alias hoặc mã node; lặp lại để chọn nhiều đích")
    roadmap_target.add_argument("--output", type=Path, help="ghi trang HTML của lộ trình tới mục tiêu")
    prereq_merge = commands.add_parser("a8-gold-merge",
                                       help="hội ý hai bộ nhãn: sinh file quyết, hoặc đọc ngược thành bộ vàng")
    prereq_merge.add_argument("--doc-id", required=True)
    prereq_merge.add_argument("--chapter", required=True)
    prereq_merge.add_argument("--chapter-level", type=int, default=1)
    prereq_merge.add_argument("--canonical-version", type=int)
    prereq_merge.add_argument("--graph", type=Path, help="đúng graph.json đã dùng lúc sinh file gán")
    prereq_merge.add_argument("--gold", type=Path, action="append", required=True,
                              help="hai JSON từ a8-gold-check, mỗi người một file")
    prereq_merge.add_argument("--file", type=Path, help="file hội ý đã điền; không có thì sinh file mới")
    prereq_merge.add_argument("--output", type=Path, help="nơi ghi file hội ý mới, hoặc bộ vàng cuối dạng JSON")
    prereq_merge.add_argument("--force", action="store_true", help="ghi đè file hội ý đã có")
    prereq_check = commands.add_parser("a8-gold-check", help="đọc và kiểm file Excel tiên quyết đã gán")
    prereq_check.add_argument("--doc-id", required=True)
    prereq_check.add_argument("--chapter", required=True)
    prereq_check.add_argument("--chapter-level", type=int, default=1)
    prereq_check.add_argument("--canonical-version", type=int)
    prereq_check.add_argument("--file", type=Path, required=True)
    prereq_check.add_argument("--graph", type=Path, help="phải dùng đúng graph.json đã dùng lúc sinh file")
    prereq_check.add_argument("--output", type=Path, help="ghi nhãn đã kiểm thành JSON, chỉ khi không có lỗi")
    evaluation = commands.add_parser("a4-evaluate", help="chấm canonical trên bộ vàng")
    evaluation.add_argument("--doc-id", required=True)
    evaluation.add_argument("--gold", type=Path, required=True)
    evaluation.add_argument("--second-gold", type=Path)
    evaluation.add_argument("--canonical-version", type=int)
    evaluation.add_argument("--exclude-subtype-item", action="append", default=[])
    ingest = commands.add_parser("ingest", help="parse và cắt một PDF/DOCX")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--doc-id", required=True)
    ingest.add_argument("--a1", choices=("nhe", "docling"), default="nhe",
                        help="bộ đọc A1; mặc định nhẹ R2, tài liệu cũ ghim docling")
    ingest.add_argument("--pdf-backend", choices=["docling-parse", "pypdfium2"], default=None,
                        help="ghim bộ đọc PDF; bỏ cờ để tự chọn, bắt đầu bằng pypdfium2 và đổi khi chữ hỏng")
    ingest.add_argument("--heading-scheme", choices=["vn-textbook"], default=None,
                        help="thang tiêu đề Phần → Chương → I- → 1. → a) của giáo trình tiếng Việt")
    ingest.add_argument("--dry-run", action="store_true", help="chỉ kiểm cache parse; không parse/cắt chunk/ghi artifact")
    ingest.add_argument("--pdf-text-policy", choices=("preserve", "legacy"), default=None,
                        help="preserve: giữ chữ lặp; legacy: tái lập cleanup/cache adapter v11")
    for name in ("do_ocr", "generate_picture_images", "force_full_page_ocr", "do_table_structure", "do_cell_matching"):
        ingest.add_argument("--" + name.replace("_", "-"), action=argparse.BooleanOptionalAction,
                            default=None)
    for name in ("images_scale", "bitmap_area_threshold", "batch_polling_interval_seconds"):
        ingest.add_argument("--" + name.replace("_", "-"), type=float, default=None)
    for name in ("num_threads", "ocr_batch_size", "layout_batch_size", "table_batch_size", "queue_max_size"):
        ingest.add_argument("--" + name.replace("_", "-"), type=int, default=None)
    ingest.add_argument("--ocr-engine", choices=("rapidocr", "easyocr"), default=None)
    ingest.add_argument("--ocr-backend", choices=("torch", "onnxruntime", "openvino", "paddle"), default=None)
    ingest.add_argument("--table-mode", choices=("accurate", "fast"), default=None)
    ingest.add_argument("--layout-model", choices=("heron", "heron-101", "egret-medium", "egret-large", "v2"), default=None)
    ingest.add_argument(
        "--strip-line",
        action="append",
        default=[],
        help="bỏ mẫu văn bản trước khi cắt chunk; có thể lặp lại",
    )
    inspect = commands.add_parser("inspect", help="xem cây section và window đã lưu")
    inspect.add_argument("--doc-id", required=True)
    extract = commands.add_parser("extract", help="trích ứng viên thực thể A3")
    extract.add_argument("--doc-id", required=True)
    extract.add_argument("--few-shot", type=Path, help="ghi đè tệp few-shot mặc định")
    extract.add_argument("--force", action="store_true", help="tạo phiên bản mới để đo ổn định")
    index = commands.add_parser("index", help="lập chỉ mục chunk A3'")
    index.add_argument("--doc-id", required=True)
    a3 = commands.add_parser("a3", help="chạy A3 và A3' song song")
    a3.add_argument("--doc-id", required=True)
    a3.add_argument("--few-shot", type=Path, help="ghi đè tệp few-shot mặc định")
    search = commands.add_parser("search", help="truy hồi lai trên chỉ mục A3'")
    search.add_argument("query")
    search.add_argument("--doc-id", required=True)
    search.add_argument("--top-k", type=int, default=10)
    search.add_argument("--stage-id", action="append")
    report = commands.add_parser("a3-report", help="báo cáo chỉ số ứng viên")
    report.add_argument("--doc-id", action="append", required=True)
    review = commands.add_parser("a3-review-types", help="liệt kê kiểu hiếm cần người duyệt")
    review.add_argument("--doc-id", action="append", required=True)
    compare = commands.add_parser("a3-compare", help="so Jaccard hai phiên bản ứng viên")
    compare.add_argument("--doc-id", required=True)
    compare.add_argument("--first", type=int, required=True)
    compare.add_argument("--second", type=int, required=True)
    evaluate = commands.add_parser("a3-evaluate", help="chấm ứng viên bằng bộ vàng mù")
    evaluate.add_argument("--doc-id", required=True)
    evaluate.add_argument("--gold", type=Path, required=True)
    evaluate.add_argument("--candidate-version", type=int)
    roadmap = commands.add_parser("roadmap", help="chạy A6 đến A10 trên một tài liệu")
    roadmap.add_argument("--doc-id", required=True)
    roadmap.add_argument(
        "--stop-after",
        choices=("clusters", "mentions", "edges", "stages"),
        default="stages",
        help="dừng sau stage đã chọn; provenance/teaching/identity đã gỡ, neo và danh tính nằm trong canonical",
    )
    roadmap.add_argument("--allow-spend", action="store_true",
                         help="cho phép gọi mô hình trả tiền; thiếu cờ thì lệnh dừng ở stage đầu tiên định chi")
    roadmap.add_argument("--dry-run", action="store_true",
                         help="chỉ đọc cache/checkpoint và dự toán mọi stage; không gọi mô hình hoặc ghi artifact")
    for command in (ingest, roles, commands.choices["a3"], commands.choices["extract"], commands.choices["roadmap"]):
        command.add_argument("--allow-text-quality-reason", help="cho phép chữ cảnh báo với lý do xác nhận; không xoá cảnh báo")
    from doc2roadmap.presentation.cli.phase_b import configure as configure_phase_b
    configure_phase_b(commands)
    return parser


def _ingest(path: Path, doc_id: str, *, strip_lines: list[str] | None = None,
            pdf_backend: str | None = None, heading_scheme: str | None = None,
            pipeline: PipelineConfig | None = None, dry_run: bool = False, quality_reason=None,
            a1: str = "docling") -> None:
    if not path.is_file():
        raise FileNotFoundError(f"không đọc được file: {path}")
    if a1 == "nhe" and path.suffix.lower() != ".pdf":
        raise ValueError("A1 nhẹ chỉ hỗ trợ PDF gốc; DOCX dùng --a1 docling")
    use_case, settings = (build_ingest(a1="nhe") if a1 == "nhe" else build_ingest(pdf_backend) if pipeline is None
                          else build_ingest(pdf_backend, pipeline=pipeline))
    if dry_run:
        from doc2roadmap.application.use_cases.ingest_document import _hash, parse_config, validate_doc_id, quality_selection_report
        validate_doc_id(doc_id)
        if path.suffix.lower() not in {".pdf", ".docx"} or path.stat().st_size == 0:
            raise ValueError("cần file PDF/DOCX không rỗng")
        selected, stored, _, _, _, _ = use_case.select_parse(path.read_bytes(), path.name, doc_id, strip_lines or [],
                                                          dry_run=True, quality_reason=quality_reason)
        config = parse_config(selected, strip_lines or [])
        _json({"doc_id": doc_id, "parse": "tái dùng" if stored else "cần parse mới",
               "parser_config_hash": _hash(config), "parser_config": config,
               "parse_version": stored.version if stored else None,
               "text_quality_selection": quality_selection_report(use_case.last_parse_selection),
               "parser_runtime": stored.manifest.get("parser_runtime", "chưa ghi ở artifact cũ") if stored else None})
        return
    summary = use_case.execute(
        path.read_bytes(),
        path.name,
        doc_id,
        max_tokens=settings.max_tokens,
        max_table_tokens=settings.max_table_tokens,
        hard_cap_tokens=settings.hard_cap_tokens,
        target_tokens=settings.target_tokens,
        sentence_overlap=settings.sentence_overlap,
        strip_lines=strip_lines or [],
        heading_scheme=heading_scheme,
        **({"quality_reason": quality_reason} if quality_reason is not None else {}),
    )
    seen = " (đã ingest trước đó; tái dùng parse tree)" if summary.source_seen_before else ""
    print(
        f"{summary.doc_id}: {summary.section_count} section, {summary.chunk_count} chunk, "
        f"{summary.window_count} window{seen}"
    )
    stats = summary.parse_stats
    dropped = ", ".join(f"{label}={count}" for label, count in stats.get("dropped", {}).items()) or "không"
    print(
        f"parse: giữ {stats.get('nodes_kept', 0)}/{stats.get('items_total', 0)}; bỏ: {dropped}; "
        f"stitch={stats.get('page_breaks_stitched', 0)}; sắp lại trang={stats.get('pages_reordered', 0)}"
    )
    captions = stats.get("captions")
    if captions:
        print(
            f"media: ảnh={stats.get('images_extracted', 0)}; chú thích="
            f"{captions['total']} (lấy lại={captions['recovered']}, mồ côi={captions['orphaned']})"
        )
    warnings = [*summary.structure_warnings, *summary.quality_warnings]
    if warnings:
        print("Cảnh báo:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("Cảnh báo: không")
    print(f"artifact: {summary.artifact_path}")


def _inspect(doc_id: str) -> None:
    stored, windows = build_inspect().execute(doc_id)
    result = stored.result
    by_parent: dict[str | None, list] = {}
    for section in result.sections:
        by_parent.setdefault(section.parent_section_id, []).append(section)

    def print_section(section, indent: int = 0) -> None:
        marker = "" if section.has_direct_content else " [không có nội dung trực tiếp]"
        path = " > ".join(section.section_path) or "<document>"
        print(f"{'  ' * indent}- {section.title} ({path}){marker}")
        for child in by_parent.get(section.section_id, []):
            print_section(child, indent + 1)

    roots = by_parent.get(None, [])
    for root in roots:
        print_section(root)
    print("\nWindows:")
    section_by_id = {section.section_id: section for section in result.sections}
    for section_id, chunks in windows.items():
        section = section_by_id[section_id]
        print(f"[{section_id}] {' > '.join(section.section_path) or '<document>'}")
        for chunk in chunks:
            preview = chunk.text.replace("\n", " ")
            print(f"  {chunk.order_index:04d} {chunk.chunk_id} {preview}")
    if result.structure_warnings:
        print("\nCảnh báo:")
        for warning in result.structure_warnings:
            print(f"- {warning}")
    else:
        print("\nCảnh báo: không")


def _print_extraction(summary) -> None:
    metrics = summary.result.stats["metrics"]
    state = "tái dùng" if summary.reused else "mới"
    print(
        f"A3 {summary.result.doc_id}: {metrics['learnable_entities']} learnable, "
        f"{metrics['total_entities']} tổng, {metrics['learnable_per_1000_tokens']:.2f}/1000 token "
        f"({state})"
    )
    for warning in summary.result.warnings:
        print(f"- {warning}")
    print(
        f"artifact: {summary.artifact_path or 'không ghi vì coverage_incomplete'}"
    )
    if summary.result.coverage_incomplete:
        raise ValueError("coverage_incomplete: không ghi ứng viên; các mục hỏng: "
                         + ", ".join(summary.result.failed_sections))


def _extract(
    doc_id: str, *, force: bool = False, few_shot_path: Path | None = None, quality_reason=None
) -> None:
    use_case, settings = build_extract(few_shot_path=few_shot_path)
    use_case.quality_reason = quality_reason
    _print_extraction(
        use_case.execute(
            doc_id,
            max_workers=settings.extraction_concurrency,
            force=force,
        )
    )


def _index(doc_id: str) -> None:
    use_case, _ = build_index()
    summary = use_case.execute(doc_id)
    state = "tái dùng" if summary.reused else "mới"
    print(
        f"A3' {doc_id}: {len(summary.payload['documents'])} chunk ({state})\n"
        f"artifact: {summary.artifact_path}"
    )


def _a3(doc_id: str, *, few_shot_path: Path | None = None, quality_reason=None) -> None:
    extraction, index, settings = build_a3(few_shot_path=few_shot_path)
    extraction.quality_reason = quality_reason
    if hasattr(extraction, "store"):
        from doc2roadmap.application.use_cases.ingest_document import require_text_quality
        require_text_quality(extraction.store.load_latest_chunks(doc_id), reason=quality_reason, store=extraction.store)
    with ThreadPoolExecutor(max_workers=2) as executor:
        extraction_future = executor.submit(
            extraction.execute,
            doc_id,
            max_workers=settings.extraction_concurrency,
        )
        index_future = executor.submit(index.execute, doc_id)
        extraction_summary = extraction_future.result()
        index_summary = index_future.result()
    _print_extraction(extraction_summary)
    print(f"A3' {doc_id}: {len(index_summary.payload['documents'])} chunk")


def _search(doc_id: str, query: str, top_k: int, stage_ids: list[str] | None) -> None:
    hits = build_search().execute(
        doc_id,
        query,
        top_k=top_k,
        allowed_stage_ids=set(stage_ids) if stage_ids else None,
    )
    for rank, hit in enumerate(hits, 1):
        print(
            f"{rank}. {hit.chunk_id} score={hit.score:.6f} "
            f"dense={hit.dense_rank or '-'} bm25={hit.bm25_rank or '-'}"
        )


def _inside_artifacts(store, path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to(store.root.resolve()):
        raise ValueError("file gán nhãn chứa nội dung tài liệu: chỉ ghi trong artifact_dir")
    return path


def _graph_payload(path: Path | None):
    """Payload stage `provenance` cho file gán nhãn: nơi dạy đi theo provenance đã vá (spec D13, F105/F106)."""
    if path is None:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("stage") != "provenance":
        raise ValueError(f"cần artifact stage 'provenance', file này là {payload.get('stage')!r}")
    return payload


def _json(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    try:
        if args.command == "phase-b":
            from doc2roadmap.presentation.cli.phase_b import run as run_phase_b
            _json(run_phase_b(args))
        elif args.command == "a4-gold-sheet":
            store = build_artifact_store()
            output = args.output.resolve()
            if not output.is_relative_to(store.root.resolve()):
                raise ValueError("bảng gán chứa tài liệu: chỉ ghi trong artifact_dir")
            payload = gold_items(store, args.doc_id)
            write_gold_sheet(payload, output)
            _json({"path": str(output), "items": len(payload["items"]), "sheet_id": payload["sheet_id"]})
        elif args.command == "a8-gold-sheet":
            store = build_artifact_store()
            options = {"chapter_level": args.chapter_level, "canonical_version": args.canonical_version}
            if args.list_chapters:
                _json(chapters_from_store(store, args.doc_id, **options))
                return 0
            if not args.annotator or not args.chapter:
                raise ValueError("cần --chapter và --annotator (dùng --list-chapters để xem chương)")
            code = "".join(ch for ch in args.annotator if ch.isalnum()) or "nguoi-gan"
            unit = "".join(ch if ch.isalnum() or ch == "-" else "_" for ch in args.chapter)
            default = store.root / "a8-gold" / f"{args.doc_id}-chuong-{unit}-{code}.xlsx"
            output = _inside_artifacts(store, args.output or default)
            scope = scope_from_store(store, args.doc_id, chapter=args.chapter,
                                     graph_payload=_graph_payload(args.graph), **options)
            _json(write_annotation_sheet(scope, output, annotator=args.annotator, overwrite=args.force))
        elif args.command == "a8-gold-check":
            store = build_artifact_store()
            scope = scope_from_store(store, args.doc_id, chapter=args.chapter, chapter_level=args.chapter_level,
                                     canonical_version=args.canonical_version,
                                     graph_payload=_graph_payload(args.graph))
            result = read_annotation_sheet(args.file, scope)
            summary = {"annotator": result["annotator"], "edges": len(result["edges"]),
                       "flags": len(result["flags"]), "timing": result["timing"],
                       "errors": result["errors"], "warnings": result["warnings"]}
            if args.output and not result["errors"]:
                output = _inside_artifacts(store, args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
                summary["output"] = str(output)
            _json(summary)
            return 1 if result["errors"] else 0
        elif args.command == "a8-gold-merge":
            store = build_artifact_store()
            scope = scope_from_store(store, args.doc_id, chapter=args.chapter, chapter_level=args.chapter_level,
                                     canonical_version=args.canonical_version,
                                     graph_payload=_graph_payload(args.graph))
            golds = [a8_score.load_gold(path) for path in args.gold]
            if args.file is None:
                data = adjudication_rows(scope, golds)
                unit = "".join(ch if ch.isalnum() or ch == "-" else "_" for ch in args.chapter)
                default = store.root / "a8-gold" / f"{args.doc_id}-chuong-{unit}-hoi-y.xlsx"
                output = _inside_artifacts(store, args.output or default)
                _json(write_adjudication_sheet(scope, data, output, overwrite=args.force))
                return 0
            result = read_adjudication_sheet(args.file, scope, golds)
            summary = {key: result[key] for key in
                       ("annotator", "agreed_count", "differing_count", "kept_count", "errors", "warnings")}
            summary["edges"] = len(result["edges"])
            if args.output and not result["errors"]:
                output = _inside_artifacts(store, args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
                summary["output"] = str(output)
            _json(summary)
            return 1 if result["errors"] else 0
        elif args.command == "a8-roadmap-score":
            remap_options = ({"remap_gold_ids": True, "store": build_artifact_store()}
                             if args.remap_gold_ids else {})
            report = a8_score.score_roadmap_order(args.graph, args.gold, mode=args.gold_mode, **remap_options)
            if args.output:
                store = build_artifact_store()
                output = _inside_artifacts(store, args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
                report = {**report, "output": str(output)}
            _json({key: value for key, value in report.items() if key != "violations"})
            return 0
        elif args.command == "roadmap-target":
            payload = json.loads(args.graph.read_text(encoding="utf-8"))
            result = target_roadmap(payload, args.concept)
            if args.output:
                store = build_artifact_store()
                output = _inside_artifacts(store, args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                kept = {concept["node_id"] for module in result["modules"] for concept in module["concepts"]}
                view = {
                    **payload,
                    "modules": [module for module in payload["modules"] if set(module["node_ids"]) & kept],
                    "requires_edges": [edge for edge in payload.get("requires_edges", [])
                                       if edge["source"] in kept and edge["target"] in kept],
                }
                view["modules"] = [{**module, "node_ids": [node for node in module["node_ids"] if node in kept]}
                                   for module in view["modules"]]
                output.write_text(render_roadmap_html(view), encoding="utf-8", newline="\n")
                result = {**result, "output": str(output)}
            _json(result)
            return 0
        elif args.command == "a8-score":
            store = build_artifact_store()
            remap_options = {}
            if args.gold_graph is not None and not args.remap_gold_ids:
                raise ValueError("--gold-graph cần --remap-gold-ids")
            if args.remap_gold_ids:
                remap_options = {"remap_gold_ids": True, "gold_graph_path": args.gold_graph}
            report = a8_score.score_from_store(store, args.doc_id, args.graph, args.gold,
                                               mode=args.gold_mode, samples=args.bootstrap, seed=args.seed,
                                               provenance=args.provenance, **remap_options)
            if args.output:
                output = _inside_artifacts(store, args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
                report = {**report, "output": str(output)}
            # Bảng tổ hợp bộ sinh dài; bản in gọn bỏ nó đi, JSON đầy đủ nằm ở --output.
            _json({**report, "e2": {**report["e2"], "subsets": f"{len(report['e2']['subsets'])} tổ hợp, xem --output"}})
        elif args.command == "a4-evaluate":
            store = build_artifact_store()
            gold = load_gold(args.gold, store)
            second = load_gold(args.second_gold, store) if args.second_gold else None
            artifact = store.load_canonical(args.doc_id, args.canonical_version) if args.canonical_version else store.load_latest_canonical(args.doc_id)
            _json(evaluate_canonical(artifact, gold, second,
                                     exclude_subtype_items=args.exclude_subtype_item))
        elif args.command == "a4":
            chain = "v3" if args.names_only or args.prepare else "gop"
            if args.merge_review is not None and (args.names_only or args.prepare):
                raise ValueError("--merge-review cần A4/A5 đầy đủ")
            store = build_artifact_store()
            build_options = {} if args.names_only or args.prepare else {
                "allow_spend": args.allow_spend and not args.dry_run, "dry_run": args.dry_run}
            execution_options = {}
            if args.merge_review is not None:
                import hashlib
                from doc2roadmap.application.identity_review import load_identity_review
                build_options.update(merge_review=load_identity_review(args.merge_review, doc_id=args.doc_id),
                                     merge_review_hash=hashlib.sha256(args.merge_review.read_bytes()).hexdigest())
            if args.names_only:
                use_case = Canonicalize(store)
            elif args.prepare:
                use_case = build_canonical(prepare=True, **build_options)
            else:
                if args.gold is None:
                    raise ValueError("task 06 chưa xong: cần --gold đã gán mù; dùng --prepare hoặc --names-only trước")
                gold = load_gold(args.gold, store, require_complete=True)
                if args.doc_id not in gold["documents"]:
                    if not args.no_gold_for_doc:
                        raise ValueError("bộ vàng không có tài liệu này")
                    execution_options = {
                        "a4_gold_coverage": "none",
                        "gold_sheet_id": gold["sheet_id"],
                    }
                use_case = build_canonical(**build_options)
            if args.language:
                execution_options["declared_language"] = args.language
            if args.dry_run:
                _json({"doc_id": args.doc_id, "upstream_chain": chain,
                       "phases": {phase: plan.to_dict() for phase, plan in
                                  use_case.plan(args.doc_id, **execution_options).items()}})
                return 0
            artifact, reused = use_case.execute(args.doc_id, **execution_options)
            _json({"path": str(artifact.path), "version": artifact.version, "reused": reused,
                   "stage": artifact.payload["stage"], "stats": artifact.payload["stats"],
                   "cost_summary": artifact.payload.get("cost_summary", {})})
        elif args.command == "a4-compare":
            store = build_artifact_store()
            first = store.load_canonical(args.doc_id, args.first)
            second = store.load_canonical(args.doc_id, args.second)
            _json({**compare_nodes(first.payload["nodes"], second.payload["nodes"]),
                   "redirect_count": len(second.payload["redirects"]),
                   "first_version": first.version, "second_version": second.version})
        elif args.command == 'a8-secondary-features':
            from doc2roadmap.application.use_cases.export_secondary_features import ExportSecondaryFeatures
            from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
            from doc2roadmap.infrastructure.secondary_tokenizer import VietnameseWordTokenizer

            store = JsonArtifactStore(args.artifacts) if args.artifacts else build_artifact_store()
            chunks_store = JsonArtifactStore(args.chunks_artifacts) if args.chunks_artifacts else None
            _json(ExportSecondaryFeatures(store, VietnameseWordTokenizer()).execute(
                args.doc_id, main_version=args.main_version, output_dir=args.output_dir, chunks_store=chunks_store))
        elif args.command == 'label-roles':
            use_case = build_region_roles(allow_spend=args.allow_spend and not args.dry_run)
            use_case.quality_reason = args.allow_text_quality_reason
            if args.dry_run:
                payload = use_case.plan(args.doc_id, chunks_version=args.chunks_version,
                                        transfer_from_chunks_version=args.transfer_from_chunks_version).to_dict()
            else:
                artifact,reused = use_case.execute(args.doc_id, chunks_version=args.chunks_version,
                                                   transfer_from_chunks_version=args.transfer_from_chunks_version)
                payload = {'chunks_version':artifact.version,'reused':reused,
                           'role_counts':artifact.manifest['role_counts'],
                           'warnings':artifact.manifest['role_warnings']}
            print(json.dumps(payload,ensure_ascii=False,indent=2))
        elif args.command == "ingest":
            pipeline_flags = {name: getattr(args, name) for name in PipelineConfig.__dataclass_fields__
                              if getattr(args, name) is not None}
            if args.a1 == "nhe" and (args.pdf_backend is not None or pipeline_flags):
                raise ValueError("--pdf-backend, --pdf-text-policy và cờ pipeline chỉ dùng với --a1 docling")
            _ingest(args.file, args.doc_id, strip_lines=args.strip_line, pdf_backend=args.pdf_backend,
                    heading_scheme=args.heading_scheme,
                    pipeline=PipelineConfig(**pipeline_flags) if args.a1 == "docling" else None,
                    dry_run=args.dry_run, quality_reason=args.allow_text_quality_reason, a1=args.a1)
        elif args.command == "inspect":
            _inspect(args.doc_id)
        elif args.command == "extract":
            _extract(args.doc_id, force=args.force, few_shot_path=args.few_shot, quality_reason=args.allow_text_quality_reason)
        elif args.command == "index":
            _index(args.doc_id)
        elif args.command == "a3":
            _a3(args.doc_id, few_shot_path=args.few_shot, quality_reason=args.allow_text_quality_reason)
        elif args.command == "search":
            _search(args.doc_id, args.query, args.top_k, args.stage_id)
        elif args.command == "roadmap":
            use_case, _ = build_learning_graph(allow_spend=args.allow_spend and not args.dry_run)
            if hasattr(use_case, "clusters"):
                use_case.clusters.quality_reason = args.allow_text_quality_reason
            if args.dry_run:
                _json(use_case.plan(args.doc_id, stop_after=args.stop_after))
                return 0
            artifact, reused = use_case.execute(args.doc_id, stop_after=args.stop_after)
            _json({
                "path": str(artifact.path),
                "version": artifact.version,
                "stage": artifact.payload["stage"],
                "reused": reused,
                "stats": artifact.payload.get("stats", {}),
            })
        elif args.command == "a3-report":
            _json(report_candidates(build_artifact_store(), args.doc_id))
        elif args.command == "a3-review-types":
            result = review_candidate_types(build_artifact_store(), args.doc_id)
            print("Artifact: " + ", ".join(
                f"{doc_id} v{version}" for doc_id, version in result["documents"].items()
            ))
            print("node_type | rare_doc_candidates | artifact_learnable | reviewed | reviewed_learnable | corpus_candidates | examples")
            for row in result["types"]:
                values = [row[key] for key in (
                    "node_type", "candidate_count", "artifact_learnable", "reviewed", "reviewed_learnable", "corpus_candidate_count"
                )]
                print(" | ".join(
                    "-" if value is None else str(value).lower() if isinstance(value, bool) else str(value)
                    for value in values
                ) + " | " + "; ".join(" ".join(name.split()) for name in row["examples"]))
            print(f"{len(result['types'])} kiểu hiếm; chỉ đọc, không thay quyết định hoặc artifact.")
        elif args.command == "a3-compare":
            _json(
                compare_candidate_versions(
                    build_artifact_store(), args.doc_id, args.first, args.second
                )
            )
        else:
            _json(
                evaluate_gold(
                    build_artifact_store(),
                    args.doc_id,
                    args.gold,
                    candidate_version=args.candidate_version,
                )
            )
        return 0
    except Exception as error:
        print(f"lỗi: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
