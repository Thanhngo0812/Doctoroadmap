"""SA-64: the text-with-pictures stream of the Gemini client, record/replay of it, and the page-picture reader."""
import base64
import hashlib
import io
import json

import pytest

from doc2roadmap.infrastructure.artifacts.page_images import ArtifactPageImages
from doc2roadmap.infrastructure.llm import phase_b
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel, ReplayToolModel


class _Response:
    def __init__(self, events):
        self._stream = io.BytesIO(b"".join(b"data: " + json.dumps(e).encode() + b"\n\n" for e in events))

    def __iter__(self):
        return self._stream

    def close(self):
        self._stream.close()


def _events(*texts):
    rows = [{"candidates": [{"content": {"parts": [{"text": text}]}}], "usageMetadata": {"promptTokenCount": 7}}
            for text in texts]
    return rows + [{"candidates": [{"finishReason": "STOP"}], "usageMetadata": {"candidatesTokenCount": 3}}]


def test_stream_text_sends_prompt_then_each_page_picture_and_no_json_schema(monkeypatch):
    seen = {}

    def urlopen(request, timeout):
        seen["body"], seen["url"], seen["timeout"] = json.loads(request.data), request.full_url, timeout
        return _Response(_events("Xin ", "chào"))

    monkeypatch.setattr(phase_b, "urlopen", urlopen)
    model = GeminiToolModel("key", temperature=1.0, max_output_tokens=4096)
    session = model.start_session("hệ thống")
    pieces = list(session.stream_text("tư liệu", images=[(37, b"jpeg37"), (62, b"jpeg62")],
                                      transport_retries=1, timeout_seconds=12.5))
    body = seen["body"]
    assert pieces == ["Xin ", "chào"]
    assert body["systemInstruction"]["parts"][0]["text"] == "hệ thống"
    parts = body["contents"][0]["parts"]
    assert parts[0] == {"text": "tư liệu"}
    assert parts[1] == {"text": "Ảnh trang 37 của sách:"}
    assert parts[2] == {"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(b"jpeg37").decode()}}
    assert parts[3] == {"text": "Ảnh trang 62 của sách:"} and len(parts) == 5
    config = body["generationConfig"]
    assert config == {"temperature": 1.0, "maxOutputTokens": 4096}
    assert "streamGenerateContent" in seen["url"] and seen["timeout"] == 12.5
    assert session.last_finish_reason == "STOP" and session.last_usage["promptTokenCount"] == 7
    assert session.last_ttft_ms is not None


def test_stream_text_temperature_argument_beats_the_model_default(monkeypatch):
    seen = {}
    monkeypatch.setattr(phase_b, "urlopen", lambda request, timeout: seen.setdefault("body", json.loads(request.data)) and _Response(_events("a")))
    list(GeminiToolModel("key", temperature=0.0).start_session("s").stream_text("p", temperature=0.7))
    assert seen["body"]["generationConfig"]["temperature"] == 0.7


class _Delegate:
    def start_session(self, system, tools=()):
        return self

    last_usage = {"promptTokenCount": 5}
    last_ttft_ms = 9
    last_finish_reason = "STOP"

    def stream_text(self, prompt, *, images=(), temperature=None, transport_retries=None, timeout_seconds=None):
        yield "một "
        yield "hai"


def test_text_stream_records_pictures_by_hash_and_replays_the_same_chunks(tmp_path):
    path = tmp_path / "lecture.json"
    recorder = RecordingToolModel(_Delegate(), path, prompt_hash="h")
    session = recorder.start_session("sys")
    assert list(session.stream_text("p", images=[(3, b"pic")], temperature=1.0, transport_retries=1, timeout_seconds=5)) == ["một ", "hai"]
    stored = json.loads(path.read_text(encoding="utf-8"))
    call = stored["sessions"][0]["calls"][0]
    assert call["kind"] == "text_stream" and call["images"] == [[3, hashlib.sha256(b"pic").hexdigest()]]
    assert "pic" not in path.read_text(encoding="utf-8").replace("lecture", "")

    replay = ReplayToolModel(path, prompt_hash="h").start_session("sys")
    assert list(replay.stream_text("p", images=[(3, b"pic")], temperature=1.0, transport_retries=1, timeout_seconds=1)) == ["một ", "hai"]
    assert replay.last_finish_reason == "STOP"
    other = ReplayToolModel(path, prompt_hash="h").start_session("sys")
    with pytest.raises(ValueError):
        list(other.stream_text("p", images=[(3, b"different")], temperature=1.0, transport_retries=1))


def _store(root, *, sha=None, file="pages/p037.jpg", data=b"jpeg-bytes"):
    folder = root / "phase_b" / "page_images" / "doc-1" / "parse-v3"
    (folder / "pages").mkdir(parents=True)
    (folder / "pages" / "p037.jpg").write_bytes(data)
    index = {"schema_version": 1, "doc_id": "doc-1", "parse_version": 3, "scale": 1.5, "format": "jpeg",
             "pages": {"37": {"file": file, "sha256": sha or hashlib.sha256(data).hexdigest()}}}
    (folder / "index.json").write_text(json.dumps(index), encoding="utf-8")
    return ArtifactPageImages(root)


def test_page_images_reads_a_stored_page_and_returns_none_for_anything_else(tmp_path):
    reader = _store(tmp_path)
    assert reader.get("doc-1", 3, 37) == b"jpeg-bytes"
    assert reader.get("doc-1", 3, 38) is None          # page not stored
    assert reader.get("doc-1", 4, 37) is None          # no index for that parse version
    assert reader.get("doc-2", 3, 37) is None          # no such book


def test_page_images_refuses_a_changed_file_and_paths_that_leave_the_folder(tmp_path):
    assert _store(tmp_path / "a", sha="0" * 64).get("doc-1", 3, 37) is None
    assert _store(tmp_path / "b", file="../../../../outside.jpg").get("doc-1", 3, 37) is None
    (tmp_path / "c").mkdir()
    assert ArtifactPageImages(tmp_path / "c").get("../doc-1", 3, 37) is None
