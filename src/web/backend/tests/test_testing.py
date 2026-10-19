from doc2roadmap.application.ports.embedding import EmbeddingRequest

from wayfinder.testing import build_test_application


def test_fake_application_runs_phase_b_lecture_on_shared_memory_ports() -> None:
    application = build_test_application()
    phase_b = application.phase_b
    quotes = [
        "Tập hợp gồm các phần tử có cùng một đặc điểm.",
        "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.",
    ]
    phase_b.model.json_replies.append({
        "prereq_notes": [],
        "explanation": [{"text": quote, "sources": ["S1"], "quote": quote} for quote in quotes],
        "example": [], "contrasts": [], "gaps": [],
    })

    lecture = phase_b.lecture.make("sample", "g1", phase_b.graph, "a", owner="learner", allow_spend=True)
    progress = phase_b.progress.set_progress("learner", "sample", "a", True)
    vector = [0.25, -0.5, 0.75]
    phase_b.embedding.vectors = [vector]
    embedded = phase_b.embedding.embed([EmbeddingRequest("tập hợp", "RETRIEVAL_QUERY")])

    assert lecture["status"] == "ready"
    assert phase_b.model.json_replies == []
    assert len(phase_b.model.json_calls) == 1
    assert phase_b.store.get_cache(lecture["lecture_key"]) is not None
    assert progress["state"] == "learned"
    assert phase_b.store.list_records("progress", owner="learner", doc_id="sample") == [progress]
    assert phase_b.embedding.requests == [[EmbeddingRequest("tập hợp", "RETRIEVAL_QUERY")]]
    assert embedded == [vector]
    assert phase_b.sessions.store is phase_b.library.store is phase_b.quiz.store is phase_b.store
    assert phase_b.assistant.store is phase_b.documents.store is phase_b.store
    assert application.media_store.files == {}
