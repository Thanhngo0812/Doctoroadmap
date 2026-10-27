"""DG-06 (2): seed xáo ngữ cảnh pass chính. Mặc định None: lời nhắc, khoá cache, hash cấu hình, artifact y hệt trước khi sửa."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges
from test_build_main_edges import Model, Store  # noqa: E402  (tests/unit/application nằm trong rootdir của pytest)

GOLDEN = Path(__file__).resolve().parent / "dg06_vang_mac_dinh_pass_chinh.json"
NODES = [{"node_id": x, "name": x.upper()} for x in "abcdefghij"]
SESSION = {"session_id": "s1", "route": "chapter", "chapter_id": "ch1", "target_node_ids": ["a"],
           "allowed_node_ids": list("abcdefgh"), "chunk_ids": ["c1"]}
CHUNKS = [SimpleNamespace(chunk_id="c1", text="A", order_index=0)]
# i, j chỉ được chunk nhắc tới (không nằm trong allowed): đi qua nhánh mention_map
MENTION = {"c1": {"i": {}, "j": {}}}


def lap_input(**kw):
    use_case = BuildMainEdges(Store(), Model(), parallel_sessions=False, **kw)
    return use_case._input(SESSION, NODES, CHUNKS, MENTION, [], [], {})


def chay_artifact(**kw):
    store, model = Store(), Model()
    use_case = BuildMainEdges(store, model, **kw)
    artifact, _ = use_case.execute("doc")
    return store, model, artifact


def ma_checkpoint(**kw):
    return BuildMainEdges(Store(), Model(), **kw).plan("doc").checkpoint_id


def dau_van_tay_mac_dinh():
    """Những gì phải y hệt trước và sau khi thêm công tắc."""
    store, model, artifact = chay_artifact()
    return {
        "input": lap_input(),
        "prompts": model.calls,
        "main_base_config_hash": artifact.payload["main_base_config_hash"],
        "config_hash": artifact.manifest["config_hash"],
        "checkpoint_id": ma_checkpoint(),
        "main_edges": artifact.payload["main_edges"],
    }


def ten_khoi(value):
    return [row["node_id"] for row in value["mentioned_elsewhere"]]


def test_mac_dinh_y_het_truoc_khi_sua():
    assert json.loads(json.dumps(dau_van_tay_mac_dinh())) == json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_seed_none_tuong_duong_khong_truyen_tham_so():
    assert lap_input(context_shuffle_seed=None) == lap_input()
    a, b = chay_artifact(context_shuffle_seed=None)[2], chay_artifact()[2]
    assert a.payload["main_base_config_hash"] == b.payload["main_base_config_hash"]


def test_mac_dinh_giu_thu_tu_goc():
    assert ten_khoi(lap_input()) == list("bcdefgh") + ["i", "j"]


def test_xao_cung_tap_khoi_khac_thu_tu():
    goc, xao = lap_input(), lap_input(context_shuffle_seed=7)
    assert sorted(ten_khoi(xao)) == sorted(ten_khoi(goc)) and ten_khoi(xao) != ten_khoi(goc)
    for khoa in goc:  # chỉ mentioned_elsewhere đổi
        if khoa != "mentioned_elsewhere":
            assert xao[khoa] == goc[khoa]


def test_cung_seed_cung_thu_tu_seed_khac_thu_tu_khac():
    assert ten_khoi(lap_input(context_shuffle_seed=7)) == ten_khoi(lap_input(context_shuffle_seed=7))
    thu_tu = {tuple(ten_khoi(lap_input(context_shuffle_seed=s))) for s in range(8)}
    assert len(thu_tu) > 1


def test_seed_theo_cach_xao_cua_script_19j():
    import random
    mong_doi = ten_khoi(lap_input())
    random.Random("7:s1").shuffle(mong_doi)
    assert ten_khoi(lap_input(context_shuffle_seed=7)) == mong_doi


def test_seed_vao_hash_cau_hinh_va_khoa_checkpoint_nhung_none_thi_khong():
    goc = chay_artifact()
    xao7, xao8 = chay_artifact(context_shuffle_seed=7), chay_artifact(context_shuffle_seed=8)
    hash_ = lambda ket_qua: ket_qua[2].payload["main_base_config_hash"]  # noqa: E731
    assert len({hash_(goc), hash_(xao7), hash_(xao8)}) == 3
    assert chay_artifact(context_shuffle_seed=7)[2].payload["main_base_config_hash"] == hash_(xao7)
    assert len({ma_checkpoint(), ma_checkpoint(context_shuffle_seed=7), ma_checkpoint(context_shuffle_seed=8)}) == 3
    assert ma_checkpoint(context_shuffle_seed=None) == ma_checkpoint()  # lượt nhiễu không dùng lại checkpoint của lượt chính


def test_luot_nhieu_khong_dung_lai_artifact_cache_cua_luot_chinh():
    store = Store()
    BuildMainEdges(store, Model()).execute("doc")
    _, tai_dung = BuildMainEdges(store, Model(), context_shuffle_seed=7).execute("doc")
    assert tai_dung is False


def test_seed_sai_kieu_bi_tu_choi():
    with pytest.raises(ValueError, match="seed"):
        BuildMainEdges(Store(), Model(), context_shuffle_seed=True)
    with pytest.raises(ValueError, match="seed"):
        BuildMainEdges(Store(), Model(), context_shuffle_seed=1.5)
