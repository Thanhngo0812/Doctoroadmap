"""Hằng số của bộ sinh bảng và hình: bảng tra tên thước, nhãn hệ, bảng màu khâu, nhãn lý do quy lỗi.

Mọi chỉ số chính dùng mức căn nghiêm (spec mục 8). Tên thước là tên thật trong dòng số đếm do bộ chấm sinh ra.
"""
MUC = "nghiem"

# Cột Bảng 9: (khoá, nhãn, tên thước, số chữ số thập phân, thấp là tốt)
COT_BANG_9 = (
    ("do_phu", "Độ phủ khái niệm", f"dau_cuoi.do_phu_day_hoc.{MUC}", 3, False),
    ("q6", "Q6 (thấp là tốt)", f"a10.q6.{MUC}", 3, True),
    ("f1", "F1 cạnh tiên quyết", f"a8.f1_truc_tiep.{MUC}", 3, False),
    ("bang_chung", "Bằng chứng có thật", f"truy_nguyen.bang_chung_co_that.{MUC}", 3, False),
    ("phut", "Phút/cuốn", "chi_phi.phut", 1, True),
    ("usd", "USD/cuốn", "chi_phi.usd", 2, True),
)
# Thước chi phí không nằm trong dòng số đếm của bộ chấm: sinh từ khối `chi_phi` của hợp đồng (xem so_lieu.dong_chi_phi)
THUOC_PHUT, THUOC_PHUT_KHONG_CHO, THUOC_USD = "chi_phi.phut", "chi_phi.phut_khong_cho_embedding", "chi_phi.usd"
THUOC_CHAT_LUONG = tuple(c[2] for c in COT_BANG_9[:4])

# Hàng Bảng 9: (khoá hệ, nhãn)
HE_BANG_9 = (
    ("chinh", "Hệ chính"),
    ("b1", "B1 mục lục"),
    ("b2", "B2 luật đơn giản"),
    ("b5", "B5 mô hình đọc thẳng"),
    ("tran_nguoi", "Trần người (F1 giữa hai sinh viên)"),
)
HE_TRAN_NGUOI = "tran_nguoi"
THU_TU_HE = ("chinh", "b1", "b2", "b5")


def thu_tu_he(he):
    return THU_TU_HE.index(he) if he in THU_TU_HE else len(THU_TU_HE)


THUOC_F1 = f"a8.f1_truc_tiep.{MUC}"
THUOC_Q6 = f"a10.q6.{MUC}"
THUOC_BANG_CHUNG = f"truy_nguyen.bang_chung_co_that.{MUC}"
# B5 chạy ở chế độ a hoặc b (giao thức còn CHỜ): hợp đồng đặt he là b5a hoặc b5b
HE_B5_CO_THE = ("b5", "b5a", "b5b")

# Ba phép kiểm định chính thức (giao thức mục 9): (tên, thước, hệ A, hệ B, thấp là tốt)
KIEM_DINH = (
    ("q6_chinh_so_b1", THUOC_Q6, "chinh", "b1", True),
    ("f1_chinh_so_b5", THUOC_F1, "chinh", "b5", False),
    ("bang_chung_chinh_so_b5", THUOC_BANG_CHUNG, "chinh", "b5", False),
)

# Bảng 10: (khâu, nhãn thước chính, [(nhãn phụ, tên thước)], có trần người)
BANG_10 = (
    ("A1", "M3", [("", "a1.m3")], False),
    ("A2", 'độ phủ vai trò "nội dung"', [("", "a2.recall_noi_dung_muc")], False),
    ("A3", "độ phủ khái niệm", [("", f"a3.do_phu.{MUC}")], False),
    ("A4", "tỉ lệ tách / gộp nhầm", [("tách", f"a4.ti_le_tach.{MUC}"), ("gộp nhầm", f"a4.ti_le_gop_nham.{MUC}")], False),
    ("A5", "câu định nghĩa đúng; độ chính xác trạng thái",
     [("câu", f"a5.cau_neo_dung.{MUC}"), ("trạng thái", f"a5.trang_thai_chinh_xac.{MUC}")], False),
    ("A8", "F1 cạnh", [("", THUOC_F1)], True),
    ("A10", "Q6", [("", THUOC_Q6)], False),
)

# Bảng 11: (khoá hệ, nhãn, [(nhãn chỉ số, tên thước, số chữ số)], nhóm). Hệ không có dòng nào thì hiện "— (không chạy)".
BANG_11 = (
    ("docling", "docling thay bộ đọc nhẹ (3–4 cuốn)", [("M3", "a1.m3", 3), ("F1", THUOC_F1, 3)], "thật"),
    ("pass_phu_llm", "bước phụ A8 bằng mô hình ngôn ngữ (cặp của 3 chương bốc)", [("F1", THUOC_F1, 3)], "thật"),
    ("bo_pass_chinh", "bỏ quan hệ của bước suy luận chính", [("F1", THUOC_F1, 3)], "thật"),
    ("bo_pass_phu", "bỏ quan hệ của bước phụ", [("F1", THUOC_F1, 3)], "thật"),
    ("tat_r17", "tắt R17", [("Q6", THUOC_Q6, 3)], "thật"),
    ("tat_a2", "tắt gán vai trò vùng A2 (nếu chạy)", [("recall nội dung", "a2.recall_noi_dung_muc", 3)], "thật"),
    ("tat_a5", "tắt lọc trạng thái dạy A5 (nếu chạy)", [("độ phủ", f"dau_cuoi.do_phu_day_hoc.{MUC}", 3)], "thật"),
    ("logistic", "hồi quy logistic thay LightGBM (A1 và bước phụ A8)", [("M3", "a1.m3", 3), ("F1", THUOC_F1, 3)], "thật"),
    ("cross_encoder", "cross-encoder thay LightGBM ở bước phụ A8", [("F1", THUOC_F1, 3)], "thật"),
    ("oracle_a8", "oracle A8 (khái niệm vàng)", [("F1", THUOC_F1, 3)], "oracle"),
    ("oracle_a10", "oracle A10 (quan hệ vàng)", [("Q6", THUOC_Q6, 3)], "oracle"),
)

HE_NHAN = {**dict(HE_BANG_9), **{k: n for k, n, _, _ in BANG_11}}

# Hình 4: lý do quy lỗi -> (khâu, nhãn theo Bảng 8). Khâu dùng chung một bảng màu với Hình 1.
LY_DO = {
    1: ("A1/A2", "Mục cắt sai hoặc sai vai trò"),
    2: ("A3", "Không trích được khái niệm"),
    3: ("A4", "Gộp nhầm hoặc tách đôi"),
    4: ("A5", "Bị bỏ khỏi dãy học"),
    5: ("A6/A7", "Cặp không được xét"),
    6: ("A8", "Suy luận không đề xuất"),
    7: ("A9/A10", "Làm mềm hoặc xếp sai"),
}
# Bảng màu khâu (hex sáng, hex tối): bảy ô đầu của bảng màu phân loại trong skill dataviz, đúng thứ tự, đã qua validate_palette cả hai nền.
MAU_KHAU = {
    "A1/A2": ("#2a78d6", "#3987e5"),
    "A3": ("#eb6834", "#d95926"),
    "A4": ("#1baf7a", "#199e70"),
    "A5": ("#eda100", "#c98500"),
    "A6/A7": ("#e87ba4", "#d55181"),
    "A8": ("#008300", "#008300"),
    "A9/A10": ("#6250d6", "#9085e9"),
}
# Hai cột đầu và cuối của thác nước không thuộc khâu nào: màu trung tính
MAU_TONG = ("#898781", "#898781")
MAU_DUNG = ("#52514e", "#c3c2b7")
