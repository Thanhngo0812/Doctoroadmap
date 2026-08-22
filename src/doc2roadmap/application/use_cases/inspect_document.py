from doc2roadmap.application.ports import ArtifactStore, StoredChunks
from doc2roadmap.application.use_cases.ingest_document import validate_doc_id
from doc2roadmap.application.windows import assemble_windows
from doc2roadmap.domain.models import Chunk


class InspectDocument:
    def __init__(self, store: ArtifactStore) -> None:
        self.store = store

    def execute(self, doc_id: str) -> tuple[StoredChunks, dict[str, list[Chunk]]]:
        validate_doc_id(doc_id)
        stored = self.store.load_latest_chunks(doc_id)
        return stored, assemble_windows(stored.result.chunks)
