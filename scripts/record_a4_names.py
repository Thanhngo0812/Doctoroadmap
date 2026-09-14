"""Record name embeddings and A3 inputs, never call an A4/A5 language model."""
from pathlib import Path
from dataclasses import asdict

from doc2roadmap.composition import _a3_dependencies
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.application.use_cases.canonicalize import Canonicalize
from doc2roadmap.application.use_cases.extract_entities import DocumentExtraction
from doc2roadmap.infrastructure.embedding.replay import record_embedding_fixture, ReplayEmbedding


def main():
    _, store, embedding = _a3_dependencies()
    for doc_id in ("nhap-mon-ml", "xstk-ch3-1", "baocao-canhan", "naive-bayes"):
        candidate = store.load_latest_candidates(doc_id)
        extraction = DocumentExtraction.from_payload(candidate.payload)
        names = sorted({e.name for e in extraction.entities if not e.is_media})
        target = Path("tests/fixtures/a4") / doc_id
        path = target / "name-vectors.json"
        record_embedding_fixture(path, embedding, [EmbeddingRequest(name, "SEMANTIC_SIMILARITY") for name in names])
        chunks = store.load_chunks(doc_id, candidate.manifest["upstream_version"])
        store._write(target / "input.json", {
            "candidate_payload": candidate.payload, "candidate_manifest": candidate.manifest,
            "candidate_version": candidate.version, "chunks": asdict(chunks.result),
            "chunk_manifest": chunks.manifest, "chunk_version": chunks.version,
        })
        artifact, reused = Canonicalize(store, ReplayEmbedding(path, expected_model_id=embedding.embedding_model_id)).execute(doc_id)
        print(f"{doc_id}: vectors={len(names)} canonical=v{artifact.version} reused={reused}", flush=True)


if __name__ == "__main__":
    main()
