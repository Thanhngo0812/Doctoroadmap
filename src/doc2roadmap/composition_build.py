from __future__ import annotations

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from pathlib import Path

from doc2roadmap.application.build_usage import BuildUsage, MeteredEmbedding, MeteredModel
from doc2roadmap.application.extraction_prompt import load_prompts
from doc2roadmap.application.ports.build import BuildRejected
from doc2roadmap.application.spend_guard import SpendGuard
from doc2roadmap.config import Settings
from doc2roadmap.domain.chunking import CHUNK_ALGORITHM_ID, ROLE_ALGORITHM_ID
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.artifacts.phase_b_store import JsonPhaseBStore
from doc2roadmap.infrastructure.embedding import GeminiEmbedding
from doc2roadmap.infrastructure.llm import GeminiEntityExtractor
from doc2roadmap.infrastructure.llm.rate_limit import AdaptiveModelLimiter
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser
from doc2roadmap.infrastructure.parsing.pdf_scope import require_native_pdf
from doc2roadmap.infrastructure.parsing.nhe_parser import MODEL_HASHES
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter
from doc2roadmap.application.use_cases import ExtractEntities, IndexDocument, IngestDocument


_BUILD_POLICY = {"reader_policy": "nhe-pdf-docling-docx-pypdfium2-v1",
                 "scan_min_chars_per_page": 150, "scan_max_empty_page_ratio": .5,
                 "vi_min_diacritic_ratio": .01,
                 "chunk_algorithm": CHUNK_ALGORITHM_ID, "role_algorithm": ROLE_ALGORITHM_ID,
                 "reader_models": MODEL_HASHES,
                 "chain": "roles+a3+a3-prime+gop+roadmap+a12+concept-index+formulas-v1"}


def _pipeline_version(settings):
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                text=True, check=True, cwd=Path(__file__).resolve().parents[2]).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    values = {"settings": settings.model_dump(mode="json", exclude={"gemini_api_key", "artifact_dir"}),
              "build_policy": _BUILD_POLICY}
    config_hash = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return f"{commit}:{config_hash}"


class BuildTracePhaseBStore:
    """Phase B store seen by one build: usage rows it writes are traces, not spend.

    Every `append_usage` row gets `counted_in = "build"`; all other methods go straight to the wrapped store.
    The build's spend is the delta of `DocumentPipeline.usage()` (provider tokens through the meters).
    Rule: every sum of provider spend (receipts, ledgers, reports, admin spend tables) must not add rows whose
    `counted_in = "build"`. `DailySpendGuard` is unaffected: it only counts lecture, quiz, assistant and document rows, so build
    rows never reach the daily caps.
    """

    def __init__(self, store):
        self._store = store

    def append_usage(self, row):
        self._store.append_usage({**row, "counted_in": "build"})

    def __getattr__(self, name):
        return getattr(self._store, name)


class DocumentPipeline:
    _injected_phase_b_store = None

    def __init__(self, settings, *, allow_spend, phase_b_store=None):
        self.settings, self.allow_spend = settings, allow_spend
        self._injected_phase_b_store = phase_b_store
        self.store = JsonArtifactStore(settings.artifact_dir)
        self.usage_meter = BuildUsage()
        self.limiter = AdaptiveModelLimiter(settings.llm_max_in_flight, settings.llm_tpm_budget,
                                            requests_per_minute=settings.llm_rpm_budget)
        self.embedding = GeminiEmbedding(
            settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else
            ("dry-run-no-key" if settings.llm_transport == "developer_api" else None),
            model=settings.embedding_model_id, output_dimensionality=settings.embedding_dimensions,
            timeout=settings.gemini_timeout_seconds, max_retries=settings.gemini_max_retries,
            transport=settings.llm_transport, vertex_project=settings.vertex_project,
            vertex_location=settings.vertex_location, limiter=self.limiter)
        self.metered_embedding = MeteredEmbedding(self.embedding, self.usage_meter)
        self.embedding_guard = SpendGuard(self.metered_embedding, allowed=allow_spend)
        self.parser = DoclingParser("pypdfium2")
        counter = SentencePieceTokenCounter(settings.tokenizer_model, settings.tokenizer_id)
        self.ingest = IngestDocument(self.parser, self.store, counter, UnicodeSentenceSplitter(),
                                     allow_backend_fallback=False, pdf_scope_validator=require_native_pdf)
        self._extractor = lambda model_id, **kwargs: GeminiEntityExtractor(
            settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else
            ("dry-run-no-key" if settings.llm_transport == "developer_api" else None), model_id,
            timeout_seconds=settings.gemini_timeout_seconds, max_retries=settings.gemini_max_retries,
            transport=settings.llm_transport, vertex_project=settings.vertex_project,
            vertex_location=settings.vertex_location, limiter=self.limiter, **kwargs)

    def _phase_b_store(self):
        store = self._injected_phase_b_store
        if store is None:
            store = JsonPhaseBStore(self.settings.artifact_dir / "phase_b" / "live.json")
        return BuildTracePhaseBStore(store)

    def read(self, file_path, doc_id):
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            try:
                require_native_pdf(path.read_bytes())
            except ValueError as exc:
                raise BuildRejected("ban_quet", str(exc)) from exc
        if path.suffix.lower() == ".pdf":
            from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser
            self.ingest.parser = NheParser()
        elif path.suffix.lower() == ".docx":
            self.ingest.parser = DoclingParser("pypdfium2")
        try:
            summary = self.ingest.execute(path.read_bytes(), path.name, doc_id,
                max_tokens=self.settings.max_tokens, max_table_tokens=self.settings.max_table_tokens,
                hard_cap_tokens=self.settings.hard_cap_tokens, target_tokens=self.settings.target_tokens,
                sentence_overlap=self.settings.sentence_overlap)
        except ValueError as exc:
            if "chất lượng chữ" in str(exc):
                raise BuildRejected("chu_loi", str(exc)) from exc
            raise
        chunks = self.store.load_chunks(doc_id, summary.chunk_version)
        from doc2roadmap.application.use_cases.ingest_document import require_text_quality
        try:
            require_text_quality(chunks, store=self.store)
        except ValueError as exc:
            raise BuildRejected("chu_loi", str(exc)) from exc
        warnings = chunks.manifest.get("text_quality", {}).get("warnings", [])
        if warnings:
            raise BuildRejected("chu_loi", "; ".join(warnings))
        try:
            parsed = self.store.load_parse(doc_id, summary.parse_version)
            page_count = int(parsed.tree.parse_stats.get("page_count", 0))
            if page_count:
                pages = [""] * page_count
                for node in parsed.tree.nodes:
                    if node.page is not None and 1 <= node.page <= page_count:
                        pages[node.page - 1] += node.text
            else:
                pages = [" ".join(node.text for node in parsed.tree.nodes)]
        except FileNotFoundError:
            pages = []
        if not pages and path.suffix.lower() == ".docx":
            pages = [" ".join(chunk.text for chunk in chunks.result.chunks)]
        if not pages:
            raise BuildRejected("ban_quet", "Không lấy được nội dung trang sau khi đọc tài liệu")
        return {"page_texts": pages, "chunks_version": summary.chunk_version,
                "parse_version": summary.parse_version, "chunk_count": summary.chunk_count,
                "a4_gold_coverage": "none"}

    def label_roles(self, doc_id):
        from doc2roadmap.application.use_cases.label_chunk_roles import LabelChunkRoles
        settings = self.settings
        model = MeteredModel(self._extractor(settings.roadmap_model_id, temperature=0.0,
            max_output_tokens=16384), self.usage_meter)
        artifact, reused = LabelChunkRoles(self.store, model, allow_spend=self.allow_spend).execute(doc_id)
        return {"chunks_version": artifact.version, "reused": reused}

    def a3(self, doc_id):
        settings = self.settings
        extraction = ExtractEntities(self.store,
            SpendGuard(MeteredModel(self._extractor(settings.extraction_model_id,
                temperature=settings.extraction_temperature, max_output_tokens=settings.extraction_max_output_tokens),
                self.usage_meter), allowed=self.allow_spend),
            self.embedding_guard,
            generation={"temperature": settings.extraction_temperature,
                        "max_output_tokens": settings.extraction_max_output_tokens},
            counter=SentencePieceTokenCounter(settings.tokenizer_model, settings.tokenizer_id),
            prompts=load_prompts(settings.extraction_few_shot))
        index = IndexDocument(self.store, self.embedding_guard)
        contexts = [copy_context(), copy_context()]
        with ThreadPoolExecutor(max_workers=2) as pool:
            extracted, indexed = [future.result() for future in (
                pool.submit(contexts[0].run, extraction.execute, doc_id),
                pool.submit(contexts[1].run, index.execute, doc_id),
            )]
        return {"candidate_version": extracted.artifact_version, "retrieval_version": indexed.artifact_version,
                "a3_reused": extracted.reused, "a3_prime_reused": indexed.reused}

    def canonical(self, doc_id, language):
        from doc2roadmap.application.use_cases.canonicalize import Canonicalize
        from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning
        s = self.settings
        guarded_embedding = SpendGuard(self.metered_embedding, allowed=self.allow_spend)
        def model(model_id, anchor=False):
            return SpendGuard(MeteredModel(self._extractor(model_id,
                temperature=0.0 if anchor else s.extraction_temperature,
                max_output_tokens=2048 if anchor else s.extraction_max_output_tokens), self.usage_meter),
                allowed=self.allow_spend)
        reasoning = CanonicalReasoning(model(s.merge_model_id), model(s.description_model_id),
            generation={"temperature": s.extraction_temperature, "max_output_tokens": s.extraction_max_output_tokens},
            language_rule=s.canonical_language_rule, batch_size=s.canonical_batch_size,
            concurrency=s.canonical_concurrency,
            counter=SentencePieceTokenCounter(s.tokenizer_model, s.tokenizer_id))
        canonicalizer = Canonicalize(self.store, guarded_embedding,
            graph_config={"k": s.merge_neighbors, "ngram_threshold": s.merge_ngram_threshold,
                          "resolution": s.merge_resolution, "seed": s.merge_seed, "cap": s.merge_cluster_cap},
            reasoning=reasoning, anchor_model=model(s.roadmap_model_id, anchor=True))
        artifact, reused = canonicalizer.execute(doc_id, a4_gold_coverage="none", gold_sheet_id=None,
                                                 declared_language=language)
        return {"canonical_version": artifact.version, "reused": reused,
                "a4_gold_coverage": "none"}

    def roadmap(self, doc_id):
        from doc2roadmap.application.use_cases import (
            BuildClusters, BuildLearningGraph, BuildMainEdges, BuildMentions,
            BuildRoadmap, BuildSecondaryEdges, ValidateGraph,
        )
        from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges
        from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels
        from doc2roadmap.application.phase_b.naming import NameModulesB
        from doc2roadmap.application.stage_measurements import measure_stage
        from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer
        from doc2roadmap.infrastructure.secondary_tokenizer import VietnameseWordTokenizer
        s = self.settings
        concurrency = s.llm_max_in_flight if s.llm_transport == "vertex" else s.roadmap_concurrency
        model = lambda limit: SpendGuard(MeteredModel(self._extractor(s.roadmap_model_id, temperature=0.0,
            max_output_tokens=limit), self.usage_meter), allowed=self.allow_spend)
        generation = {"temperature": 0.0, "max_output_tokens": s.extraction_max_output_tokens}
        secondary = (BuildSecondaryMLEdges(self.store, LightGBMSecondaryScorer(), VietnameseWordTokenizer())
                     if s.secondary_mode == "ml" else BuildSecondaryEdges(self.store, model(s.extraction_max_output_tokens),
                     concurrency=concurrency, window_pairs=s.secondary_window_pairs, generation=generation))
        titles = NameModulesB(self.store, model(512), concurrency=concurrency,
            phase_b_store=self._phase_b_store(), allow_spend=self.allow_spend)
        titles.execute = measure_stage(titles.execute)
        runner = BuildLearningGraph(
            BuildClusters(self.store, self.embedding_guard, semantic_neighbors=s.topic_neighbors,
                edge_quantile=s.topic_edge_quantile, resolution=s.topic_resolution,
                seed=s.topic_seed, concept_cap=s.topic_cluster_cap),
            BuildMentions(self.store, self.embedding_guard, dense_top_k=s.mention_dense_top_k,
                dense_min_z=s.mention_dense_min_z, pair_cluster_top_k=s.mention_pair_cluster_top_k,
                common_name_fraction=s.mention_common_name_fraction),
            BuildMainEdges(self.store, model(s.extraction_max_output_tokens),
                single_session_limit=s.roadmap_single_session_limit, parallel_sessions=s.roadmap_main_parallel,
                definition_before=s.a8_definition_before, definition_after=s.a8_definition_after,
                concurrency=concurrency, generation=generation), secondary, ValidateGraph(self.store),
            BuildRoadmap(self.store, stage_cap=s.roadmap_stage_cap), titles,
            NameConceptLabels(self.store, model(512), concurrency=concurrency))
        artifact, reused = runner.execute(doc_id)
        return {"graph_version": artifact.version, "reused": reused}

    def learning_prep(self, file_path, doc_id, graph_version):
        from doc2roadmap.application.phase_b.concept_index import IndexConcepts
        from doc2roadmap.composition_phase_b import PhaseBRuntime
        phase = PhaseBRuntime(settings=self.settings, allow_spend=self.allow_spend,
                              store=self._phase_b_store(),
                              mode="gemini" if self.allow_spend else "offline")
        a12 = phase.a12(doc_id, graph_version=graph_version)
        concept = IndexConcepts(self.store, self.embedding_guard, phase.store).execute(
            doc_id, graph_version, allow_spend=self.allow_spend)
        a12_metadata = {"graph_version": a12["graph_version"],
                        "retrieval_version": a12["retrieval_version"],
                        "assignment_count": len(a12.get("assignments", {}))}
        concept_metadata = {"graph_version": concept.get("graph_version", graph_version),
                            "model_id": concept.get("model_id", self.settings.embedding_model_id),
                            "reused": concept.get("reused", False),
                            "concept_count": concept.get("concept_count", len(concept.get("items", [])))}
        formulas = {"skipped": "not a PDF"}
        if Path(file_path).suffix.lower() == ".pdf":
            from doc2roadmap.application.phase_b.formula_images import CutFormulaImages, persist_formula_images
            from doc2roadmap.infrastructure.media.formula_images import PdfiumFormulaRenderer
            graph = self.store.load_graph(doc_id, graph_version)
            chunks = self.store.load_chunks(doc_id, graph.manifest["config"]["chunks_version"])
            parsed = self.store.load_parse(doc_id, chunks.manifest["parse_version"])
            full_formulas = persist_formula_images(CutFormulaImages(PdfiumFormulaRenderer()).execute(file_path, parsed.tree),
                self.settings.artifact_dir, doc_id, chunks.manifest["parse_version"])
            formulas = {"index_path": full_formulas["index_path"],
                        "parse_version": chunks.manifest["parse_version"],
                        "cut_count": full_formulas["cut_count"],
                        "skipped_count": full_formulas["skipped_count"]}
        return {"a12": a12_metadata, "concept_index": concept_metadata, "formulas": formulas}

    def inspect(self, doc_id):
        # Inspect only existing artifacts; never plans with cost estimates or writes new artifacts.
        def latest(loader):
            try:
                return loader(doc_id).version
            except FileNotFoundError:
                return None
        return {"cache_validated": False,
                "chunks_version": latest(self.store.load_latest_chunks),
                "candidate_version": latest(self.store.load_latest_candidates),
                "canonical_version": latest(self.store.load_latest_canonical),
                "graph_version": latest(self.store.load_latest_graph),
                "retrieval_version": latest(self.store.load_latest_retrieval)}

    def usage(self):
        return self.usage_meter.snapshot()


def build_document_runner(settings=None, *, allow_spend=False, recorder=None):
    settings = settings or Settings()
    pipeline = DocumentPipeline(settings, allow_spend=allow_spend)
    if recorder is None:
        from doc2roadmap.infrastructure.artifacts.build_log import SqliteBuildLog
        recorder = SqliteBuildLog(settings.artifact_dir / "builds.sqlite3")
    from doc2roadmap.application.use_cases.build_document import BuildDocument
    return BuildDocument(pipeline, _pipeline_version(settings), recorder=recorder,
                         scan_min_chars_per_page=150, scan_max_empty_page_ratio=.5,
                         vi_min_diacritic_ratio=.01)
