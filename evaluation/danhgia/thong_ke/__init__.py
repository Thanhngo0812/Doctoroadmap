"""Thống kê và đồng thuận cho đánh giá Pha A (spec `doc/danh-gia-pha-a-spec.md`, mục 8–9; vé DG-05).

Thuần: không gọi mô hình, không đọc kho, không nhập `doc2roadmap`. Đầu vào là bảng số đếm theo chương do lõi chấm sinh ra.
"""
from danhgia.thong_ke.bootstrap import bootstrap_phan_cap
from danhgia.thong_ke.cong_suat import mo_phong_cong_suat
from danhgia.thong_ke.dong_thuan import cohen_kappa, krippendorff_alpha, psa
from danhgia.thong_ke.kiem_dinh import hoan_vi_ghep_cap, holm, sign_test
from danhgia.thong_ke.so_dem import thuoc_theo_cuon
from danhgia.thong_ke.wilson import wilson

__all__ = [
    "bootstrap_phan_cap",
    "cohen_kappa",
    "hoan_vi_ghep_cap",
    "holm",
    "krippendorff_alpha",
    "mo_phong_cong_suat",
    "psa",
    "sign_test",
    "thuoc_theo_cuon",
    "wilson",
]
