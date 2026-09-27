"""Liệt kê riêng lớp vai trò cấu trúc; để gán đủ sáu vai trò, dùng `doc2roadmap label-roles`.

python scripts/doc-lo-trinh/vai_tro_vung.py --doc-id doc-1 [--chunk-version 5] [--save]
Không đổi text, ID, cửa sổ hay offset. Các stage đang ghim chunk version cũ vẫn dùng bản cũ.
"""
import argparse
import json
from collections import Counter

from doc2roadmap.composition import build_artifact_store
from doc2roadmap.application.use_cases.ingest_document import refresh_chunk_roles
from doc2roadmap.domain.chunking import assign_section_roles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", required=True)
    parser.add_argument("--chunk-version", type=int)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    store = build_artifact_store()
    if args.save:
        chunks = refresh_chunk_roles(store, args.doc_id, version=args.chunk_version)
    else:
        chunks = (store.load_chunks(args.doc_id, args.chunk_version) if args.chunk_version is not None
                  else store.load_latest_chunks(args.doc_id))
        assign_section_roles(chunks.result.sections, chunks.result.chunks)
    print(json.dumps({"doc_id": args.doc_id, "chunks_version": chunks.version, "saved": args.save,
        "section_counts": dict(Counter(s.role for s in chunks.result.sections)),
        "chunk_counts": dict(Counter(c.role for c in chunks.result.chunks)),
        "sections": [{"section_id": s.section_id, "title": s.title, "role": s.role,
                      "order_index": s.order_index} for s in chunks.result.sections]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
