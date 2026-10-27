from tests.evaluation.ho_tro import nfd

from danhgia.ten import am_tiet, chuan_hoa, do_giong, xuat_hien


def test_chuan_hoa_nfc_chu_thuong_khoang_trang_dau_cau():
    assert chuan_hoa("  Quy   LUẬT,\n") == "quy luật"
    assert chuan_hoa(nfd("Tỷ lệ")) == "tỷ lệ"  # NFD vào, NFC ra
    assert chuan_hoa("«Kỳ vọng»") == "kỳ vọng"
    assert chuan_hoa("P(A|B)") == "p(a|b)"  # dấu câu bên trong giữ nguyên


def test_chi_so_tren_duoi_va_ky_tu_tuong_thich_ve_dang_thuong():
    # Gán thử xstk 27/10: hai người ghi "Phân phối χ²" và "Phân phối χ2"; NFC để hai tên lệch nhau.
    assert chuan_hoa("Phân phối χ²") == chuan_hoa("Phân phối χ2") == "phân phối χ2"
    assert am_tiet("x₁ và x₂") == am_tiet("x1 và x2")
    assert chuan_hoa("µ") == chuan_hoa("μ")  # dấu micro và chữ mu Hy Lạp
    assert chuan_hoa("ﬁ") == "fi"  # chữ ghép từ phông PDF


def test_giu_dau_tieng_viet():
    assert chuan_hoa("hàm") != chuan_hoa("ham")
    assert am_tiet("Hàm số") != am_tiet("Ham so")


def test_am_tiet_tach_theo_khoang_trang_va_dau_noi():
    assert am_tiet("Quy luật_số lớn") == ("quy", "luật", "số", "lớn")
    assert am_tiet(nfd("Tỷ lệ")) == ("tỷ", "lệ")


def test_xuat_hien_theo_ranh_gioi_am_tiet_khong_theo_chuoi_con():
    assert xuat_hien("tâm lý", "Ngành tâm lý học nghiên cứu hành vi")
    assert not xuat_hien("hi", "chi tiết")  # "hi" là chuỗi con của "chi" nhưng không phải âm tiết
    assert not xuat_hien("suất", "xác suất có điều kiện") is False  # suất là một âm tiết riêng
    assert not xuat_hien("xác suất", "xác định suất")  # phải liền kề


def test_ten_co_am_tiet_tan_cung_y_khop_giua_cau_va_voi_chinh_no():
    for ten in ["quy luật", "tỷ lệ", "lý thuyết", "mức ý nghĩa", "chủ nghĩa duy vật", "không suy biến"]:
        assert xuat_hien(ten, f"Theo {ten.upper()} này, ta suy ra kết quả.")
        assert xuat_hien(nfd(ten), f"Theo {ten} này")  # NFD và NFC như nhau
        assert xuat_hien(ten, ten)
    # câu in hoa đầu câu, tên nằm giữa
    assert xuat_hien("quy luật", "Theo Quy Luật số lớn, trung bình hội tụ.")
    # y và i là hai âm tiết khác nhau, không được gộp
    assert not xuat_hien("quy luật", "qui luật")


def test_do_giong_tren_cung_phep_bien_doi():
    assert do_giong("Xác suất  có điều kiện.", nfd("xác suất có điều kiện")) == 1.0
    assert do_giong("abc def", "xyz uvw") < 0.5
