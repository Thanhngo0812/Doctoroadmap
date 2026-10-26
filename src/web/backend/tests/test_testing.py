from doc2roadmap.application.ports.embedding import EmbeddingRequest

from wayfinder.testing import build_test_application


def test_fake_application_runs_phase_b_lecture_on_shared_memory_ports() -> None:
    application = build_test_application()
    phase_b = application.phase_b
    quotes = [
        "Tập hợp gồm các phần tử có cùng một đặc điểm.",
        "Mỗi phần tử của tập hợp được xét theo một quy tắc xác định.",
    ]
    body = '\n\n'.join(quote + ' [S1]' for quote in quotes)
    phase_b.model.text_replies.append([body])

    lecture = phase_b.lecture.make("sample", "g1", phase_b.graph, "a", owner="learner", allow_spend=True)
    progress = phase_b.progress.set_progress("learner", "sample", "a", True)
    vector = [0.25, -0.5, 0.75]
    phase_b.embedding.vectors = [vector]
    embedded = phase_b.embedding.embed([EmbeddingRequest("tập hợp", "RETRIEVAL_QUERY")])

    assert lecture["status"] == "ready"
    assert lecture['contract_version'] == 'lecture-3' and lecture['body_md'] == body
    assert phase_b.model.text_replies == []
    assert len(phase_b.model.text_calls) == 1
    assert phase_b.model.text_calls[0][1]['temperature'] == phase_b.lecture.settings.lecture_temperature
    assert phase_b.model.json_calls == []
    assert phase_b.store.get_cache(lecture["lecture_key"]) is not None
    assert progress["state"] == "learned"
    assert phase_b.store.list_records("progress", owner="learner", doc_id="sample") == [progress]
    assert phase_b.embedding.requests == [[EmbeddingRequest("tập hợp", "RETRIEVAL_QUERY")]]
    assert embedded == [vector]
    assert phase_b.sessions.store is phase_b.library.store is phase_b.quiz.store is phase_b.store
    assert phase_b.assistant.store is phase_b.documents.store is phase_b.store
    assert application.media_store.files == {}


def test_scripted_json_adapter_still_consumes_exactly_one_reply() -> None:
    from wayfinder.testing import ScriptedModel
    model = ScriptedModel(json_replies=[{'value': 1}, {'value': 2}])
    session = model.start_session('fake system')
    assert list(session.stream_json('fake prompt', response_schema={'type': 'object'})) == ['{"value": 1}']
    assert model.json_replies == [{'value': 2}]
    assert model.json_calls == [('fake prompt', {'type': 'object'})]
