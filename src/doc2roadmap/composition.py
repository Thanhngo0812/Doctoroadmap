from pathlib import Path

from doc2roadmap.application.extraction_prompt import load_prompts
from doc2roadmap.application.use_cases import (
    ExtractEntities,
    IndexDocument,
    IngestDocument,
    InspectDocument,
    SearchDocument,
)
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.embedding import GeminiEmbedding
from doc2roadmap.infrastructure.llm import GeminiEntityExtractor
from doc2roadmap.infrastructure.parsing import DoclingParser
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter


def build_ingest() -> tuple[IngestDocument, Settings]:
    settings = Settings()
    store = JsonArtifactStore(settings.artifact_dir)
    counter = SentencePieceTokenCounter(settings.tokenizer_model, settings.tokenizer_id)
    return (
        IngestDocument(DoclingParser(), store, counter, UnicodeSentenceSplitter()),
        settings,
    )


def build_inspect() -> InspectDocument:
    settings = Settings()
    return InspectDocument(JsonArtifactStore(settings.artifact_dir))


def _a3_dependencies() -> tuple[Settings, JsonArtifactStore, GeminiEmbedding]:
    settings = Settings()
    if settings.gemini_api_key is None:
        raise ValueError("thiếu DOC2ROADMAP_GEMINI_API_KEY")
    key = settings.gemini_api_key.get_secret_value()
    store = JsonArtifactStore(settings.artifact_dir)
    embedding = GeminiEmbedding(
        key,
        model=settings.embedding_model_id,
        output_dimensionality=settings.embedding_dimensions,
        timeout=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
    )
    return settings, store, embedding


def _extractor(settings: Settings) -> GeminiEntityExtractor:
    if settings.gemini_api_key is None:
        raise ValueError("thiếu DOC2ROADMAP_GEMINI_API_KEY")
    return GeminiEntityExtractor(
        settings.gemini_api_key.get_secret_value(),
        settings.extraction_model_id,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
        temperature=settings.extraction_temperature,
        max_output_tokens=settings.extraction_max_output_tokens,
    )


def build_extract(
    *, few_shot_path: Path | None = None
) -> tuple[ExtractEntities, Settings]:
    settings, store, embedding = _a3_dependencies()
    counter = SentencePieceTokenCounter(settings.tokenizer_model, settings.tokenizer_id)
    generation = {
        "temperature": settings.extraction_temperature,
        "max_output_tokens": settings.extraction_max_output_tokens,
    }
    return (
        ExtractEntities(
            store,
            _extractor(settings),
            embedding,
            generation=generation,
            counter=counter,
            prompts=load_prompts(few_shot_path or settings.extraction_few_shot),
        ),
        settings,
    )


def build_index() -> tuple[IndexDocument, Settings]:
    settings, store, embedding = _a3_dependencies()
    return IndexDocument(store, embedding), settings


def build_search() -> SearchDocument:
    _, store, embedding = _a3_dependencies()
    return SearchDocument(store, embedding)


def build_a3(
    *, few_shot_path: Path | None = None
) -> tuple[ExtractEntities, IndexDocument, Settings]:
    settings, store, embedding = _a3_dependencies()
    counter = SentencePieceTokenCounter(settings.tokenizer_model, settings.tokenizer_id)
    extraction = ExtractEntities(
        store,
        _extractor(settings),
        embedding,
        generation={
            "temperature": settings.extraction_temperature,
            "max_output_tokens": settings.extraction_max_output_tokens,
        },
        counter=counter,
        prompts=load_prompts(few_shot_path or settings.extraction_few_shot),
    )
    return extraction, IndexDocument(store, embedding), settings


def build_artifact_store() -> JsonArtifactStore:
    settings = Settings()
    return JsonArtifactStore(settings.artifact_dir)


def build_canonical(*, prepare=False):
    from doc2roadmap.application.use_cases.canonicalize import Canonicalize
    from doc2roadmap.application.use_cases.canonical_reasoning import CanonicalReasoning

    settings, store, embedding = _a3_dependencies()
    graph = {"k": settings.merge_neighbors, "ngram_threshold": settings.merge_ngram_threshold,
             "resolution": settings.merge_resolution, "seed": settings.merge_seed, "cap": settings.merge_cluster_cap}
    if prepare:
        return Canonicalize(store, embedding, graph_config=graph)
    def model(model_id):
        return GeminiEntityExtractor(settings.gemini_api_key.get_secret_value(), model_id,
            timeout_seconds=settings.gemini_timeout_seconds, max_retries=settings.gemini_max_retries,
            temperature=settings.extraction_temperature, max_output_tokens=settings.extraction_max_output_tokens)
    reasoning = CanonicalReasoning(model(settings.merge_model_id), model(settings.description_model_id),
        generation={"temperature": settings.extraction_temperature, "max_output_tokens": settings.extraction_max_output_tokens},
        language_rule=settings.canonical_language_rule, batch_size=settings.canonical_batch_size,
        concurrency=settings.canonical_concurrency,
        counter=SentencePieceTokenCounter(settings.tokenizer_model, settings.tokenizer_id))
    return Canonicalize(store, embedding, graph_config=graph, reasoning=reasoning)


def build_learning_graph():
    from doc2roadmap.application.use_cases import (
        BuildClusters,
        BuildLearningGraph,
        BuildMainEdges,
        BuildMentions,
        BuildProvenance,
        BuildRoadmap,
        BuildSecondaryEdges,
        ValidateGraph,
    )

    settings, store, embedding = _a3_dependencies()
    model = GeminiEntityExtractor(
        settings.gemini_api_key.get_secret_value(),
        settings.roadmap_model_id,
        timeout_seconds=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
        temperature=0.0,
        max_output_tokens=settings.extraction_max_output_tokens,
    )
    generation = {"temperature": 0.0, "max_output_tokens": settings.extraction_max_output_tokens}
    return BuildLearningGraph(
        BuildClusters(
            store,
            embedding,
            semantic_neighbors=settings.topic_neighbors,
            edge_quantile=settings.topic_edge_quantile,
            resolution=settings.topic_resolution,
            seed=settings.topic_seed,
            concept_cap=settings.topic_cluster_cap,
        ),
        BuildMentions(
            store,
            embedding,
            dense_top_k=settings.mention_dense_top_k,
            dense_min_z=settings.mention_dense_min_z,
            pair_cluster_top_k=settings.mention_pair_cluster_top_k,
        ),
        BuildProvenance(
            store,
            model,
            concurrency=settings.roadmap_concurrency,
            generation=generation,
        ),
        BuildMainEdges(
            store,
            model,
            single_session_limit=settings.roadmap_single_session_limit,
            concurrency=settings.roadmap_concurrency,
            generation=generation,
        ),
        BuildSecondaryEdges(
            store,
            model,
            concurrency=settings.roadmap_concurrency,
            generation=generation,
        ),
        ValidateGraph(store),
        BuildRoadmap(
            store,
            stage_cap=settings.roadmap_stage_cap,
            stage_floor=settings.roadmap_stage_floor,
        ),
    ), settings
