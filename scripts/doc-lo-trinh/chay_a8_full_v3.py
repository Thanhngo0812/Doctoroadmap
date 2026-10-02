"""Vé 12: pass phụ đầy đủ rồi A9, nhãn khái niệm, A10, tên module; mặc định dry-run.

Chỉ đọc pass chính v1 từ kho v3-r12-quote-evaluation. Mọi stage mới nằm trong
v3-r12-final-evaluation. --allow-spend cần Vertex và có trần ledger 50 USD.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError

from google.auth.exceptions import RefreshError, TransportError as AuthTransportError

from chay_danh_tinh_v3 import EvaluationStore, MeteredGemini
from doc2roadmap.application.ports.extraction import ModelTransportError
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges
from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
from doc2roadmap.application.use_cases.name_modules import NameModules
from doc2roadmap.application.use_cases.validate_graph import ValidateGraph
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.llm.rate_limit import AdaptiveModelLimiter

DOCS = ("doc-3", "doc-6", "naive-bayes", "nhap-mon-ml", "doc-1", "doc-2")
INPUT = Path("artifacts/v3-r12-quote-evaluation")
OUTPUT = Path("artifacts/v3-r12-final-evaluation")
MAX_OUTAGE_SECONDS = 12 * 60 * 60
RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}


class FinalStore(EvaluationStore):
    def load_graph(self, doc_id, version):
        # v1 in the source repo is the vector artifact. Later input vector
        # versions can also live only in the source repo (for example v13).
        if version >= 2:
            try:
                return self.output.load_graph(doc_id, version)
            except FileNotFoundError:
                pass
        return self.base.load_graph(doc_id, version)


def pinned_main(source, output, doc_id, *, write):
    original = source.load_graph(doc_id, 1)
    if original.payload.get("stage") != "edges" or not original.payload.get("main_complete"):
        raise ValueError(f"{doc_id}: thiếu pass chính hoàn chỉnh đã chốt")
    if not write:
        return original
    manifest = original.manifest
    copied = output.save_graph(
        doc_id, manifest["source_hash"], manifest["config_hash"], manifest["config"], original.payload,
        upstream_version=manifest["upstream_version"],
        manifest_fields={key: manifest[key] for key in ("stage", "edge_pass", "complete", "stats", "routing", "llm_transport")},
    )
    if copied.version != 1 or copied.manifest["config_hash"] != manifest["config_hash"]:
        raise ValueError(f"{doc_id}: kho cuối chứa pass chính khác")
    return copied


def retry_temporary(operation, *, stage, event_path, progress):
    """Wait through a temporary provider outage; the stage reloads its checkpoint on each call."""
    first_failure, last_progress, delay = None, None, 30
    while True:
        try:
            return operation()
        except (ModelTransportError, AuthTransportError, RefreshError) as error:
            if isinstance(error, AuthTransportError):
                detail = "Google auth transport"
            elif isinstance(error, RefreshError):
                if not error.retryable:
                    raise
                detail = "Google auth refresh retryable"
            else:
                cause = error.__cause__
                if isinstance(cause, HTTPError):
                    if cause.code not in RETRYABLE_HTTP:
                        raise
                    detail = f"HTTP {cause.code}"
                elif isinstance(cause, URLError):
                    detail = f"URLError: {cause.reason}"
                elif isinstance(cause, TimeoutError):
                    detail = "TimeoutError"
                else:
                    raise
            now = monotonic()
            completed = progress()
            if first_failure is None or completed > last_progress:
                first_failure = now
                delay = 30
            last_progress = completed
            wait = min(delay, MAX_OUTAGE_SECONDS - (now - first_failure))
            event = {"time_utc": datetime.now(timezone.utc).isoformat(), "stage": stage,
                     "cause": detail, "wait_seconds": max(wait, 0)}
            event_path.parent.mkdir(parents=True, exist_ok=True)
            with event_path.open("a", encoding="utf-8") as log:
                log.write(json.dumps(event, ensure_ascii=False) + "\n")
            print(f"{stage}: {detail}; {'dừng vì lỗi kéo dài không có tiến triển' if wait <= 0 else f'chờ {wait:.0f}s rồi tiếp tục từ checkpoint'}", flush=True)
            if wait <= 0:
                raise
            sleep(wait)
            delay = min(delay * 2, 300)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", choices=DOCS)
    parser.add_argument("--allow-spend", action="store_true")
    parser.add_argument("--max-usd", type=float, default=50.0)
    args = parser.parse_args()
    if not 0 < args.max_usd <= 50:
        parser.error("trần chi pass phụ + đặt tên: tối đa 50 USD")
    settings = Settings()
    if settings.llm_transport != "vertex":
        raise ValueError("lượt này chỉ chạy qua Vertex")
    source = JsonArtifactStore(INPUT)
    output = JsonArtifactStore(OUTPUT)
    store = FinalStore(JsonArtifactStore(settings.artifact_dir), output)
    key = settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else "dry-run-no-key"
    ledger = OUTPUT / ("llm-ledger.jsonl" if args.allow_spend else "llm-ledger.json")
    limiter = AdaptiveModelLimiter(
        settings.llm_max_in_flight,
        settings.llm_tpm_budget,
        requests_per_minute=settings.llm_rpm_budget,
    )

    def model(max_output_tokens):
        raw = MeteredGemini(key, max_usd=args.max_usd, ledger_path=ledger,
                            max_output_tokens=max_output_tokens, transport=settings.llm_transport,
                            vertex_project=settings.vertex_project, vertex_location=settings.vertex_location,
                            limiter=limiter)
        return SpendGuard(raw, allowed=args.allow_spend)

    summary_path = OUTPUT / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    for doc_id in DOCS:
        if args.doc and doc_id != args.doc:
            continue
        main_artifact = pinned_main(source, output, doc_id, write=args.allow_spend)
        secondary_model = model(settings.extraction_max_output_tokens)
        secondary = BuildSecondaryEdges(store, secondary_model,
                                        concurrency=settings.llm_max_in_flight,
                                        window_pairs=settings.secondary_window_pairs,
                                        generation=main_artifact.manifest["config"]["generation"])
        plan = secondary.plan(doc_id, upstream=main_artifact)
        print(doc_id, "secondary", json.dumps(plan.to_dict(), ensure_ascii=False), flush=True)
        if not args.allow_spend:
            continue
        retry_log = OUTPUT / "transport-retries.jsonl"
        edges, _ = retry_temporary(lambda: secondary.execute(doc_id, upstream=main_artifact),
                                   stage=f"{doc_id}:secondary", event_path=retry_log,
                                   progress=lambda: len((store.load_checkpoint(doc_id, plan.checkpoint_id) or {}).get(
                                       "completed_secondary_pairs", [])))
        validated, _ = ValidateGraph(store).execute(doc_id, upstream=edges)
        labels_model = model(512)
        labels_stage = NameConceptLabels(store, labels_model, concurrency=settings.llm_max_in_flight)
        labels, _ = retry_temporary(lambda: labels_stage.execute(doc_id, upstream=validated),
                                    stage=f"{doc_id}:concept-labels", event_path=retry_log,
                                    progress=lambda: sum(not row.get("reserved") for row in labels_model.ledger))
        roadmap, _ = BuildRoadmap(store, stage_cap=settings.roadmap_stage_cap).execute(doc_id, upstream=labels)
        titles_model = model(128)
        titles_stage = NameModules(store, titles_model, concurrency=settings.llm_max_in_flight)
        titled, _ = retry_temporary(lambda: titles_stage.execute(doc_id, upstream=roadmap),
                                    stage=f"{doc_id}:module-titles", event_path=retry_log,
                                    progress=lambda: sum(not row.get("reserved") for row in titles_model.ledger))
        summary[doc_id] = {"main": str(main_artifact.path), "secondary": str(edges.path),
                           "validated": str(validated.path), "labels": str(labels.path),
                           "stages": str(titled.path)}
        output._write(summary_path, summary)
        print(doc_id, json.dumps(summary[doc_id], ensure_ascii=False), flush=True)
    if args.allow_spend:
        rows = model(1).ledger
        print("spent/reserved USD", round(sum(row["usd"] for row in rows), 6), flush=True)
        print("limiter", json.dumps(limiter.snapshot(), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
