"""Mô phỏng công suất trước khi chốt giao thức (Card và cộng sự 2020, VL §9).

Gần đúng có chủ ý: làm trên **hiệu thước theo chương** (hệ A − hệ B) đo ở tập phát triển, không trên số đếm. Mỗi lần mô phỏng:
1. lấy lại `so_cuon × so_chuong` hiệu chương từ tập phát triển, đã trừ trung bình (giả thuyết không), cộng `hieu_ung`;
2. kiểm định đổi dấu ghép cặp phân tầng: đổi dấu từng chương, thống kê là trung bình các trung bình cuốn;
3. đếm tỉ lệ p < alpha.
Kiểm định thật (DG-05 `hoan_vi_ghep_cap`) tính lại thước từ số đếm, nên số ở đây chỉ để ước cỡ hiệu ứng phát hiện được.
"""
from danhgia.thong_ke.lcg import Lcg


def _thong_ke(cac_cuon):
    return sum(sum(ch) / len(ch) for ch in cac_cuon) / len(cac_cuon)


def mo_phong_cong_suat(hieu_chuong, *, hieu_ung, so_cuon=8, so_chuong=3, so_mo_phong=1000, so_hoan_vi=1000, alpha=0.05,
                       seed=20261114):
    if len(hieu_chuong) < 2:
        raise ValueError("cần ít nhất hai hiệu chương từ tập phát triển")
    tb = sum(hieu_chuong) / len(hieu_chuong)
    goc = [h - tb for h in hieu_chuong]
    sinh = Lcg(seed)
    bac_bo = 0
    for _ in range(so_mo_phong):
        cac_cuon = [[goc[sinh.chi_so(len(goc))] + hieu_ung for _ in range(so_chuong)] for _ in range(so_cuon)]
        quan_sat = abs(_thong_ke(cac_cuon))
        cuc_doan = 0
        for _ in range(so_hoan_vi):
            xao = [[-h if sinh.dong_xu() else h for h in cuon] for cuon in cac_cuon]
            if abs(_thong_ke(xao)) >= quan_sat - 1e-12:
                cuc_doan += 1
        if (cuc_doan + 1) / (so_hoan_vi + 1) < alpha:
            bac_bo += 1
    return {"hieu_ung": hieu_ung, "cong_suat": bac_bo / so_mo_phong, "so_mo_phong": so_mo_phong}
