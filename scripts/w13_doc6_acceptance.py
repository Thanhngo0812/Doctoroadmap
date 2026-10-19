"""Run the approved W-13 doc-6 acceptance in its own artifact store."""
import argparse
import json
import shutil
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from doc2roadmap.composition_build import build_document_runner
from doc2roadmap.config import Settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-spend", action="store_true")
    args = parser.parse_args()
    root = Path("artifacts/w13-doc6-acceptance-2026-10-19")
    store = root / "store"
    if not store.exists():
        store.mkdir(parents=True)
        for kind in ("parse_tree", "chunks", "candidates", "retrieval", "canonical", "graph", "checkpoints/graph"):
            source = Path("artifacts") / kind / "doc-6"
            if source.exists():
                shutil.copytree(source, store / kind / "doc-6")
    attempt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    settings = Settings(artifact_dir=store, llm_transport="vertex")
    with ExitStack() as stack:
        if not args.allow_spend:
            for name in ("doc2roadmap.infrastructure.llm.gemini.urlopen",
                         "doc2roadmap.infrastructure.embedding.gemini.urlopen",
                         "doc2roadmap.infrastructure.google_auth.VertexCredentials.headers"):
                stack.enter_context(patch(name, side_effect=AssertionError("cache-only acceptance forbids network")))
        runner = build_document_runner(settings, allow_spend=args.allow_spend)

        def event(step, detail):
            row = {"at": datetime.now(timezone.utc).isoformat(), "step": step, **detail}
            print(json.dumps(row, ensure_ascii=False), flush=True)
            with (root / f"{attempt}-progress.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

        for name in ("label_roles", "a3", "canonical", "roadmap", "learning_prep"):
            original = getattr(runner.pipeline, name)

            def traced(*values, _name=name, _original=original, **kwargs):
                event(_name, {"status": "started", "usage": runner.pipeline.usage()})
                result = _original(*values, **kwargs)
                event(_name, {"status": "completed", "details": result, "usage": runner.pipeline.usage()})
                return result

            setattr(runner.pipeline, name, traced)
        result = runner.execute(Path("doc-6.pdf"), "doc-6", progress=event)
        payload = {"allow_spend": args.allow_spend, **result.to_dict()}
        (root / f"{attempt}-result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
        return 0 if result.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
