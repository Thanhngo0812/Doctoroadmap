"""DG-06 (3): bộ lọc cặp pass phụ theo đích (ml và llm). Mặc định None: mọi thứ y hệt trước khi sửa."""
import json
from pathlib import Path

import pytest

from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges
from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges
from test_build_secondary_edges import PairModel, Store  # noqa: E402
from test_build_secondary_ml_edges import Scorer, Tokenize, fixture as ml_fixture  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "dg06_vang_mac_dinh_pass_phu.json"


def them_nut_c(store):
    """Thêm node c và cặp ac, bc: ab, ac, bc. Mọi cặp đều có thể được hỏi."""
    payload = store.main.payload
    payload["nodes"].append({"node_id": "c", "name": "C", "description": "C", "cluster_id": "g1", "learnable": True,
                             "defining_chunk_ids": ["c1"]})
    payload["mention_map"]["c1"]["c"] = {}
    payload["suspected_pairs"] += [
        {"pair_id": "ac", "left": "a", "right": "c", "sources": ["citation"], "details": {"citation": ["c1"]}},
        {"pair_id": "bc", "left": "b", "right": "c", "sources": ["citation"], "details": {"citation": ["c1"]}},
    ]
    return store


def cap_da_gui(model):
    return sorted({row["dossier"]["pair_id"] for row in model.calls})


def chay_llm(**kw):
    store, model = them_nut_c(Store()), PairModel()
    artifact, _ = BuildSecondaryEdges(store, model, concurrency=2, **kw).execute("doc")
    return store, model, artifact


def chay_ml(**kw):
    scorer = Scorer()
    store = ml_fixture()
    stage = BuildSecondaryMLEdges(store, scorer, Tokenize(), **kw)
    artifact, _ = stage.execute("doc")
    return store, scorer, artifact


def dau_van_tay_mac_dinh():
    store, model, llm = chay_llm()
    _, scorer, ml = chay_ml()
    return {
        "llm": {"prompts": model.calls, "config_hash": llm.payload["secondary_base_config_hash"],
                "edges": llm.payload["secondary_edges"], "log": llm.payload["secondary_log"],
                "checkpoint_id": BuildSecondaryEdges(them_nut_c(Store()), PairModel(), concurrency=2).plan("doc").checkpoint_id},
        "ml": {"config_hash": ml.payload["secondary_base_config_hash"], "edges": ml.payload["secondary_edges"],
               "stats": ml.payload["stats"], "log": ml.payload["secondary_log"]},
    }


def test_mac_dinh_y_het_truoc_khi_sua():
    assert json.loads(json.dumps(dau_van_tay_mac_dinh())) == json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_none_tuong_duong_khong_truyen_tham_so():
    assert cap_da_gui(chay_llm(target_filter=None)[1]) == cap_da_gui(chay_llm()[1]) == ["ab", "ac", "bc"]
    assert (chay_llm(target_filter=None)[2].payload["secondary_base_config_hash"]
            == chay_llm()[2].payload["secondary_base_config_hash"])
    assert (chay_ml(target_filter=None)[2].payload["secondary_base_config_hash"]
            == chay_ml()[2].payload["secondary_base_config_hash"])


def test_llm_cap_ngoai_danh_sach_khong_duoc_gui_di():
    _, model, artifact = chay_llm(target_filter=["c"])
    assert cap_da_gui(model) == ["ac", "bc"]  # ab không chứa đích nào được phép
    assert "ab" not in {row["pair_id"] for row in artifact.payload["secondary_log"]}
    assert "ab" not in artifact.payload["completed_secondary_pairs"]


def test_llm_loc_mot_dich_chi_giu_cap_chua_dich_do():
    assert cap_da_gui(chay_llm(target_filter=["a"])[1]) == ["ab", "ac"]
    assert cap_da_gui(chay_llm(target_filter=["a", "b", "c"])[1]) == ["ab", "ac", "bc"]


def test_llm_ke_hoach_cung_ap_bo_loc():
    use_case = BuildSecondaryEdges(them_nut_c(Store()), PairModel(), concurrency=2, target_filter=["c"])
    assert use_case.plan("doc").remaining_items == 2
    assert BuildSecondaryEdges(them_nut_c(Store()), PairModel(), concurrency=2).plan("doc").remaining_items == 3


def test_llm_bo_loc_vao_hash_cau_hinh_va_checkpoint():
    goc = chay_llm()[2].payload["secondary_base_config_hash"]
    c = chay_llm(target_filter=["c"])[2].payload["secondary_base_config_hash"]
    a = chay_llm(target_filter=["a"])[2].payload["secondary_base_config_hash"]
    assert len({goc, c, a}) == 3
    assert chay_llm(target_filter=["c", "c"])[2].payload["secondary_base_config_hash"] == c  # thứ tự và lặp không đổi nghĩa
    assert chay_llm(target_filter=["c"])[2].payload["secondary_base_config_hash"] == c
    ids = {BuildSecondaryEdges(them_nut_c(Store()), PairModel(), concurrency=2, **kw).plan("doc").checkpoint_id
           for kw in ({}, {"target_filter": ["c"]}, {"target_filter": ["a"]})}
    assert len(ids) == 3


def test_id_dich_khong_co_trong_do_thi_bao_loi_o_ca_hai_che_do():
    # Claude thêm khi nghiệm thu: danh sách đích gõ sai id (hay của sách khác) không được lặng lẽ cho ablation rỗng.
    with pytest.raises(ValueError, match="không id nào trong danh sách đích"):
        chay_ml(target_filter=["zzz"])
    with pytest.raises(ValueError, match="không id nào trong danh sách đích"):
        chay_llm(target_filter=["zzz"])


def test_id_dich_co_trong_do_thi_nhung_khong_cap_nao_thi_hop_le():
    # node c có trong đồ thị ML? fixture ML chỉ có a, b: dùng LLM, nơi c có trong đồ thị; bỏ mọi cặp chứa c thì 0 cặp vẫn hợp lệ.
    store, model = them_nut_c(Store()), PairModel()
    store.main.payload["suspected_pairs"] = [p for p in store.main.payload["suspected_pairs"] if "c" not in (p["left"], p["right"])]
    BuildSecondaryEdges(store, model, concurrency=2, target_filter=["c"]).execute("doc")
    assert cap_da_gui(model) == []


def test_ml_giu_cap_khi_mot_dau_la_dich_cho_phep():
    _, _, loc = chay_ml(target_filter=["b"])
    _, _, goc = chay_ml()
    assert loc.payload["secondary_edges"] == goc.payload["secondary_edges"]
    assert loc.payload["stats"]["secondary_pair_count"] == 1
    assert loc.payload["secondary_base_config_hash"] != goc.payload["secondary_base_config_hash"]


@pytest.mark.parametrize("gia_tri", [[], (), set()])
def test_danh_sach_rong_bao_loi_ro_o_ca_hai_che_do(gia_tri):
    with pytest.raises(ValueError, match="rỗng"):
        BuildSecondaryEdges(Store(), PairModel(), target_filter=gia_tri)
    with pytest.raises(ValueError, match="rỗng"):
        BuildSecondaryMLEdges(ml_fixture(), Scorer(), Tokenize(), target_filter=gia_tri)


@pytest.mark.parametrize("gia_tri", ["c", 5, [1, 2], [None]])
def test_kieu_sai_bi_tu_choi(gia_tri):
    with pytest.raises(ValueError, match="danh sách"):
        BuildSecondaryEdges(Store(), PairModel(), target_filter=gia_tri)
