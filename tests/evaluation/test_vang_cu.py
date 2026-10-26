"""Bộ chuyển vàng A8 cũ sang G3, G4 và bảng căn. Định dạng phải đúng `danh-gia-g3-1` và `danh-gia-g4-1`."""
import pytest

from danhgia.vang.cu import KhongQuyDuoc, chuyen


def vang_cu():
    return {
        "doc_id": "d", "canonical_version": 1, "annotator": "A1+A2 (hội ý)",
        "chapter": {"label": "10-12", "ordinals": [10, 11, 12], "section_ids": ["s1"], "titles": ["x"]},
        "targets": ["t1", "t2", "t3old"],
        "edges": [
            {"prerequisite": "t1", "target": "t2", "evidence_kind": "noi_ro", "source": "both", "note": "", "location": "l1"},
            {"prerequisite": "o1", "target": "t2", "evidence_kind": "trong_dinh_nghia", "source": "A1", "note": "", "location": ""},
            {"prerequisite": "t1", "target": "t3old", "evidence_kind": "mach_trinh_bay", "source": "A2", "note": "", "location": ""},
        ],
    }


TEN = {"t1": "Khái niệm một", "t2": "Khái niệm hai", "t3": "Khái niệm ba", "o1": "Khái niệm ngoài"}


def chay(**kw):
    tham_so = dict(ma_sach="d", ten=TEN, node_ids={"t1", "t2", "t3", "o1"}, redirects={"t3old": "t3"})
    tham_so.update(kw)
    return chuyen(vang_cu(), **tham_so)


def test_g3_la_kho_khai_niem_dung_dinh_dang():
    g3 = chay()["g3"]
    assert g3["schema"] == "danh-gia-g3-1" and g3["ma_sach"] == "d" and g3["nguoi_gan"] == "hoi-y"
    assert [k["ma"] for k in g3["khai_niem"]] == ["G-d-001", "G-d-002", "G-d-003"]
    assert {k["chuong"] for k in g3["khai_niem"]} == {"10-12"}
    assert set(g3["khai_niem"][0]) == {"ma", "chuong", "ten", "ten_khac", "trang_thai", "dinh_nghia", "khong_chac", "ghi_chu"}
    assert g3["tranh_chap"] == []


def test_g4_dung_dinh_dang_va_nguon_ngoai_chuong():
    ket_qua = chay()
    g4 = ket_qua["g4"]
    assert g4["schema"] == "danh-gia-g4-1" and len(g4["quan_he"]) == 3
    assert g4["vang_chinh"] == g4["vang_hop"] == g4["vang_giao"] == g4["quan_he"]
    nguon = {(q["nguon"] if isinstance(q["nguon"], str) else "ngoai", q["dich"]) for q in g4["quan_he"]}
    codes = {k["ten"]: k["ma"] for k in ket_qua["g3"]["khai_niem"]}
    assert ("ngoai", codes["Khái niệm hai"]) in nguon
    ngoai = [q["nguon"] for q in g4["quan_he"] if not isinstance(q["nguon"], str)][0]
    assert ngoai["ngoai"]["ten"] == "Khái niệm ngoài"
    assert all(q["loai"] == "van_ban" for q in g4["quan_he"])


def test_bang_can_dung_bang_chuyen_huong():
    ket_qua = chay()
    can = {(h["vang"] if isinstance(h["vang"], str) else "ngoai"): h for h in ket_qua["can"]["hang"]}
    ma_ba = next(k["ma"] for k in ket_qua["g3"]["khai_niem"] if k["ten"] == "Khái niệm ba")
    assert can[ma_ba]["may"] == "t3" and can[ma_ba]["quan_he"] == "khop"  # t3old chuyển hướng sang t3
    assert can["ngoai"]["may"] == "o1"
    assert ket_qua["bao_cao"]["chuyen_huong"] == {"t3old": "t3"}


def test_khai_niem_khong_quy_duoc_bi_tu_choi_nhu_bo_cham_cu():
    with pytest.raises(KhongQuyDuoc, match="t3old"):
        chay(node_ids={"t1", "t2", "o1"})  # t3 không còn trong đồ thị


def test_cho_phep_chua_can_thi_chuyen_phan_con_lai_va_bao_cao():
    ket_qua = chay(node_ids={"t1", "t2", "o1"}, cho_phep_chua_can=True)
    assert ket_qua["bao_cao"]["chua_can"] == ["t3old"]
    assert not [h for h in ket_qua["can"]["hang"] if h["may"] == "t3"]


def test_ten_thieu_la_loi_khong_dien_ngam():
    with pytest.raises(ValueError, match="t1"):
        chay(ten={"t2": "Khái niệm hai"})


def test_hai_id_cu_cung_chuyen_huong_ve_mot_node_thanh_mot_khai_niem():
    vang = vang_cu()
    vang["targets"] = ["t1", "t2", "t2old"]
    vang["edges"] = [
        {"prerequisite": "t1", "target": "t2", "note": ""},
        {"prerequisite": "t1", "target": "t2old", "note": ""},      # trùng cạnh trên sau khi hợp nhất
        {"prerequisite": "t2old", "target": "t2", "note": ""},      # tự nối sau khi hợp nhất
    ]
    ket_qua = chuyen(vang, ma_sach="d", ten=TEN, node_ids={"t1", "t2"}, redirects={"t2old": "t2"})
    assert [k["ten"] for k in ket_qua["g3"]["khai_niem"]] == ["Khái niệm một", "Khái niệm hai"]
    assert len(ket_qua["g4"]["quan_he"]) == 1
    assert ket_qua["bao_cao"]["canh_tu_noi"] == 1 and ket_qua["bao_cao"]["khai_niem_gop"] == {"t2old": "t2"}
    assert len(ket_qua["can"]["hang"]) == 2
