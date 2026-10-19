from __future__ import annotations

import json

from doc2roadmap.composition_build import build_document_runner


def run(args) -> int:
    runner = build_document_runner(allow_spend=args.allow_spend and not args.dry_run)
    result = runner.execute(args.file, args.doc_id, language="vi", dry_run=args.dry_run)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.to_dict()["status"] in {"succeeded", "dry_run"} else 1
