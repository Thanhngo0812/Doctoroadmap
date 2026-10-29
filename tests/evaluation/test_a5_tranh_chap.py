"""DG-18a: khái niệm vàng có `trang_thai = null` (tranh chấp sau hội ý) ra khỏi hai mẫu số A5 và được đếm riêng (giao thức mục 10)."""
from tests.evaluation import dung_tay as dt
from tests.evaluation.test_thuoc_khai_niem import MA, cham, g3_, hd_, nd, so, tu_mau, vang


def the_gioi():
    # G1 tranh chấp (null), được máy căn khop với node taught; G2 dạy ở đây, node taught (đúng); G3 ở chương c2, tranh chấp, không có node
    g3 = g3_(vang("G1", "c1", None), vang("G2", "c1", "day_o_day"), vang("G3", "c2", None))
    hd = hd_([nd("n1", status="taught"), nd("n2", status="taught")])
    can = dt.can(MA, [("G1", "n1", "khop"), ("G2", "n2", "khop")])
    return cham(hd, g3, can)


def test_khai_niem_tranh_chap_khong_vao_hai_mau_so_a5():
    rows = the_gioi()
    assert tu_mau(rows, "a5.trang_thai_chinh_xac.nghiem") == (1, 1)     # chỉ G2; trước sửa là (1, 2): G1 bị tính là máy sai
    assert tu_mau(rows, "a5.trang_thai_phu.nghiem") == (1, 1)           # chỉ G2 có đáp án để so


def test_khai_niem_tranh_chap_duoc_dem_rieng_theo_chuong():
    rows = the_gioi()
    assert so(rows, "a5.trang_thai_vang_tranh_chap.nghiem", "c1")["gia_tri"] == 1
    assert so(rows, "a5.trang_thai_vang_tranh_chap.nghiem", "c2")["gia_tri"] == 1    # đếm mọi khái niệm tranh chấp của chương, kể cả chưa căn
    assert so(rows, "a5.trang_thai_vang_tranh_chap.noi", "c1")["gia_tri"] == 1


def test_khai_niem_tranh_chap_van_la_node_o_cac_thuoc_khac():
    rows = the_gioi()
    # A3 chỉ tính day_o_day và day_qua_vi_du: G1, G3 tranh chấp không vào mẫu số, G2 có node
    assert tu_mau(rows, "a3.do_phu.nghiem") == (1, 1)
    # A4 và câu neo vẫn thấy node n1 căn G1 (vẫn là node khi căn)
    assert tu_mau(rows, "a4.ti_le_tach.nghiem")[1] == 2
