"""DG-11: baseline B2, B3, B4 (hàm thuần, đầu ra tính tay). B1 và các biến thể phát lại nằm ở `test_phat_lai.py`."""
import copy

import pytest

import dung_tay as dt
from danhgia.hop_dong import kiem
from danhgia.ten import xuat_hien
from danhgia.xuat.baseline.b2 import canh_b2
from danhgia.xuat.baseline.b3 import bo_so_muc, hop_dong_b3
from danhgia.xuat.baseline.b4 import hop_dong_b4

# ---------- B2: sách thiên văn/thống kê nhỏ, tự soạn ----------

C0 = "Lượn là một khái niệm thử."
C1 = "Tổng thể là tập hợp các phần tử. Mẫu là một phần của tổng thể được chọn ra."
C2 = "Phương sai mẫu đo độ phân tán của mẫu. Độ lệch chuẩn là căn bậc hai của phương sai."
C3 = "Ước lượng điểm dùng mẫu để ước lượng tham số. Tham số là đặc trưng của tổng thể."
C4 = "Kiểm định giả thiết dùng ước lượng của tham số."
CHUNKS = [
    {"chunk_id": "c0", "order_index": 0, "text": C0, "page": 1},
    {"chunk_id": "c1", "order_index": 1, "text": C1, "page": 1},
    {"chunk_id": "c2", "order_index": 2, "text": C2, "page": 2},
    {"chunk_id": "c3", "order_index": 3, "text": C3, "page": 2},
    {"chunk_id": "c4", "order_index": 4, "text": C4, "page": 3},
]
# (mã, tên, tên khác, chunk, câu neo, trong dãy học)
KHAI_NIEM_B2 = [
    ("K7", "Lượn", [], "c0", C0, True),
    ("K1", "Tổng thể", [], "c1", "Tổng thể là tập hợp các phần tử.", True),
    ("K2", "Mẫu", [], "c1", "Mẫu là một phần của tổng thể được chọn ra.", True),
    ("K3", "Phương sai", [], "c2", "Phương sai mẫu đo độ phân tán của mẫu.", True),
    ("K4", "Độ lệch chuẩn", [], "c2", "Độ lệch chuẩn là căn bậc hai của phương sai.", True),
    ("K5", "Ước lượng điểm", ["ước lượng"], "c3", "Ước lượng điểm dùng mẫu để ước lượng tham số.", True),
    ("K6", "Tham số", [], "c3", "Tham số là đặc trưng của tổng thể.", True),
    ("K8", "Kiểm định", [], "c4", C4, True),
    ("K9", "Phần tử", [], "c1", "Tổng thể là tập hợp các phần tử.", False),  # nhắc trong c1 nhưng hệ chính không dạy
    ("K10", "Tập hợp", [], "c1", "Tổng thể là tập hợp các phần tử.", True),  # cùng câu neo với K1: vị trí dạy bằng nhau
]


def hd_b2(khai_niem=KHAI_NIEM_B2):
    ks = []
    for ma, ten, khac, chunk, cau, day in khai_niem:
        k = dt.khai_niem(ma, ten, trong_day_hoc=day)
        k["ten_khac"] = list(khac)
        k["cau_neo"] = {"trang": 1, "cau": cau, "ma_chunk": chunk}
        ks.append(k)
    return dt.hop_dong(ks, [], [])


# Tính tay: cửa sổ = chunk của câu neo; cạnh X -> Y khi X dạy trước hẳn Y và tên/tên khác của X nằm trong cửa sổ của Y.
#   K2: cửa sổ c1 chứa "tổng thể" -> K1.      K3: c2 chứa "mẫu" -> K2.     K4: c2 chứa "phương sai" (K3), "mẫu" (K2).
#   K5: c3 chứa "tổng thể" (K1), "mẫu" (K2).  K6: c3 chứa "ước lượng điểm" (K5), "tổng thể" (K1), "mẫu" (K2).
#   K8: c4 chứa "ước lượng" (tên khác của K5), "tham số" (K6).
#   K1: cửa sổ c1 chứa "mẫu" (K2) nhưng K2 dạy sau K1 -> không có cạnh.  K7 "lượn" không khớp "lượng" (khác âm tiết).
#   K10 cùng câu neo với K1 (vị trí dạy bằng nhau): K1 và K10 không có cạnh nào giữa chúng; K10 dạy trước K2 và "tập hợp" nằm
#   trong cửa sổ c1 của K2 -> K10 -> K2.
#   K9 không trong dãy học -> không bao giờ là đầu cạnh dù "phần tử" nằm trong c1.
CANH_B2 = {("K1", "K2"), ("K2", "K3"), ("K2", "K4"), ("K3", "K4"), ("K1", "K5"), ("K2", "K5"), ("K1", "K6"), ("K2", "K6"),
           ("K5", "K6"), ("K5", "K8"), ("K6", "K8"), ("K10", "K2")}


def cap(canh):
    return {(c["source"], c["target"]) for c in canh}


def test_b2_canh_tinh_tay():
    assert cap(canh_b2(hd_b2(), CHUNKS)) == CANH_B2


def test_b2_khop_theo_am_tiet_khong_theo_chuoi_con():
    canh = cap(canh_b2(hd_b2(), CHUNKS))
    assert not {c for c in canh if c[0] == "K7"}  # "lượn" là chuỗi con của "lượng" nhưng không phải âm tiết
    assert xuat_hien("Lượn", "Ước lượng điểm") is False


def test_b2_x_phai_day_truoc_y():
    canh = cap(canh_b2(hd_b2(), CHUNKS))
    assert ("K2", "K1") not in canh  # tên K2 nằm trong cửa sổ K1 nhưng K2 dạy sau
    assert ("K6", "K5") not in canh  # tên K6 nằm trong cửa sổ K5 (cùng chunk) nhưng câu neo của K6 đứng sau
    assert len(canh) == len(CANH_B2)  # chặn kiểm vô nghĩa: tập cạnh không rỗng


def test_b2_dong_vi_tri_day_khong_phai_day_truoc():
    canh = cap(canh_b2(hd_b2(), CHUNKS))
    assert ("K1", "K10") not in canh and ("K10", "K1") not in canh


def test_b2_chi_xet_khai_niem_trong_day_hoc():
    assert not [c for c in canh_b2(hd_b2(), CHUNKS) if "K9" in (c["source"], c["target"])]


def test_b2_ten_khac_cung_khop():
    canh = canh_b2(hd_b2(), CHUNKS)
    assert ("K5", "K8") in cap(canh)  # chỉ nhờ tên khác "ước lượng"; tên chính "ước lượng điểm" không có trong cửa sổ K8
    assert not xuat_hien("Ước lượng điểm", C4)


def test_b2_cau_trich_va_chunk_cua_canh():
    canh = {(c["source"], c["target"]): c for c in canh_b2(hd_b2(), CHUNKS)}
    # câu đầu tiên trong cửa sổ của K2 có tên "tổng thể" (K1) là câu thứ nhất của chunk c1
    assert canh[("K1", "K2")]["quote"] == "Tổng thể là tập hợp các phần tử."
    assert canh[("K1", "K2")]["chunk_ids"] == ["c1"]
    assert canh[("K5", "K8")]["quote"] == C4


def test_b2_chunk_cau_neo_thieu_la_loi():
    with pytest.raises(ValueError, match="K1"):
        canh_b2(hd_b2(), [c for c in CHUNKS if c["chunk_id"] != "c1"])


def test_b2_ten_ngan_khong_bi_loc():
    # baseline đơn giản đúng như mô tả: tên một âm tiết vẫn khớp, không có danh sách tên chung
    assert ("K2", "K3") in cap(canh_b2(hd_b2(), CHUNKS))


# ---------- B3 ----------

def tieu_de(ma, chu, cap_, trang):
    return {"ma": ma, "chu": chu, "cap": cap_, "cha": None, "trang": trang, "ma_dong": None}


TIEU_DE = [
    tieu_de("s0", "Giáo trình Xác suất", 0, None),
    tieu_de("s1", "Chương 2. Ước lượng tham số", 1, 5),
    tieu_de("s2", "2.1 Các khái niệm cơ bản", 2, 5),
    tieu_de("s3", "2.1.1. Tổng thể và mẫu", 3, 6),
    tieu_de("s4", "Bài tập", 2, 9),
    tieu_de("s5", "1) Phương pháp", 2, None),
    tieu_de("s6", "Phần mở đầu", 1, 1),
    tieu_de("s7", "A. Phụ lục", 1, 12),
    tieu_de("s8", "95% khoảng tin cậy", 2, 7),
    tieu_de("s9", "3", 1, 13),
]


def hd_b3(tieu=TIEU_DE):
    hd = dt.hop_dong([dt.khai_niem("N1")], [], ["N1"])
    hd["cau_truc"] = {"tieu_de": copy.deepcopy(tieu), "muc": [], "doan_van": []}
    return hd


def test_b3_bo_so_muc_tinh_tay():
    ky_vong = {"Chương 2. Ước lượng tham số": "Ước lượng tham số", "2.1 Các khái niệm cơ bản": "Các khái niệm cơ bản",
               "2.1.1. Tổng thể và mẫu": "Tổng thể và mẫu", "Bài tập": "Bài tập", "1) Phương pháp": "Phương pháp",
               "Phần mở đầu": "Phần mở đầu", "A. Phụ lục": "Phụ lục", "95% khoảng tin cậy": "95% khoảng tin cậy",
               "3": "3", "Chương 3: Xác suất": "Xác suất", "II. Giới thiệu": "Giới thiệu"}
    assert {chu: bo_so_muc(chu) for chu in ky_vong} == ky_vong


def test_b3_moi_tieu_de_tu_cap_1_la_mot_khai_niem_theo_thu_tu_sach():
    hd = hop_dong_b3(hd_b3())
    assert kiem(hd) == []
    assert [k["ten"] for k in hd["khai_niem"]] == [
        "Ước lượng tham số", "Các khái niệm cơ bản", "Tổng thể và mẫu", "Bài tập", "Phương pháp", "Phần mở đầu", "Phụ lục",
        "95% khoảng tin cậy", "3"]
    assert [k["ma"] for k in hd["khai_niem"]][:2] == ["b3-s1", "b3-s2"]  # tiêu đề gốc cấp 0 (s0) không phải khái niệm
    assert hd["lo_trinh"]["day_hoc"] == [k["ma"] for k in hd["khai_niem"]]
    assert [k["vi_tri"] for k in hd["khai_niem"]] == list(range(9))


def test_b3_hop_dong_baseline_khong_canh_cau_neo_la_dong_tieu_de():
    hd = hop_dong_b3(hd_b3())
    assert hd["canh"] == [] and hd["cau_truc"] is None and hd["cap_ung_vien"] is None
    assert hd["dinh_danh"]["he"] == "b3" and hd["dinh_danh"]["doc_id"] == "S"
    k = hd["khai_niem"][0]
    assert k["cau_neo"] == {"trang": 5, "cau": "Chương 2. Ước lượng tham số", "ma_chunk": ""}
    assert k["trang_thai_day"] == "taught" and k["kieu"] == "tieu_de"
    assert hd["chi_phi"]["tong"]["usd"] == 0.0


def test_b3_khong_loc_theo_vai_tro_vung():
    # B3 không có A2: tiêu đề "Bài tập" vẫn là khái niệm dù hệ chính gán vai trò bai_tap
    tieu = copy.deepcopy(TIEU_DE)
    hd = hd_b3(tieu)
    hd["cau_truc"]["muc"] = [{"ma": "s4", "vai_tro": "bai_tap"}]
    assert "Bài tập" in [k["ten"] for k in hop_dong_b3(hd)["khai_niem"]]


def test_b3_thieu_cau_truc_la_loi():
    hd = hd_b3()
    hd["cau_truc"] = None
    with pytest.raises(ValueError, match="cau_truc"):
        hop_dong_b3(hd)


# ---------- B4 ----------

def ung_vien(ma, ten, *, thu_tu, alias=(), learnable=True, quote=None, chunk="c1"):
    return {"candidate_id": ma, "name": ten, "aliases": list(alias), "node_type": "concept", "learnable": learnable,
            "first_order_index": thu_tu, "evidence": [{"chunk_id": chunk, "quote": quote or f"câu về {ten}"}]}


UNG_VIEN = [
    ung_vien("u1", "Mẫu", thu_tu=3, quote="Mẫu là một phần của tổng thể."),
    ung_vien("u2", "  mẫu. ", thu_tu=7, alias=["tập mẫu"]),
    ung_vien("u3", "Mẫu ngẫu nhiên", thu_tu=5),
    ung_vien("u4", "Tổng thể", thu_tu=1, alias=[{"name": "Mẫu"}, {"name": "quần thể"}], chunk="c0"),
    ung_vien("u5", "Kỳ vọng", thu_tu=9),
    ung_vien("u6", "Kì vọng", thu_tu=11),
    ung_vien("u7", "Hình 1", thu_tu=2, learnable=False),
    ung_vien("u8", "Phương sai", thu_tu=8),
    ung_vien("u9", "Phương sai.", thu_tu=4, alias=["độ phân tán"]),
]
TRANG = {"c0": 1, "c1": 2}


def test_b4_gop_chi_khi_trung_ten_sau_chuan_hoa_tinh_tay():
    hd = hop_dong_b4(dt.hop_dong([dt.khai_niem("N1")], [], ["N1"]), UNG_VIEN, TRANG)
    assert kiem(hd) == []
    # Nhóm theo tên chuẩn hoá: {u4}, {u8,u9} (phương sai), {u1,u2} (mẫu), {u3}, {u5}, {u6}; u7 không learnable.
    # Thứ tự theo first_order_index nhỏ nhất của nhóm: u4(1), u9(4), u1(3) -> 1,3,4: Tổng thể, Mẫu, Phương sai; rồi u3(5), u5(9), u6(11).
    assert [k["ten"] for k in hd["khai_niem"]] == ["Tổng thể", "Mẫu", "Phương sai", "Mẫu ngẫu nhiên", "Kỳ vọng", "Kì vọng"]
    theo_ten = {k["ten"]: k for k in hd["khai_niem"]}
    assert theo_ten["Mẫu"]["ung_vien_goc"] == ["u1", "u2"]
    assert theo_ten["Phương sai"]["ung_vien_goc"] == ["u8", "u9"]  # đầu nhóm = ứng viên đứng trước theo thứ tự đầu vào
    assert theo_ten["Phương sai"]["ten_khac"] == ["Phương sai.", "độ phân tán"]


def test_b4_khong_gop_theo_alias_hay_gan_giong():
    hd = hop_dong_b4(dt.hop_dong([dt.khai_niem("N1")], [], ["N1"]), UNG_VIEN, TRANG)
    ten = [k["ten"] for k in hd["khai_niem"]]
    assert "Kỳ vọng" in ten and "Kì vọng" in ten  # gần giống nhưng khác tên: không gộp
    assert "Mẫu ngẫu nhiên" in ten and ten.count("Mẫu") == 1
    tong_the = next(k for k in hd["khai_niem"] if k["ten"] == "Tổng thể")
    assert tong_the["ung_vien_goc"] == ["u4"]  # alias "Mẫu" của u4 không kéo nó vào nhóm Mẫu
    assert tong_the["ten_khac"] == ["Mẫu", "quần thể"]


def test_b4_ten_khac_cau_neo_va_loai_ung_vien_khong_learnable():
    hd = hop_dong_b4(dt.hop_dong([dt.khai_niem("N1")], [], ["N1"]), UNG_VIEN, TRANG)
    mau = next(k for k in hd["khai_niem"] if k["ten"] == "Mẫu")
    assert mau["ten_khac"] == ["  mẫu. ", "tập mẫu"]  # tên thô của ứng viên gộp vào, giữ nguyên chữ
    assert mau["cau_neo"] == {"trang": 2, "cau": "Mẫu là một phần của tổng thể.", "ma_chunk": "c1"}
    assert "Hình 1" not in [k["ten"] for k in hd["khai_niem"]]
    assert hd["canh"] == [] and hd["dinh_danh"]["he"] == "b4"


def test_b4_khai_niem_khong_co_bang_chung_co_cau_neo_null():
    u = ung_vien("u1", "Mẫu", thu_tu=1)
    u["evidence"] = []
    hd = hop_dong_b4(dt.hop_dong([dt.khai_niem("N1")], [], ["N1"]), [u], TRANG)
    assert hd["khai_niem"][0]["cau_neo"] is None and kiem(hd) == []


def test_baseline_khong_nhap_pipeline():
    import ast
    from pathlib import Path
    thu_muc = Path(__file__).resolve().parents[2] / "evaluation" / "danhgia" / "xuat" / "baseline"
    tep = sorted(thu_muc.glob("*.py"))
    assert {p.name for p in tep} >= {"b2.py", "b3.py", "b4.py", "chung.py", "lenh.py"}
    for p in tep:
        for nut in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            ten = [x.name for x in nut.names] if isinstance(nut, ast.Import) else \
                [nut.module or ""] if isinstance(nut, ast.ImportFrom) and nut.level == 0 else []
            assert not any(t.split(".")[0] == "doc2roadmap" for t in ten), f"{p.name}: {ten}"
