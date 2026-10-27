"""DG-06: các công tắc đi từ Settings tới use case, mặc định None, và không làm đổi phiên bản pipeline khi tắt."""
import hashlib
import json
from types import SimpleNamespace

import pytest

from doc2roadmap.composition_build import _BUILD_POLICY, _pipeline_version
from doc2roadmap.config import Settings

CONG_TAC = ("main_context_shuffle_seed", "secondary_target_filter")


def dung_pipeline(tmp_path, monkeypatch, **kw):
    from doc2roadmap.composition import build_learning_graph
    settings = Settings(_env_file=None, artifact_dir=tmp_path, **kw)
    monkeypatch.setattr("doc2roadmap.composition._a3_dependencies",
                        lambda: (settings, SimpleNamespace(), SimpleNamespace(limiter=None)))
    monkeypatch.setattr("doc2roadmap.composition.GeminiEntityExtractor", lambda *a, **k: object())
    pipeline, _ = build_learning_graph()
    return pipeline


def test_mac_dinh_cac_cong_tac_deu_tat():
    settings = Settings(_env_file=None)
    assert settings.main_context_shuffle_seed is None and settings.secondary_target_filter is None


@pytest.mark.parametrize("mode", ["llm", "ml"])
def test_composition_truyen_cong_tac_xuong_use_case(tmp_path, monkeypatch, mode):
    tat = dung_pipeline(tmp_path, monkeypatch, secondary_mode=mode)
    assert tat.main_edges.context_shuffle_seed is None and tat.secondary_edges.target_filter is None
    bat = dung_pipeline(tmp_path, monkeypatch, secondary_mode=mode, main_context_shuffle_seed=11,
                        secondary_target_filter=["b", "a"])
    assert bat.main_edges.context_shuffle_seed == 11 and bat.secondary_edges.target_filter == ["a", "b"]


def test_danh_sach_dich_rong_tu_settings_bao_loi(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="rỗng"):
        dung_pipeline(tmp_path, monkeypatch, secondary_target_filter=[])


def test_phien_ban_pipeline_khi_tat_giong_het_truoc_khi_co_cong_tac(tmp_path):
    settings = Settings(_env_file=None, artifact_dir=tmp_path)
    bo_tay = settings.model_dump(mode="json", exclude={"gemini_api_key", "artifact_dir", *CONG_TAC})
    mong_doi = hashlib.sha256(json.dumps({"settings": bo_tay, "build_policy": _BUILD_POLICY}, sort_keys=True,
                                         separators=(",", ":")).encode()).hexdigest()
    assert _pipeline_version(settings).split(":", 1)[1] == mong_doi


def test_phien_ban_pipeline_doi_khi_bat_cong_tac(tmp_path):
    tat = _pipeline_version(Settings(_env_file=None, artifact_dir=tmp_path))
    assert _pipeline_version(Settings(_env_file=None, artifact_dir=tmp_path, main_context_shuffle_seed=3)) != tat
    assert _pipeline_version(Settings(_env_file=None, artifact_dir=tmp_path, secondary_target_filter=["a"])) != tat
