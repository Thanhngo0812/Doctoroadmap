"""SA-66: page pictures inside a conversation turn, and one shared Vertex credentials object per runtime."""
import base64
import hashlib
import json
import threading
from types import SimpleNamespace as NS

import pytest

from doc2roadmap.application.ports.phase_b import Delta, Done
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding
from doc2roadmap.infrastructure.google_auth import VertexCredentials
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel, ReplayToolModel
from doc2roadmap.infrastructure.llm.phase_b_demo import DemoModel

IMAGES = [(5, b'jpeg-five'), (7, b'jpeg-seven')]


def test_user_turn_with_pictures_becomes_text_then_one_labelled_picture_part_per_page():
    session = GeminiToolModel('key').start_session('system')
    contents = session._contents([{'role': 'user', 'text': 'Câu hỏi', 'images': IMAGES}])
    parts = contents[0]['parts']
    assert parts[0] == {'text': 'Câu hỏi'}
    assert parts[1] == {'text': 'Ảnh trang 5 của sách:'}
    assert parts[2] == {'inlineData': {'mimeType': 'image/jpeg', 'data': base64.b64encode(b'jpeg-five').decode()}}
    assert parts[3] == {'text': 'Ảnh trang 7 của sách:'} and len(parts) == 5
    assert session._contents([{'role': 'user', 'text': 'Chỉ chữ'}])[0]['parts'] == [{'text': 'Chỉ chữ'}]


class Delegate:
    model_id = 'gemini-3.1-flash-lite'

    def start_session(self, prompt, tools=()):
        return self

    def stream(self, messages, *, mode):
        yield Delta('Trả lời [S1]')
        yield Done({'promptTokenCount': 3})


def test_a_conversation_with_pictures_is_recorded_as_json_with_picture_ids_and_replays_only_for_the_same_pictures(tmp_path):
    path = tmp_path / 'rec.json'
    messages = [{'role': 'user', 'text': 'Câu hỏi', 'images': IMAGES}]
    session = RecordingToolModel(Delegate(), path, prompt_hash='h').start_session('system', [])
    assert [e.text for e in session.stream(messages, mode='AUTO') if isinstance(e, Delta)] == ['Trả lời [S1]']
    recorded = json.loads(path.read_text(encoding='utf-8'))['sessions'][0]['calls'][0]['messages'][0]
    assert recorded['images'] == [[5, hashlib.sha256(b'jpeg-five').hexdigest()], [7, hashlib.sha256(b'jpeg-seven').hexdigest()]]
    assert 'jpeg-five' not in path.read_text(encoding='utf-8')
    replay = ReplayToolModel(path, prompt_hash='h')
    same = replay.start_session('system', [])
    assert [e.text for e in same.stream(messages, mode='AUTO') if isinstance(e, Delta)] == ['Trả lời [S1]']
    other = ReplayToolModel(path, prompt_hash='h').start_session('system', [])
    with pytest.raises(ValueError, match='no unused session'):
        list(other.stream([{'role': 'user', 'text': 'Câu hỏi', 'images': [(5, b'another picture'), (7, b'jpeg-seven')]}],
                          mode='AUTO'))


# ------------------------------------------------------------------ shared credentials
class FakeCredentials:
    valid = True
    token = 'token'

    def refresh(self, request):  # pragma: no cover - never expires in these tests
        pass


def client_of(model):
    return getattr(model, 'delegate', model).vertex  # a recording wrapper holds the real client


def vertex_runtime(tmp_path, **kwargs):
    settings = Settings(artifact_dir=tmp_path, _env_file=None, llm_transport='vertex', vertex_project='proj')
    return PhaseBRuntime(settings=settings, mode='gemini', allow_spend=True, store=InMemoryPhaseBStore(), **kwargs)


def test_every_client_of_a_runtime_shares_one_credentials_object_and_the_token_is_fetched_once(tmp_path, monkeypatch):
    fetched = []
    monkeypatch.setattr('google.auth.default', lambda scopes=None: fetched.append(threading.current_thread()) or (FakeCredentials(), 'p'))
    runtime = vertex_runtime(tmp_path)
    runtime.auth_warmup.join(timeout=10)
    assert len(fetched) == 1 and fetched[0] is not threading.main_thread()  # fetched at start, in the background
    clients = [client_of(runtime.model(purpose)) for purpose in ('lecture', 'assistant', 'document', 'quiz_gen', 'quiz_verify')]
    clients.append(runtime.query_embedding()._delegate._vertex)
    assert all(client is runtime.vertex_credentials for client in clients)
    for client in clients:
        assert client.headers()['Authorization'] == 'Bearer token'
    assert len(fetched) == 1  # no client fetched a second token


def test_a_failed_warmup_does_not_break_the_runtime_and_the_first_real_call_retries(tmp_path, monkeypatch):
    attempts = []

    def default(scopes=None):
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError('metadata server unreachable')
        return FakeCredentials(), 'p'
    monkeypatch.setattr('google.auth.default', default)
    runtime = vertex_runtime(tmp_path)
    runtime.auth_warmup.join(timeout=10)
    assert len(attempts) == 1
    assert client_of(runtime.model('assistant')) is runtime.vertex_credentials
    assert client_of(runtime.model('assistant')).headers()['Authorization'] == 'Bearer token' and len(attempts) == 2


def test_no_credentials_object_and_no_warmup_unless_the_runtime_really_talks_to_vertex(tmp_path, monkeypatch):
    monkeypatch.setattr('google.auth.default', lambda scopes=None: pytest.fail('no token should be fetched'))
    for kwargs in ({'mode': 'offline'}, {'settings': Settings(artifact_dir=tmp_path, _env_file=None)}):
        base = {'settings': Settings(artifact_dir=tmp_path, _env_file=None, llm_transport='vertex', vertex_project='proj'),
                'mode': 'gemini', 'store': InMemoryPhaseBStore()}
        runtime = PhaseBRuntime(**{**base, **kwargs})
        assert runtime.vertex_credentials is None and runtime.auth_warmup is None


def test_clients_built_by_hand_still_make_their_own_credentials():
    shared = VertexCredentials('proj')
    assert GeminiToolModel(None, transport='vertex', vertex_project='proj', vertex_credentials=shared).vertex is shared
    assert GeminiEmbedding(None, transport='vertex', vertex_project='proj', vertex_credentials=shared)._vertex is shared
    own = GeminiToolModel(None, transport='vertex', vertex_project='proj').vertex
    assert isinstance(own, VertexCredentials) and own is not shared


# ------------------------------------------------------------------ offline demo model reads the prose context
def test_demo_model_answers_from_the_first_passage_of_the_prose_context():
    text = ('Người học đang mở module 1: Ma trận\n\nTư liệu từ sách:\n'
            '[S1] (trang 3, mục Ma trận)\nMa trận là bảng các số. Mỗi hàng có cùng số cột.\n\n'
            '[S2] (trang 4, mục Khác)\nMột đoạn khác.\n\nCâu hỏi của người học: Ma trận là gì?')
    session = DemoModel().start_session('', [])
    events = list(session.stream([{'role': 'user', 'text': text}], mode='AUTO'))
    assert events[0].text == 'Ma trận là bảng các số. [S1]'
    nothing = list(session.stream([{'role': 'user', 'text': 'Tư liệu từ sách:\n(không có)\n\nCâu hỏi của người học: Xyz?'}], mode='AUTO'))
    assert 'KHONG_DU' not in nothing[0].text
