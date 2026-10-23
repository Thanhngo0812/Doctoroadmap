"""W08 web contract with PostgreSQL; the scripted use case is not SA64 acceptance."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from test_learning_progress_w07 import w07


pytestmark = pytest.mark.postgres


class ScriptedLecture3:
    def __init__(self, store, progress):
        self.store, self.progress = store, progress
        self.calls = 0
        self.body = "### Hiểu bài\n\nMột ví dụ $x^2$ từ tài liệu. [S1] [S999]"

    def make(self, doc_id, version, graph, node_id, *, owner, cache_only=False,
             on_event=None, **kwargs):
        emit = on_event or (lambda event: None)
        lecture = dict(contract_version="lecture-3", doc_id=doc_id, graph_version=version,
            node_id=node_id, lecture_key="web-scripted-lecture3", status="generating",
            position=dict(module_id="m1", module_index=1, index_in_module=1, count_in_module=2),
            definition=dict(quote="Định nghĩa nguyên văn.", page=1, citation=None, formula_refs=[]),
            prerequisites=[dict(recall=dict(node_id="b", name="B", module_index=1,
                module_title="Nền tảng", definition=dict(quote="Định nghĩa B.", citation=None)),
                learner_status="unknown")], next_up=[], body_md="", self_check=None,
            sources=[dict(label="S1", chunk_id="chunk-a", page=1, section_path=["Mục 1"])],
            warnings=[], failure=None, usage={}, media=[])
        emit({"event": "skeleton", "lecture": deepcopy(lecture)})
        if cache_only:
            result = self.store.get_cache(lecture["lecture_key"])
            if result is None:
                return lecture
        else:
            def generate():
                self.calls += 1
                emit({"event": "delta", "text": self.body})
                return {**lecture, "status": "ready", "body_md": self.body,
                    "self_check": {"question_md": "Vì sao?", "answer_md": "Vì $x^2$."},
                    "validation": {"private_admin_marker": True},
                    "sections": [{"text": "legacy must not appear"}],
                    "public_id": "private-provider-id"}
            result = self.store.single_flight(lecture["lecture_key"], generate)
        result = deepcopy(result)
        result["prerequisites"][0]["learner_status"] = self.progress.get_progress(owner, doc_id)["nodes"]["b"]["state"]
        emit({"event": "final", "lecture": result})
        return result


@pytest.fixture
def lecture_web(w07):
    with w07.engine.begin() as c:
        c.execute(text("DELETE FROM media_asset WHERE doc_id='doc-1'"))
    scripted = ScriptedLecture3(w07.phase_b, w07.gateway.runtime.progress(w07.graph))
    w07.gateway.runtime.lecture = lambda graph: scripted
    return SimpleNamespace(**vars(w07), scripted=scripted,
        url=f"/api/v1/courses/{w07.course.id}/concepts/a/lecture")


def test_w08_cache_read_does_not_generate_and_stream_has_lecture3_only(lecture_web):
    w = lecture_web
    before = w.a.client.get(w.url)
    assert before.status_code == 200
    assert before.json()["status"] == "generating"
    assert w.scripted.calls == 0
    response = w.a.client.get(w.url + "/stream")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-accel-buffering"] == "no"
    assert response.text.index('event: skeleton') < response.text.index('event: delta') < response.text.index('event: final')
    assert w.scripted.body in w.a.client.get(w.url).json()["body_md"]
    assert w.scripted.calls == 1
    for forbidden in ["validation", "private_admin_marker", "sections", "bridge", "public_id", "private-provider-id"]:
        assert forbidden not in response.text
        assert forbidden not in w.a.client.get(w.url).text
    assert w.phase_b.get_cache("web-scripted-lecture3")["validation"]["private_admin_marker"] is True


def test_w08_cache_is_shared_but_progress_is_attached_to_current_actor(lecture_web):
    w = lecture_web
    w.gateway.set_progress(w.a.actor, w.course.id, "b", True)
    assert w.a.client.get(w.url + '/stream').status_code == 200
    first = w.a.client.get(w.url).json()
    second = w.b.client.get(w.url).json()
    assert first["lecture_key"] == second["lecture_key"]
    assert first["prerequisites"][0]["learner_status"] == "learned"
    assert second["prerequisites"][0]["learner_status"] == "not_learned"
    assert w.scripted.calls == 1
    with w.independent_engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM phase_b_cache WHERE key='web-scripted-lecture3'")) == 1


@pytest.mark.parametrize('node_id', ['missing', 'hidden'])
def test_w08_node_must_be_in_published_learnable_graph(lecture_web, node_id):
    w = lecture_web
    response = w.a.client.get(w.url.replace('/a/', f'/{node_id}/') + '/stream')
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'not_found'
    assert w.scripted.calls == 0


def test_w08_private_source_page_headers_range_and_lazy_media_are_real_postgres(lecture_web, tmp_path):
    from wayfinder.fakes.media import MemoryMediaStore
    from wayfinder.infrastructure.learning_media import LearningMedia
    w = lecture_web
    settings = w.courses.settings
    settings.artifact_root = tmp_path
    media = MemoryMediaStore()
    pdf = tmp_path / 'source.pdf'
    pdf.write_bytes(b'%PDF-test')
    public = media.upload(pdf, 'private-source', 'image')
    with w.engine.begin() as c:
        c.execute(text('UPDATE course SET source_public_id=:public WHERE id=:cid'), {'public': public, 'cid': w.course.id})
    w.graph.tree = SimpleNamespace(parse_stats={'page_count': 2})
    w.graph.parse_version = 1
    w.graph.formula_images = {'f@p1': {'image_ref': 'images/formula.png'}}
    image = tmp_path / 'phase_b/formula_images/doc-1/parse-v1/images/formula.png'
    image.parent.mkdir(parents=True)
    image.write_bytes(b'fake-formula')
    w.gateway.media = LearningMedia(w.engine, settings, store=media)
    base = f'/api/v1/courses/{w.course.id}'
    for bad in ['0', '3', '-1', 'not-a-page']:
        assert w.a.client.get(base + '/source/pages/' + bad).status_code == 404
    assert media.fetch_count == 0
    page = w.a.client.get(base + '/source/pages/2')
    assert page.status_code == 200 and page.headers['content-type'] == 'image/webp'
    assert page.headers['cache-control'] == 'private, max-age=300'
    assert page.headers['x-page-count'] == '2' and page.content.startswith(b'RIFF')
    location = w.a.client.get(base + '/source', follow_redirects=False)
    assert location.status_code == 302
    assert 'expires_at=' in location.headers['location']
    for _ in range(2):
        response = w.a.client.get(base + '/media/parse-v1/images/formula.png')
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'private, max-age=300'
    with w.independent_engine.connect() as c:
        assert c.scalar(text('SELECT count(*) FROM media_asset WHERE doc_id=\'doc-1\'')) == 1
    assert len(media.files) == 2  # source plus one shared formula upload
    before = media.fetch_count
    assert w.a.client.get(base + '/media/another-version.png').status_code == 404
    with w.engine.begin() as c:
        c.execute(text('DELETE FROM membership WHERE course_id=:cid AND account_id=:uid'),
                  {'cid': w.course.id, 'uid': w.b.actor.user_id})
    for path in ['/source/pages/1', '/source', '/media/parse-v1/images/formula.png', '/concepts/a/lecture', '/concepts/a/lecture/stream']:
        result = w.b.client.get(base + path, follow_redirects=False)
        assert result.status_code == 404
        assert result.json()['error']['code'] == 'not_found'
    assert media.fetch_count == before


@pytest.mark.parametrize('after_delta', [False, True])
def test_w08_transport_failure_retains_text_or_has_a_vietnamese_retry(after_delta, lecture_web):
    import json
    w = lecture_web
    def broken(actor, cid, node_id, emit):
        skeleton = w.scripted.make(w.graph.doc_id, 8, w.graph, node_id, owner=actor.user_id, cache_only=True)
        emit({'event': 'skeleton', 'lecture': {**skeleton, 'course_id': cid}})
        if after_delta:
            emit({'event': 'delta', 'text': 'Nội dung đã gửi phải được giữ.'})
        raise RuntimeError('private path/provider diagnostics must stay in server logs')
    w.gateway.stream_lecture = broken
    response = w.a.client.get(w.url + '/stream')
    assert response.status_code == 200
    assert 'private path' not in response.text
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    if after_delta:
        assert events[-1]['lecture']['body_md'] == 'Nội dung đã gửi phải được giữ.'
        assert events[-1]['lecture']['status'] == 'ready'
        assert 'cat_ngan' in events[-1]['lecture']['warnings']
    else:
        assert events[-1]['failure']['message'].strip()
        assert events[-1]['failure']['retryable'] is True
