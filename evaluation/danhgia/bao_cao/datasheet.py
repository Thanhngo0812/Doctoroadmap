"""Khung datasheet cho bộ vàng, theo Gebru và cộng sự (2021), "Datasheets for Datasets", và mục D của danh mục ACL (vé DG-17; spec mục 16).

Phần chỉ số điền tự động từ manifest, kho chốt G3, vàng G4 và các tệp đồng thuận; chỉ có số, mã sách, chủ đề và hash. Phần chừa chỗ điền tay ghi `[ĐIỀN TAY]`.
Không bao giờ ghi tên người thật, tên khái niệm hay câu của sách: `dung_so_lieu` chỉ lấy độ dài danh sách và trường số.
"""
from __future__ import annotations

import hashlib

TRANG_THAI_G3 = ("day_o_day", "day_qua_vi_du", "chi_nhac", "kien_thuc_nen")
LOP_G4 = ("vang_chinh", "vang_hop", "vang_giao", "kien_thuc", "tranh_chap", "loai")
SO_NGUOI_GAN = 16
DIEN_TAY = "[ĐIỀN TAY]"


def sha256_tep(duong):
    return hashlib.sha256(open(duong, "rb").read()).hexdigest()


def _dem_ds(tep, khoa):
    """Số phần tử của một danh sách; tệp không có khoá đó thì `None` (hiện —), không phải 0."""
    return len(tep[khoa]) if khoa in tep else None


def dung_so_lieu(manifests, g3s, g4s, dt_g3, dt_g4, hash_vang):
    """`manifests`: list manifest; `g3s`, `g4s`: `{ma_sach: tệp}`; `dt_g3`, `dt_g4`: `{ma_sach: kết quả đếm đồng thuận}`; `hash_vang`: `{ma_sach: {g3, g4}}`."""
    sach = {}
    for m in sorted(manifests, key=lambda m: m["ma_sach"]):
        ma = m["ma_sach"]
        boc = (m.get("boc") or {}).get("chuong") or []
        sach[ma] = {"chu_de": m.get("chu_de"), "tap": m.get("tap"), "so_trang": m.get("so_trang"), "so_chuong": len(m.get("chuong") or []),
                    "so_chuong_boc": len(boc), "pdf_sha256": m.get("pdf_sha256"), "g3": None, "g4": None, "dong_thuan_g3": None, "dong_thuan_g4": None,
                    "hash_vang": hash_vang.get(ma)}
    for ma, kho in g3s.items():
        s = sach[ma]
        tt = {t: sum(k.get("trang_thai") == t for k in kho["khai_niem"]) for t in TRANG_THAI_G3}
        s["g3"] = {"khai_niem": len(kho["khai_niem"]), "theo_trang_thai": tt, "trang_thai_tranh_chap": sum(k.get("trang_thai") is None for k in kho["khai_niem"]),
                   "loai": _dem_ds(kho, "loai"), "tranh_chap": _dem_ds(kho, "tranh_chap")}
    for ma, vang in g4s.items():
        sach[ma]["g4"] = {**{lop: _dem_ds(vang, lop) for lop in LOP_G4}, "bao_ham_bac_cau": vang.get("bao_ham_bac_cau")}
    for ma, d in dt_g3.items():
        sach[ma]["dong_thuan_g3"] = d["tong"]
    for ma, d in dt_g4.items():
        sach[ma]["dong_thuan_g4"] = {"khong_bac_cau": d["khong_bac_cau"]["tong"]["tong"], "bac_cau": d["bac_cau"]["tong"]["tong"]}
    return {"sach": sach, "tong": _tong(sach)}


def _tong(sach):
    def cong(lay):
        gia = [lay(s) for s in sach.values()]
        co = [g for g in gia if g is not None]
        return sum(co) if co else None

    return {"so_cuon": len(sach), "so_trang": cong(lambda s: s["so_trang"]), "so_chuong": cong(lambda s: s["so_chuong"]),
            "so_chuong_boc": cong(lambda s: s["so_chuong_boc"]),
            "so_khai_niem": cong(lambda s: s["g3"] and s["g3"]["khai_niem"]),
            "so_khai_niem_loai": cong(lambda s: s["g3"] and s["g3"]["loai"]),
            "so_khai_niem_tranh_chap": cong(lambda s: s["g3"] and s["g3"]["tranh_chap"]),
            **{f"so_canh_{lop}": cong(lambda s, lop=lop: s["g4"] and s["g4"][lop]) for lop in LOP_G4}}


def _o(x):
    return "—" if x is None else str(x)


def _f1(d):
    if d is None or d.get("f1") is None:
        return "—"
    return f"{d['f1']:.3f}".replace(".", ",")


def dung_md(sl):
    sach, tong = sl["sach"], sl["tong"]
    d = ["# Phiếu mô tả bộ dữ liệu vàng (datasheet) của đánh giá Pha A", "",
         "Theo mẫu Gebru và cộng sự (2021) và mục D của danh mục báo cáo nghiên cứu có trách nhiệm của ACL. "
         f"Các bảng số điền tự động; chỗ ghi {DIEN_TAY} do người giữ bộ vàng điền tay. Tệp này không bao giờ chứa tên người gán, tên khái niệm hay câu của sách.", "",
         "## 1. Chỉ số tự động", "",
         f"Bộ vàng gồm {tong['so_cuon']} cuốn; {_o(tong['so_trang'])} trang; {_o(tong['so_chuong'])} chương, trong đó {_o(tong['so_chuong_boc'])} chương bốc để gán.", "",
         "| Mã sách | Chủ đề | Tập | Số trang | Số chương | Chương bốc | SHA-256 PDF |", "|---|---|---|---|---|---|---|"]
    for ma, s in sach.items():
        d.append(f"| {ma} | {_o(s['chu_de'])} | {_o(s['tap'])} | {_o(s['so_trang'])} | {_o(s['so_chuong'])} | {_o(s['so_chuong_boc'])} | `{_o(s['pdf_sha256'])}` |")
    d += ["", "### 1.1 Khái niệm (G3, vàng sau hội ý)", "",
          "| Mã sách | Khái niệm vào kho | " + " | ".join(TRANG_THAI_G3) + " | Trạng thái tranh chấp | Bị loại | Tranh chấp |", "|---|---|" + "---|" * (len(TRANG_THAI_G3) + 3)]
    for ma, s in sach.items():
        g = s["g3"]
        d.append(f"| {ma} | {_o(g and g['khai_niem'])} | " + " | ".join(_o(g and g["theo_trang_thai"][t]) for t in TRANG_THAI_G3)
                 + f" | {_o(g and g['trang_thai_tranh_chap'])} | {_o(g and g['loai'])} | {_o(g and g['tranh_chap'])} |")
    d += ["", f"Tổng khái niệm vào kho: {_o(tong['so_khai_niem'])}; bị loại: {_o(tong['so_khai_niem_loai'])}; tranh chấp: {_o(tong['so_khai_niem_tranh_chap'])}.", "",
          "### 1.2 Cạnh tiên quyết (G4, theo lớp vàng)", "", "| Mã sách | " + " | ".join(LOP_G4) + " | Bao hàm bắc cầu |", "|---|" + "---|" * (len(LOP_G4) + 1)]
    for ma, s in sach.items():
        g = s["g4"]
        d.append(f"| {ma} | " + " | ".join(_o(g and g[lop]) for lop in LOP_G4) + f" | {_o(g and g['bao_ham_bac_cau'])} |")
    d += ["", "Lớp `vang_chinh` là cạnh vào vàng chính (cả hai người giữ), `vang_hop` thêm cạnh tranh chấp, `vang_giao` chỉ cạnh cả hai người cùng ghi, "
          "`kien_thuc` là cạnh kiến thức nền, `loai` là cạnh bị loại sau hội ý.", "",
          "### 1.3 Đồng thuận giữa hai người gán (F1 = 2a / (2a + b + c))", "", "| Mã sách | G3 F1 | G4 F1 (không bắc cầu) | G4 F1 (bắc cầu) |", "|---|---|---|---|"]
    for ma, s in sach.items():
        g4 = s["dong_thuan_g4"] or {}
        d.append(f"| {ma} | {_f1(s['dong_thuan_g3'])} | {_f1(g4.get('khong_bac_cau'))} | {_f1(g4.get('bac_cau'))} |")
    d += ["", "### 1.4 Mã băm của vàng", "", "| Mã sách | SHA-256 G3 | SHA-256 G4 |", "|---|---|---|"]
    for ma, s in sach.items():
        h = s["hash_vang"] or {}
        d.append(f"| {ma} | `{_o(h.get('g3'))}` | `{_o(h.get('g4'))}` |")
    d += ["", "## 2. Người gán (điền tay, ẩn danh)", "",
          "Mỗi người gán một mã S1 đến S16. Không ghi tên người thật.", "",
          "| Mã | Ngành | Năm học | Kinh nghiệm | Cuốn đã gán |", "|---|---|---|---|---|"]
    d += [f"| S{i} | {DIEN_TAY} | {DIEN_TAY} | {DIEN_TAY} | {DIEN_TAY} |" for i in range(1, SO_NGUOI_GAN + 1)]
    d += ["", "- Cách tuyển người gán: " + DIEN_TAY, "- Thù lao: " + DIEN_TAY, "- Đồng ý tham gia (cách xin và lưu): " + DIEN_TAY, "",
          "## 3. Các mục theo Gebru và cộng sự (điền tay)", "",
          "- Động cơ (vì sao tạo bộ dữ liệu, ai tạo, ai tài trợ): " + DIEN_TAY,
          "- Thành phần (mỗi mẫu là gì, có nhãn nhạy cảm hay thông tin cá nhân không): " + DIEN_TAY,
          "- Quy trình thu thập (nguồn sách, quyền sử dụng, cách chọn chương bốc): " + DIEN_TAY,
          "- Tiền xử lý và gán nhãn (hướng dẫn gán G3, G4, G5, hội ý một vòng): " + DIEN_TAY,
          "- Cách dùng đã dự kiến và không nên dùng: " + DIEN_TAY,
          "- Phân phối (ai được xem, giấy phép): vàng tập thử nằm ngoài repo; repo chỉ giữ mã băm và số tổng. " + DIEN_TAY,
          "- Bảo trì (người giữ, cách báo lỗi): " + DIEN_TAY, "",
          "## 4. Giới hạn (điền tay)", "",
          "- Phạm vi: G3 và G4 chỉ phủ các chương bốc, không phủ cả cuốn. " + DIEN_TAY,
          "- Thiên lệch của người gán và của bộ sách: " + DIEN_TAY,
          "- Những điều bộ vàng không đo được: " + DIEN_TAY, "",
          "## 5. Khai việc dùng AI", "",
          "- Codex nháp cây mục G1 và vai trò vùng G2 để sinh viên duyệt. Phiên bản và ngày: " + DIEN_TAY,
          "- Claude hỗ trợ căn khái niệm giữa vàng và đầu ra của hệ, có người kiểm lại một phần. Phiên bản và ngày: " + DIEN_TAY,
          "- Sonnet rà soát lượt đầu các đầu ra lớn. Phiên bản và ngày: " + DIEN_TAY,
          "- Các khâu không dùng AI (nếu có): " + DIEN_TAY, ""]
    return "\n".join(d)
