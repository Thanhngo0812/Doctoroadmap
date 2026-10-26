"""Phép đối chiếu bộ chấm cũ và mới trên fixture nhỏ (cắt từ xstk-ch3-1 v68): mọi sai lệch phải bằng 0."""
from pathlib import Path

import danhgia.doi_chieu as doi_chieu_mod
from danhgia.doi_chieu import doi_chieu

KHO = Path(__file__).resolve().parent / "fixtures" / "kho-nho"
VANG = KHO / "a8-gold" / "xstk-nho-vang.json"


def test_bo_cham_moi_ra_dung_so_cua_bo_cham_cu_tren_fixture():
    ket_qua = doi_chieu(KHO, "xstk-ch3-1", 68, VANG)
    assert ket_qua["lech"] == 0, [h for h in ket_qua["bang"] if h["lech"]]
    assert len(ket_qua["bang"]) >= 35
    # chống đối chiếu rỗng: các số không tầm thường, và có cả ca danh tính, chuyển hướng
    gia = {h["chi_so"]: h["cu"] for h in ket_qua["bang"]}
    assert gia["spec truc_tiep tp"] > 0 and gia["Q6 mẫu (cạnh vàng sau danh tính)"] > 0
    assert gia["cạnh vàng tự nối (danh tính + chuyển hướng)"] >= 1
    assert ket_qua["ghi_chu"]["ban_do_danh_tinh"] == 1


def test_doi_chieu_bat_duoc_khi_bo_cham_moi_lech_mot_don_vi(monkeypatch):
    cham_that = doi_chieu_mod.cham

    def cham_lech(*tham_so, **kw):
        rows = cham_that(*tham_so, **kw)
        for row in rows:
            if row["thuoc"] == "a8.f1_truc_tiep.nghiem":
                row["tp"] += 1
        return rows

    monkeypatch.setattr(doi_chieu_mod, "cham", cham_lech)
    assert doi_chieu(KHO, "xstk-ch3-1", 68, VANG)["lech"] > 0
