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
    roles.add_argument('--dry-run', action='store_true')
    roles.add_argument('--allow-spend', action='store_true')
    canonical = commands.add_parser("a4", help="hợp nhất thực thể và mô tả chuẩn (cần --gold); --names-only/--prepare không gọi mô hình phán")
    canonical.add_argument("--doc-id", required=True)
    mode = canonical.add_mutually_exclusive_group()
    mode.add_argument("--names-only", action="store_true", help="chỉ lớp tên, không mạng")
    mode.add_argument("--prepare", action="store_true", help="chỉ đề cử bằng embedding, chưa phán")
    canonical.add_argument("--gold", type=Path, help="bộ vàng đã gán mù, bắt buộc trước khi gọi LLM")
    canonical.add_argument("--language", choices=("vi", "en"), help="khai ngôn ngữ tài liệu cho A5")
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
    roadmap_score = commands.add_parser(
        "a8-roadmap-score",
        help="chấm thứ tự lộ trình: tau so mục lục và tỉ lệ vi phạm cạnh vàng; không gọi mô hình")
    roadmap_score.add_argument("--graph", type=Path, required=True,
                               help="graph.json ở stage stages")
    roadmap_score.add_argument("--gold", type=Path, action="append", default=[],
                               help="JSON từ a8-gold-check; lặp lại cho người gán thứ hai")
    roadmap_score.add_argument("--gold-mode", choices=("union", "intersection"), default="union")
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
    ingest.add_argument("--pdf-backend", choices=["docling-parse", "pypdfium2"], default="docling-parse",
                        help="bộ đọc PDF; pypdfium2 cho PDF font tiếng Việt cũ bị tách rời âm tiết")
    ingest.add_argument("--heading-scheme", choices=["vn-textbook"], default=None,
                        help="thang tiêu đề Phần → Chương → I- → 1. → a) của giáo trình tiếng Việt")
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
        choices=("clusters", "mentions", "provenance", "edges", "stages"),
        default="stages",
        help="dừng sau stage đã chọn; clusters/mentions cần embedding nếu thiếu cache, provenance có gọi LLM",
    )
    roadmap.add_argument("--allow-spend", action="store_true",
                         help="cho phép gọi mô hình trả tiền; thiếu cờ thì lệnh dừng ở stage đầu tiên định chi")
    roadmap.add_argument("--dry-run", action="store_true",
                         help="chỉ đọc cache/checkpoint và dự toán mọi stage; không gọi mô hình hoặc ghi artifact")
    roadmap.add_argument("--identity-review", type=Path, default=None,
                         help="JSON quyết định duyệt danh tính (T5) của tài liệu; quyết định người thắng phán mô hình")
    return parser


def _ingest(path: Path, doc_id: str, *, strip_lines: list[str] | None = None,
            pdf_backend: str = "docling-parse", heading_scheme: str | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"không đọc được file: {path}")
    use_case, settings = build_ingest(pdf_backend)
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


def _extract(
    doc_id: str, *, force: bool = False, few_shot_path: Path | None = None
) -> None:
    use_case, settings = build_extract(few_shot_path=few_shot_path)
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


def _a3(doc_id: str, *, few_shot_path: Path | None = None) -> None:
    extraction, index, settings = build_a3(few_shot_path=few_shot_path)
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
        if args.command == "a4-gold-sheet":
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
            report = a8_score.score_roadmap_order(args.graph, args.gold, mode=args.gold_mode)
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
            report = a8_score.score_from_store(store, args.doc_id, args.graph, args.gold,
                                               mode=args.gold_mode, samples=args.bootstrap, seed=args.seed,
                                               provenance=args.provenance)
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
            store = build_artifact_store()
            execution_options = {}
            if args.names_only:
                use_case = Canonicalize(store)
            elif args.prepare:
                use_case = build_canonical(prepare=True)
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
                use_case = build_canonical()
            if args.language:
                execution_options["declared_language"] = args.language
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
        elif args.command == 'label-roles':
            use_case = build_region_roles(allow_spend=args.allow_spend and not args.dry_run)
            if args.dry_run:
                payload = use_case.plan(args.doc_id, chunks_version=args.chunks_version).to_dict()
            else:
                artifact,reused = use_case.execute(args.doc_id, chunks_version=args.chunks_version)
                payload = {'chunks_version':artifact.version,'reused':reused,
                           'role_counts':artifact.manifest['role_counts'],
                           'warnings':artifact.manifest['role_warnings']}
            print(json.dumps(payload,ensure_ascii=False,indent=2))
        elif args.command == "ingest":
            _ingest(args.file, args.doc_id, strip_lines=args.strip_line, pdf_backend=args.pdf_backend,
                    heading_scheme=args.heading_scheme)
        elif args.command == "inspect":
            _inspect(args.doc_id)
        elif args.command == "extract":
            _extract(args.doc_id, force=args.force, few_shot_path=args.few_shot)
        elif args.command == "index":
            _index(args.doc_id)
        elif args.command == "a3":
            _a3(args.doc_id, few_shot_path=args.few_shot)
        elif args.command == "search":
            _search(args.doc_id, args.query, args.top_k, args.stage_id)
        elif args.command == "roadmap":
            review = None
            if args.identity_review is not None:
                from doc2roadmap.application.use_cases.judge_identity import load_identity_review

                review = load_identity_review(args.identity_review, doc_id=args.doc_id)
            use_case, _ = build_learning_graph(allow_spend=args.allow_spend and not args.dry_run, identity_review=review)
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
