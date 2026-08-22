from doc2roadmap.application.use_cases import IngestDocument, InspectDocument
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
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
