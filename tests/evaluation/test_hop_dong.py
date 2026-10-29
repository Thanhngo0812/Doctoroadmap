"""Lược đồ `danh-gia-xuat-1` và validator: mỗi loại lỗi một ca riêng, ca hợp lệ đi qua."""
import copy

import pytest

from danhgia.hop_dong import LoiHopDong, kiem, kiem_hoac_loi
from dung_tay import canh, hop_dong, khai_niem


def hop_le():
    hd = hop_dong([khai_niem("a"), khai_niem("b")], [canh("a", "b")], ["a", "b"])
    hd["khai_niem"][0]["vi_tri"] = 0
    hd["khai_niem"][1]["vi_tri"] = 1
    hd["lo_trinh"]["module"] = [{"ma": "m1", "ten": "Module 1", "thanh_vien": ["a", "b"]}]
    return hd


def co_loi(hd, mau):
    loi = kiem(hd)
    assert any(mau in dong for dong in loi), (mau, loi)


def test_hop_dong_hop_le_khong_loi():
    assert kiem(hop_le()) == []
    kiem_hoac_loi(hop_le())


def test_phan_he_khong_co_de_null_duoc():
    hd = hop_le()
    for khoi in ("cau_truc", "cap_ung_vien", "chi_phi", "lo_trinh"):
        hd[khoi] = None
    assert kiem(hd) == []


def test_thieu_khoi_bat_buoc():
    hd = hop_le()
    del hd["canh"]
    co_loi(hd, "canh")


def test_sai_ten_schema():
    hd = hop_le()
    hd["schema"] = "danh-gia-xuat-2"
    co_loi(hd, "schema")


def test_trang_thai_day_ngoai_sau_gia_tri():
    hd = hop_le()
    hd["khai_niem"][0]["trang_thai_day"] = "taught_maybe"
    co_loi(hd, "trang_thai_day")


def test_kieu_du_lieu_sai():
    hd = hop_le()
    hd["canh"][0]["mem"] = "khong"
    co_loi(hd, "mem")


def test_truong_la_khong_duoc_phep():
    hd = hop_le()
    hd["khai_niem"][0]["ghi_chu_la"] = 1
    co_loi(hd, "ghi_chu_la")


def test_canh_tro_toi_khai_niem_khong_co():
    hd = hop_le()
    hd["canh"].append(canh("a", "zzz"))
    co_loi(hd, "zzz")


def test_ma_khai_niem_trung():
    hd = hop_le()
    hd["khai_niem"].append(copy.deepcopy(hd["khai_niem"][0]))
    co_loi(hd, "trùng")


def test_day_hoc_lap():
    hd = hop_le()
    hd["lo_trinh"]["day_hoc"] = ["a", "b", "a"]
    co_loi(hd, "lặp")


def test_day_hoc_co_ma_la():
    hd = hop_le()
    hd["lo_trinh"]["day_hoc"] = ["a", "q"]
    co_loi(hd, "q")


def test_module_thanh_vien_la():
    hd = hop_le()
    hd["lo_trinh"]["module"][0]["thanh_vien"] = ["a", "q"]
    co_loi(hd, "q")


def test_nguon_goc_canh_ngoai_bon_gia_tri():
    hd = hop_le()
    hd["canh"][0]["nguon_goc"] = "tu_nghi_ra"
    co_loi(hd, "nguon_goc")


def test_canh_mem_phai_co_ly_do_va_canh_cung_khong_co():
    hd = hop_le()
    hd["canh"][0]["mem"] = True
    hd["canh"][0]["ly_do_mem"] = None
    co_loi(hd, "ly_do_mem")
    hd = hop_le()
    hd["canh"][0]["ly_do_mem"] = "ngược thứ tự sách"
    co_loi(hd, "ly_do_mem")


def test_ban_do_danh_tinh_tro_toi_khai_niem_la():
    hd = hop_le()
    hd["ban_do_danh_tinh"] = {"a": "ghost"}
    co_loi(hd, "ghost")


def test_cau_neo_phai_du_truong():
    hd = hop_le()
    hd["khai_niem"][0]["cau_neo"] = {"trang": 3, "cau": "x"}  # thiếu ma_chunk
    co_loi(hd, "ma_chunk")


def test_kiem_hoac_loi_gom_moi_loi_vao_mot_ngoai_le():
    hd = hop_le()
    hd["schema"] = "sai"
    del hd["canh"]
    with pytest.raises(LoiHopDong) as ngoai_le:
        kiem_hoac_loi(hd)
    assert len(ngoai_le.value.args[0]) >= 2


def test_duong_vong_chu_la_khoa_tuy_chon_cua_dinh_danh():
    # DG-08b: hợp đồng cũ (không có khoá) vẫn hợp lệ; có khoá thì phải là bool; khoá lạ khác vẫn bị từ chối
    hd = hop_le()
    assert "duong_vong_chu" not in hd["dinh_danh"] and kiem(hd) == []
    for gia_tri in (True, False):
        hd["dinh_danh"]["duong_vong_chu"] = gia_tri
        assert kiem(hd) == []
    hd["dinh_danh"]["duong_vong_chu"] = "co"
    co_loi(hd, "duong_vong_chu")
    del hd["dinh_danh"]["duong_vong_chu"]
    hd["dinh_danh"]["khoa_la"] = 1
    co_loi(hd, "khoa_la")
