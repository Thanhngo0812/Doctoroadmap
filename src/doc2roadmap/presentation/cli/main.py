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
)
from doc2roadmap.application.use_cases.report_a3 import review_candidate_types
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.domain.canonical import compare_nodes
from doc2roadmap.application.use_cases.a4_gold import gold_items, write_gold_sheet, load_gold, evaluate_canonical


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doc2roadmap")
    commands = parser.add_subparsers(dest="command", required=True)
    canonical = commands.add_parser("a4", help="hợp nhất thực thể và mô tả chuẩn (cần --gold); --names-only/--prepare không gọi mô hình phán")
    canonical.add_argument("--doc-id", required=True)
    mode = canonical.add_mutually_exclusive_group()
    mode.add_argument("--names-only", action="store_true", help="chỉ lớp tên, không mạng")
    mode.add_argument("--prepare", action="store_true", help="chỉ đề cử bằng embedding, chưa phán")
    canonical.add_argument("--gold", type=Path, help="bộ vàng đã gán mù, bắt buộc trước khi gọi LLM")
    comparison = commands.add_parser("a4-compare", help="so hai phiên bản canonical")
    comparison.add_argument("--doc-id", required=True)
    comparison.add_argument("--first", type=int, required=True)
    comparison.add_argument("--second", type=int, required=True)
    gold_sheet = commands.add_parser("a4-gold-sheet", help="sinh HTML gán mù từ artifact đề cử")
    gold_sheet.add_argument("--doc-id", action="append", required=True)
    gold_sheet.add_argument("--output", type=Path, default=Path("artifacts/a4-gold.html"))
    evaluation = commands.add_parser("a4-evaluate", help="chấm canonical trên bộ vàng")
    evaluation.add_argument("--doc-id", required=True)
    evaluation.add_argument("--gold", type=Path, required=True)
    evaluation.add_argument("--second-gold", type=Path)
    evaluation.add_argument("--canonical-version", type=int)
    evaluation.add_argument("--exclude-subtype-item", action="append", default=[])
    ingest = commands.add_parser("ingest", help="parse và cắt một PDF/DOCX")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--doc-id", required=True)
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
        help="dừng sau stage đã chọn; mentions không gọi mô hình, provenance có gọi ít",
    )
    return parser


def _ingest(path: Path, doc_id: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"không đọc được file: {path}")
    use_case, settings = build_ingest()
    summary = use_case.execute(
        path.read_bytes(),
        path.name,
        doc_id,
        max_tokens=settings.max_tokens,
        max_table_tokens=settings.max_table_tokens,
        hard_cap_tokens=settings.hard_cap_tokens,
        target_tokens=settings.target_tokens,
        sentence_overlap=settings.sentence_overlap,
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
    if summary.structure_warnings:
        print("Cảnh báo:")
        for warning in summary.structure_warnings:
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
        elif args.command == "a4-evaluate":
            store = build_artifact_store()
            gold = load_gold(args.gold, store)
            second = load_gold(args.second_gold, store) if args.second_gold else None
            artifact = store.load_canonical(args.doc_id, args.canonical_version) if args.canonical_version else store.load_latest_canonical(args.doc_id)
            _json(evaluate_canonical(artifact, gold, second,
                                     exclude_subtype_items=args.exclude_subtype_item))
        elif args.command == "a4":
            store = build_artifact_store()
            if args.names_only:
                use_case = Canonicalize(store)
            elif args.prepare:
                use_case = build_canonical(prepare=True)
            else:
                if args.gold is None:
                    raise ValueError("task 06 chưa xong: cần --gold đã gán mù; dùng --prepare hoặc --names-only trước")
                gold = load_gold(args.gold, store, require_complete=True)
                if args.doc_id not in gold["documents"]:
                    raise ValueError("bộ vàng không có tài liệu này")
                use_case = build_canonical()
            artifact, reused = use_case.execute(args.doc_id)
            _json({"path": str(artifact.path), "version": artifact.version, "reused": reused,
                   "stage": artifact.payload["stage"], "stats": artifact.payload["stats"]})
        elif args.command == "a4-compare":
            store = build_artifact_store()
            first = store.load_canonical(args.doc_id, args.first)
            second = store.load_canonical(args.doc_id, args.second)
            _json({**compare_nodes(first.payload["nodes"], second.payload["nodes"]),
                   "redirect_count": len(second.payload["redirects"]),
                   "first_version": first.version, "second_version": second.version})
        elif args.command == "ingest":
            _ingest(args.file, args.doc_id)
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
            use_case, _ = build_learning_graph()
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
