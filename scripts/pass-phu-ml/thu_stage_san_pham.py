"""Offline development-only stage smoke/timing. No labels, scoring, or upstream API calls."""
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402
from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer  # noqa: E402
from doc2roadmap.infrastructure.secondary_tokenizer import VietnameseWordTokenizer  # noqa: E402

DEVELOPMENT = {"doc-1": ("artifacts/v3-r12-final-evaluation", 1),
               "nhap-mon-ml": ("artifacts/v3-r12-final-evaluation", 1),
               "xstk-ch3-1": ("artifacts", 41), "doc-4": ("artifacts", 7)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("doc", choices=tuple(DEVELOPMENT))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, version = DEVELOPMENT[args.doc]
    main_artifact = JsonArtifactStore(Path(source)).load_graph(args.doc, version)
    store = JsonArtifactStore(args.output)
    # Read pinned input chunks from their original store; write graphs only into evaluation output.
    store.load_chunks = JsonArtifactStore(Path("artifacts")).load_chunks
    stage = BuildSecondaryMLEdges(store, LightGBMSecondaryScorer(), VietnameseWordTokenizer())
    plan = stage.plan(args.doc, upstream=main_artifact).to_dict()
    assert plan["calls_estimate"] == 0 and plan["usd_estimate"] == 0
    started = perf_counter()
    artifact, reused = stage.execute(args.doc, upstream=main_artifact)
    assert all(not edge.get("soft") and edge["prerequisite_kind"] == "can_de_hieu"
               and edge["evidence_kind"] == "trong_dinh_nghia" for edge in artifact.payload["secondary_edges"])
    result = {"doc": args.doc, "version": artifact.version, "reused": reused,
              "seconds": perf_counter() - started, "stats": artifact.payload["stats"],
              "calls": artifact.manifest["stats"]["model_calls"],
              "secondary_usd": artifact.payload["cost_summary"]["secondary_usd"]}
    print(json.dumps(result, ensure_ascii=False), flush=True)
    again, reused = stage.execute(args.doc, upstream=main_artifact)
    assert reused and again.version == artifact.version
    return 0


if __name__ == "__main__":
    sys.exit(main())
