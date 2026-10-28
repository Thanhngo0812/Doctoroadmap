"""Căn dòng của bảng dòng (`bang_dong`, bộ đọc nhẹ của `src`) với mục của hệ chính, qua bbox (vé DG-13; seam xuất).

Học theo `scripts/a1-d02/can_dong.py`: mỗi dòng gán cho nút của cây parse có bbox chồng lên >= 50% diện tích dòng (cùng trang, lấy chồng lớn nhất);
tiêu đề được chunker chấp nhận được nhận lại bằng cách khớp chữ chuẩn hoá của nút tiêu đề với tiêu đề mục (cho phép tiêu đề mục ghép nhiều nút liền nhau),
theo thứ tự đọc, bỏ qua nút tiêu đề không có mục (tiêu đề giả bị chunker loại). Lá của một dòng là mục của tiêu đề được chấp nhận gần nhất đứng trước nút
chứa dòng (dòng của chính nút tiêu đề thì lá là mục đó); trước tiêu đề đầu tiên lá là gốc (`None`). Dòng không nút nào phủ đủ thì vào `dong_khong_can`,
không bị bỏ lặng lẽ.
"""
from __future__ import annotations

from doc2roadmap.domain import chunking
from doc2roadmap.domain.normalization import normalize_text

NGUONG_CHONG = 0.5


def _chong(dong, nut):
    dien_tich = max(0.0, dong[2] - dong[0]) * max(0.0, dong[1] - dong[3])
    giao = max(0.0, min(dong[2], nut[2]) - max(dong[0], nut[0])) * max(0.0, min(dong[1], nut[1]) - max(dong[3], nut[3]))
    return giao / dien_tich if dien_tich else 0.0


def nhan_tieu_de(nut_tieu_de, muc):
    """{chỉ số nút: id mục} cho các nút tiêu đề (theo thứ tự đọc) khớp tiêu đề của các mục (bỏ gốc, theo `order_index`)."""
    ket, con = {}, 0
    ds = [normalize_text(n["text"]) for n in nut_tieu_de]
    for m in sorted((m for m in muc if m["level"] > 0), key=lambda m: m.get("order_index", 0)):
        dich = normalize_text(m["title"])
        for bat_dau in range(con, len(nut_tieu_de)):
            tich, j = ds[bat_dau], bat_dau
            while tich != dich and dich.startswith(tich) and j + 1 < len(ds):
                j += 1
                tich = f"{tich} {ds[j]}"
            if tich == dich:
                for k in range(bat_dau, j + 1):
                    ket[k] = m["section_id"]
                con = j + 1
                break
    return ket


def can_dong(nut, muc, bang_dong):
    """`nut`: nút cây parse (`bbox` [x0, top, x1, bottom], `page`, `node_type`, `text`, `reading_order`); `muc`: sections.json;
    `bang_dong`: [{id, trang, text, bbox}]. Trả `ma_dong` ({id mục: [mã dòng của tiêu đề]}), `dong_thuoc_muc`, `dong_khong_can`, `thong_ke`."""
    nut = sorted(nut, key=lambda n: n["reading_order"])
    tieu_de = [(i, n) for i, n in enumerate(nut) if n["node_type"] in chunking.HEADING_TYPES and normalize_text(n["text"])]
    nhan = nhan_tieu_de([n for _, n in tieu_de], muc)
    muc_cua_nut = {tieu_de[k][0]: sid for k, sid in nhan.items()}
    la_cua_nut, hien_tai = {}, None
    for i in range(len(nut)):
        hien_tai = muc_cua_nut.get(i, hien_tai)
        la_cua_nut[i] = hien_tai
    theo_trang = {}
    for i, n in enumerate(nut):
        if n.get("bbox") and n["node_type"] != "figure":
            theo_trang.setdefault(n["page"], []).append((i, n))
    ma_dong = {m["section_id"]: [] for m in muc if m["level"] > 0}
    dong_thuoc_muc, khong_can = {}, []
    for d in bang_dong:
        ung = [(_chong(d["bbox"], n["bbox"]), -(n["bbox"][2] - n["bbox"][0]) * (n["bbox"][1] - n["bbox"][3]), i)
               for i, n in theo_trang.get(d["trang"], [])]
        ung = [u for u in ung if u[0] >= NGUONG_CHONG]
        if not ung:
            khong_can.append(d["id"])
            continue
        i = max(ung)[2]
        dong_thuoc_muc[d["id"]] = la_cua_nut[i]
        if i in muc_cua_nut:
            ma_dong[muc_cua_nut[i]].append(d["id"])
    thong_ke = {"so_dong": len(bang_dong), "so_dong_can": len(dong_thuoc_muc), "so_dong_khong_can": len(khong_can),
                "so_muc": len(ma_dong), "so_muc_nhan_duoc_tieu_de": len(set(muc_cua_nut.values())),
                "so_nut_tieu_de": len(tieu_de)}
    return {"ma_dong": ma_dong, "dong_thuoc_muc": dong_thuoc_muc, "dong_khong_can": khong_can, "thong_ke": thong_ke}
