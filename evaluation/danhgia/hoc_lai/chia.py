"""Chia dữ liệu theo cuốn: vòng ngoài LOBO, vòng trong chọn cuốn dừng sớm tất định theo seed và mã cuốn để ra."""
import hashlib

from danhgia.thong_ke.lcg import Lcg


def lobo(cuon):
    """[(cuốn để ra, các cuốn còn lại)] theo thứ tự mã cuốn."""
    tat_ca = sorted(cuon)
    return [(de_ra, [c for c in tat_ca if c != de_ra]) for de_ra in tat_ca]


def _seed_cua(seed, khoa):
    return int.from_bytes(hashlib.sha256(f"{seed}:{khoa}".encode("utf-8")).digest()[:8], "big")


def _xao_mot_phan(phan_tu, so_lay, sinh):
    """Fisher-Yates dừng sau `so_lay` bước: `so_lay` phần tử đầu của hoán vị."""
    mang = list(phan_tu)
    for i in range(so_lay):
        j = i + sinh.chi_so(len(mang) - i)
        mang[i], mang[j] = mang[j], mang[i]
    return mang[:so_lay]


def chon_dung_som(cuon, de_ra, *, seed, so_cuon=3):
    """Trong các cuốn còn lại sau khi bỏ `de_ra`, chọn `so_cuon` cuốn làm tập dừng sớm. Trả (dừng sớm, học), cả hai đã sắp theo mã.

    Kết quả chỉ phụ thuộc `seed`, `de_ra` và tập mã cuốn, không phụ thuộc thứ tự đầu vào.
    """
    con_lai = sorted(c for c in cuon if c != de_ra)
    dung = sorted(_xao_mot_phan(con_lai, so_cuon, Lcg(_seed_cua(seed, de_ra))))
    return dung, [c for c in con_lai if c not in dung]


def kiem_tra_khong_ro_ri(de_ra, dung, hoc):
    if de_ra in dung or de_ra in hoc:
        raise ValueError(f"rò rỉ: cuốn để ra {de_ra} nằm trong tập học hay tập dừng sớm")
    chung = set(dung) & set(hoc)
    if chung:
        raise ValueError(f"rò rỉ: tập dừng sớm và tập học chung {sorted(chung)}")


def vong_ngoai(cuon, hoc_va_cham, *, seed, chia=chon_dung_som, kiem_tra=True):
    """Chạy LOBO: với mỗi cuốn để ra gọi `hoc_va_cham(cuốn_học, cuốn_dừng_sớm, cuốn_để_ra)` và gom kết quả theo cuốn để ra.

    `kiem_tra=False` chỉ dùng trong test để chứng minh bài kiểm rò rỉ có răng.
    """
    ket_qua = {}
    for de_ra, _ in lobo(cuon):
        dung, hoc = chia(cuon, de_ra, seed=seed)
        if kiem_tra:
            kiem_tra_khong_ro_ri(de_ra, dung, hoc)
        ket_qua[de_ra] = hoc_va_cham(hoc, dung, de_ra)
    return ket_qua


def chia_dong(so_dong, ti_le_de_ra, *, seed):
    """Chia ngẫu nhiên theo dòng (chỉ dùng làm phép phá để cho thấy rò rỉ cuốn). Trả (chỉ số để ra, chỉ số học)."""
    chi_so = _xao_mot_phan(range(so_dong), so_dong, Lcg(seed))
    n = int(round(so_dong * ti_le_de_ra))
    return sorted(chi_so[:n]), sorted(chi_so[n:])


def chia_k_phan(cuon, so_phan, *, seed):
    """Chia các cuốn thành `so_phan` phần cùng số cuốn, tất định theo seed (phần C: 16 cuốn → 4 phần × 4 cuốn). Trả [[cuốn]] mỗi phần đã sắp theo mã."""
    tat_ca = sorted(cuon)
    if not tat_ca or len(tat_ca) % so_phan:
        raise ValueError(f"{len(tat_ca)} cuốn không chia đều thành {so_phan} phần")
    xao = _xao_mot_phan(tat_ca, len(tat_ca), Lcg(_seed_cua(seed, "chia-k-phan")))
    co = len(tat_ca) // so_phan
    return [sorted(xao[i * co:(i + 1) * co]) for i in range(so_phan)]
