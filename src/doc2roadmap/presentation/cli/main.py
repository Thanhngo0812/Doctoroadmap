from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc2roadmap.composition import build_ingest, build_inspect


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doc2roadmap")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="parse và cắt một PDF/DOCX")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--doc-id", required=True)
    inspect = commands.add_parser("inspect", help="xem cây section và window đã lưu")
    inspect.add_argument("--doc-id", required=True)
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


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args(argv)
    try:
        if args.command == "ingest":
            _ingest(args.file, args.doc_id)
        else:
            _inspect(args.doc_id)
        return 0
    except Exception as error:
        print(f"lỗi: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
