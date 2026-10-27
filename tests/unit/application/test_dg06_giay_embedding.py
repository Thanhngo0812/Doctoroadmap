"""DG-06 (1): bộ đếm giây chờ embedding trong bộ đo stage. Chỉ telemetry, không vào payload, khoá cache hay hash cấu hình."""
import json
from urllib.error import HTTPError

import pytest

import doc2roadmap.application.stage_measurements as measurements
from doc2roadmap.application.ports.embedding import EmbeddingRequest
from doc2roadmap.application.stage_measurements import measure_stage, resume_measurements
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
from doc2roadmap.infrastructure.embedding import gemini
from doc2roadmap.infrastructure.embedding.gemini import GeminiEmbedding


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


@pytest.fixture
def dong_ho(monkeypatch):
    gio = [0.0]
    monkeypatch.setattr(measurements, "perf_counter", lambda: gio[0])
    return gio


def test_snapshot_co_embedding_seconds_bang_0_khi_khong_goi_embedding(tmp_path, dong_ho):
    store = JsonArtifactStore(tmp_path)

    @measure_stage
    def execute():
        dong_ho[0] += 5
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)

    stats = execute().manifest["stats"]
    assert stats["embedding_seconds"] == 0 and stats["runtime_seconds"] == 5


def test_giay_cho_embedding_cong_dung_thoi_gian_trong_loi_goi(tmp_path, dong_ho):
    store = JsonArtifactStore(tmp_path)

    @measure_stage
    def execute():
        dong_ho[0] += 2  # việc khác
        with measurements.measure_embedding_wait():
            dong_ho[0] += 3
        dong_ho[0] += 1
        with measurements.measure_embedding_wait():
            dong_ho[0] += 4
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)

    stats = execute().manifest["stats"]
    assert stats["embedding_seconds"] == 7 and stats["runtime_seconds"] == 10


def test_loi_goi_long_nhau_hoac_chong_nhau_chi_cong_mot_lan(tmp_path, dong_ho):
    store = JsonArtifactStore(tmp_path)

    @measure_stage
    def execute():
        with measurements.measure_embedding_wait():
            dong_ho[0] += 1
            with measurements.measure_embedding_wait():  # lồng
                dong_ho[0] += 2
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)

    assert execute().manifest["stats"]["embedding_seconds"] == 3  # không phải 5


def test_ngoai_stage_khong_loi_va_khong_dem(dong_ho):
    with measurements.measure_embedding_wait():
        dong_ho[0] += 1  # không có stage đang đo: không làm gì, không lỗi


def test_retry_cua_gemini_cong_ca_lan_loi_va_cho_lui_dung_mot_lan(tmp_path, dong_ho, monkeypatch):
    lan = []

    def urlopen_gia(request, timeout):
        lan.append(1)
        dong_ho[0] += 3
        if len(lan) == 1:
            raise HTTPError(request.full_url, 503, "busy", {}, None)
        return _Response({"embeddings": [{"values": [3.0, 4.0]}]})

    monkeypatch.setattr(gemini, "urlopen", urlopen_gia)
    monkeypatch.setattr(gemini, "sleep", lambda giay: dong_ho.__setitem__(0, dong_ho[0] + giay))
    store = JsonArtifactStore(tmp_path)
    embedding = GeminiEmbedding("khoa-gia", output_dimensionality=2)

    @measure_stage
    def execute():
        embedding.embed([EmbeddingRequest("x", "RETRIEVAL_DOCUMENT")])
        return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)

    stats = execute().manifest["stats"]
    # 3 (lần lỗi) + 1 (chờ lùi 2**0) + 3 (lần thành công) = 7; cộng hai lần sẽ ra 14
    assert stats["embedding_seconds"] == 7 and stats["model_calls"] == 2


def test_resume_giu_giay_embedding_cua_lan_chay_truoc(tmp_path, dong_ho):
    store = JsonArtifactStore(tmp_path)

    class Stage:
        @measure_stage
        def execute(self, hong=False):
            resume_measurements(store.load_checkpoint("book", "t"))
            with measurements.measure_embedding_wait():
                dong_ho[0] += 5 if hong else 3
            store.save_checkpoint("book", "t", {"source_hash": "s"})
            if hong:
                raise RuntimeError("ngắt")
            return store.save_graph("book", "s", "c", {}, {}, upstream_version=1)

    with pytest.raises(RuntimeError):
        Stage().execute(hong=True)
    dong_ho[0] += 100
    assert Stage().execute().manifest["stats"]["embedding_seconds"] == 8


def test_telemetry_khong_doi_payload_va_hash_cau_hinh(tmp_path, dong_ho):
    store = JsonArtifactStore(tmp_path)

    def chay(giay):
        @measure_stage
        def execute():
            with measurements.measure_embedding_wait():
                dong_ho[0] += giay
            return store.save_graph("book", "s", "c", {"k": 1}, {"nodes": [1]}, upstream_version=1)
        return execute()

    a, b = chay(1), chay(9)
    assert a.payload == b.payload and a.manifest["config_hash"] == b.manifest["config_hash"] == "c"
    assert a.manifest["config"] == b.manifest["config"]
