"""B4 gộp theo tên: ứng viên A3 của hệ chính gộp **chỉ** khi trùng tên sau chuẩn hoá (`danhgia.ten.chuan_hoa`).

- Ứng viên lấy từ `source_candidates` của canonical mà hệ chính dùng; chỉ ứng viên `learnable` (A3 đã tự loại phần còn lại, B4 giữ nguyên
  ranh giới đó); gộp theo tên chính, không gộp theo tên khác, không gộp mờ, không có bước LLM;
- khái niệm: tên = tên của ứng viên đầu nhóm; tên khác = tên và alias khác (đã bỏ trùng) của các ứng viên trong nhóm; câu neo = bằng chứng
  đầu tiên của ứng viên đầu nhóm (câu trích nguyên văn, trang theo chunk); trạng thái dạy `taught` cho mọi nhóm;
- dãy học theo vị trí xuất hiện đầu tiên (`first_order_index`), không có cạnh.
"""
from __future__ import annotations

from danhgia.ten import chuan_hoa

from .chung import dung_hop_dong, khai_niem_mau


def _ten(muc):
    return muc.get("name") if isinstance(muc, dict) else muc


def hop_dong_b4(hop_dong_chinh, ung_vien, trang_chunk):
    """`ung_vien`: danh sách ứng viên A3; `trang_chunk`: `{chunk_id: số trang}`."""
    nhom, thu_tu = {}, []
    for u in ung_vien:
        khoa = chuan_hoa(u["name"])
        if not u.get("learnable") or not khoa:
            continue
        if khoa not in nhom:
            nhom[khoa] = []
            thu_tu.append(khoa)
        nhom[khoa].append(u)
    khoa_xep = sorted(thu_tu, key=lambda k: (min(u["first_order_index"] for u in nhom[k]), nhom[k][0]["candidate_id"]))
    khai_niem = []
    for khoa in khoa_xep:
        dau = nhom[khoa][0]
        khac = []
        for u in nhom[khoa]:
            for ten in [u["name"], *(_ten(a) for a in u.get("aliases", []))]:
                if isinstance(ten, str) and ten != dau["name"] and ten not in khac:
                    khac.append(ten)
        bang_chung = dau["evidence"][0] if dau.get("evidence") else None
        cau_neo = None
        if bang_chung:
            cau_neo = {"trang": trang_chunk.get(bang_chung["chunk_id"]), "cau": bang_chung["quote"],
                       "ma_chunk": bang_chung["chunk_id"]}
        khai_niem.append(khai_niem_mau(f"b4-{len(khai_niem) + 1:03d}", dau["name"], kieu=dau.get("node_type") or "concept",
                                       cau_neo=cau_neo, vi_tri=len(khai_niem), ten_khac=khac,
                                       ung_vien_goc=[u["candidate_id"] for u in nhom[khoa]]))
    return dung_hop_dong(hop_dong_chinh, "b4", khai_niem, tham_so={"gop": "trung_ten_sau_chuan_hoa"})
