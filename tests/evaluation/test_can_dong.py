"""DG-13: căn dòng của bảng dòng `src` với mục của hệ chính (cau_truc.ma_dong, dong_thuoc_muc, dong_khong_can) và M3 trên hợp đồng."""
import copy
import json
import shutil
from pathlib import Path

import pytest

from danhgia.cham import a1a2, dong
from danhgia.hop_dong import kiem
from danhgia.xuat import xuat
from danhgia.xuat.can_dong import can_dong
from tests.evaluation import dung_tay as dt
from tests.evaluation.test_xuat import DINH_DANH, DOC, KHO, PHIEN_BAN

MA = "S"


def nut(thu_tu, loai, text, trang, bbox):
    return {"reading_order": thu_tu, "node_type": loai, "text": text, "page": trang, "bbox": bbox}


def dong_(ma, trang, bbox, text="x"):
    return {"id": ma, "trang": trang, "text": text, "bbox": bbox}


def muc(sid, cap, tieu_de, thu_tu):
    return {"section_id": sid, "level": cap, "title": tieu_de, "order_index": thu_tu, "parent_section_id": None, "role": "noi_dung"}


NUT = [nut(0, "section_header", "CHUONG 1", 1, [10, 700, 200, 680]),
       nut(1, "text", "Noi dung chuong.", 1, [10, 670, 200, 650]),
       nut(2, "section_header", "1.1 Muc", 1, [10, 640, 200, 620]),
       nut(3, "section_header", "• tieu de gia", 1, [10, 610, 200, 590]),      # nút tiêu đề nhưng chunker loại: không có mục
       nut(4, "section_header", "Phan A", 2, [10, 700, 100, 680]),
       nut(5, "section_header", "Phan B", 2, [10, 670, 100, 650])]               # "Phan A" + "Phan B" là một tiêu đề mục ghép hai nút
MUC = [muc("root", 0, "<document>", 0), muc("s1", 1, "CHUONG 1", 1), muc("s2", 2, "1.1 Muc", 2), muc("s3", 1, "Phan A Phan B", 3)]
BANG = [dong_("p0001-l001", 1, [10, 700, 200, 680]), dong_("p0001-l002", 1, [10, 670, 200, 650]),
        dong_("p0001-l003", 1, [10, 640, 200, 620]), dong_("p0001-l004", 1, [10, 610, 200, 590]),
        dong_("p0001-l005", 1, [300, 400, 400, 380]),                               # không nút nào phủ: không căn được
        dong_("p0002-l001", 2, [10, 700, 100, 680]), dong_("p0002-l002", 2, [10, 670, 100, 650])]


def test_can_dong_theo_bbox_va_nhan_tieu_de_chap_nhan_ke_ca_tieu_de_ghep():
    kq = can_dong(NUT, MUC, BANG)
    assert kq["ma_dong"] == {"s1": ["p0001-l001"], "s2": ["p0001-l003"], "s3": ["p0002-l001", "p0002-l002"]}
    # lá: dòng của tiêu đề là chính mục đó; nội dung và tiêu đề giả thuộc mục chấp nhận gần nhất đứng trước
    assert kq["dong_thuoc_muc"] == {"p0001-l001": "s1", "p0001-l002": "s1", "p0001-l003": "s2", "p0001-l004": "s2",
                                    "p0002-l001": "s3", "p0002-l002": "s3"}
    assert kq["dong_khong_can"] == ["p0001-l005"]                                  # đếm riêng, không bị bỏ lặng lẽ
    assert kq["thong_ke"]["so_dong_can"] == 6 and kq["thong_ke"]["so_dong_khong_can"] == 1
    assert kq["thong_ke"]["so_muc_nhan_duoc_tieu_de"] == 3


def test_dong_truoc_tieu_de_dau_tien_co_la_goc():
    nut_ = [nut(0, "text", "Bia sach", 1, [10, 760, 200, 740])] + [dict(n, reading_order=n["reading_order"] + 1) for n in NUT[:3]]
    bang = [dong_("p0001-l000", 1, [10, 760, 200, 740])] + BANG[:3]
    kq = can_dong(nut_, MUC, bang)
    assert kq["dong_thuoc_muc"]["p0001-l000"] is None and kq["dong_thuoc_muc"]["p0001-l001"] == "s1"


def test_dong_phai_phu_it_nhat_nua_dien_tich_nut_moi_duoc_can():
    nua = dong_("p0001-l009", 1, [10, 700, 200, 690])     # phủ 1/2 chiều cao nút CHUONG 1 nhưng là cả dòng: chồng 100% diện tích dòng
    ngoai = dong_("p0001-l010", 1, [10, 710, 200, 690])   # dòng cao gấp đôi nút, chồng đúng 50%: vẫn đạt
    xa = dong_("p0001-l011", 1, [10, 720, 200, 685])      # chồng < 50%: không căn
    kq = can_dong(NUT[:1], MUC[:2], [nua, ngoai, xa])
    assert set(kq["dong_thuoc_muc"]) == {"p0001-l009", "p0001-l010"} and kq["dong_khong_can"] == ["p0001-l011"]


# ---------------------------------------------------------------- hợp đồng


def hop_dong_voi_can_dong(cd):
    hd = dt.hop_dong([dt.khai_niem("a")], [], ["a"])
    hd["cau_truc"] = {"tieu_de": [{"ma": m["section_id"], "chu": m["title"], "cap": m["level"], "cha": None, "trang": 1,
                                   "ma_dong": cd["ma_dong"].get(m["section_id"])} for m in MUC if m["level"] > 0],
                      "muc": [{"ma": m["section_id"], "vai_tro": "noi_dung"} for m in MUC if m["level"] > 0], "doan_van": [],
                      "dong_thuoc_muc": cd["dong_thuoc_muc"], "dong_khong_can": cd["dong_khong_can"]}
    return hd


def test_hop_dong_moi_qua_validator_va_hop_dong_cu_van_hop_le():
    hd = hop_dong_voi_can_dong(can_dong(NUT, MUC, BANG))
    assert kiem(hd) == []
    cu = copy.deepcopy(hd)
    for t in cu["cau_truc"]["tieu_de"]:
        t["ma_dong"] = None
    del cu["cau_truc"]["dong_thuoc_muc"], cu["cau_truc"]["dong_khong_can"]
    assert kiem(cu) == []                                                            # B5 và baseline không có hai trường vẫn hợp lệ
    xau = copy.deepcopy(hd)
    xau["cau_truc"]["tieu_de"][0]["ma_dong"] = "p0001-l001"                          # chuỗi đơn không còn hợp lệ
    xau["cau_truc"]["dong_khong_can"] = [1]
    assert len(kiem(xau)) >= 2


def test_m3_tren_hop_dong_bang_dung_m3_khi_dua_du_doan_dong_truc_tiep():
    cd = can_dong(NUT, MUC, BANG)
    hd = hop_dong_voi_can_dong(cd)
    vang = [{"sach": "S", "id": "h1", "dong": ["p0001-l001"], "text": "CHUONG 1", "cap": 1, "cha": None, "vung": "noi_dung", "vai_tro": "noi_dung", "ghi_chu": ""},
            {"sach": "S", "id": "h2", "dong": ["p0001-l003"], "text": "1.1 Muc", "cap": 2, "cha": "h1", "vung": None, "vai_tro": "noi_dung", "ghi_chu": ""}]
    qua_hd = a1a2.cham(vang, a1a2.du_doan_tu_hop_dong(hd, BANG), BANG, he="chinh", ma_sach=MA)
    truc_tiep = {"headings": [{"id": "s1", "dong": ["p0001-l001"], "cap": 1, "cha": None, "text": "CHUONG 1", "vai_tro": "noi_dung"},
                              {"id": "s2", "dong": ["p0001-l003"], "cap": 2, "cha": "s1", "text": "1.1 Muc", "vai_tro": "noi_dung"},
                              {"id": "s3", "dong": ["p0002-l001", "p0002-l002"], "cap": 1, "cha": None, "text": "Phan", "vai_tro": "noi_dung"}],
                 "lines": {"p0001-l001": {"leaf": "s1"}, "p0001-l002": {"leaf": "s1"}, "p0001-l003": {"leaf": "s2"},
                           "p0001-l004": {"leaf": "s2"}, "p0002-l001": {"leaf": "s3"}, "p0002-l002": {"leaf": "s3"}},
                 "evaluation_excluded": []}
    tt = a1a2.cham(vang, truc_tiep, BANG, he="chinh", ma_sach=MA)
    lay = lambda rows, t: [(r.get("tu"), r.get("mau")) for r in rows if r["thuoc"] == t]  # noqa: E731
    assert lay(qua_hd, "a1.m3") == lay(tt, "a1.m3") and lay(qua_hd, "a1.m3")[0][1] > 0
    assert [r["gia_tri"] for r in qua_hd if r["thuoc"] == "a1.m3_dong_thieu_trong_du_doan"] == [1]    # p0001-l005 không căn được
    # dòng không căn được nằm trong mẫu số của M3 (không bị bỏ), và tính là sai
    assert lay(qua_hd, "a1.m3")[0][1] == sum(len(d["text"]) for d in BANG)


# ---------------------------------------------------------------- bộ xuất đầu cuối trên kho fixture


def kho_co_cay(tmp_path):
    kho = tmp_path / "kho"
    shutil.copytree(KHO, kho)
    chunks = kho / "chunks" / DOC / "v7"
    muc_ = json.loads((chunks / "sections.json").read_text(encoding="utf-8"))
    (chunks / "manifest.json").write_text(json.dumps({"parse_version": "2"}), encoding="utf-8")
    nut_, bang = [], []
    for i, m in enumerate(sorted((m for m in muc_ if m["level"] > 0), key=lambda m: m.get("order_index", 0))):
        bbox = [10, 700 - 30 * i, 300, 680 - 30 * i]
        nut_.append(nut(i, "section_header", m["title"], 1, bbox))
        bang.append(dong_(f"p0001-l{i + 1:03d}", 1, bbox, m["title"]))
    bang.append(dong_("p0001-l900", 1, [400, 10, 450, 5]))
    cay = kho / "parse_tree" / DOC / "v2"
    cay.mkdir(parents=True)
    (cay / "tree.json").write_text(json.dumps({"nodes": nut_}), encoding="utf-8")
    return kho, [m for m in muc_ if m["level"] > 0], bang


def test_xuat_voi_bang_dong_ghi_ma_dong_va_dong_thuoc_muc_va_qua_validator(tmp_path):
    kho, muc_, bang = kho_co_cay(tmp_path)
    hd = xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH, bang_dong=bang)
    ct = hd["cau_truc"]
    goc = [t for t in ct["tieu_de"] if t["cap"] == 0]
    assert len(goc) == 1 and goc[0]["ma_dong"] == []                                     # gốc tài liệu không có dòng
    assert all(len(t["ma_dong"]) == 1 for t in ct["tieu_de"] if t["cap"] != 0) and len(ct["tieu_de"]) == len(muc_) + 1
    assert [t["id"] for t in a1a2.du_doan_tu_hop_dong(hd, [dong_(x, 1, [0, 0, 0, 0]) for x in ct["dong_thuoc_muc"]])["headings"]] == [t["ma"] for t in ct["tieu_de"] if t["cap"] != 0]
    assert ct["dong_khong_can"] == ["p0001-l900"] and len(ct["dong_thuoc_muc"]) == len(muc_)
    assert all(ct["dong_thuoc_muc"][t["ma_dong"][0]] == t["ma"] for t in ct["tieu_de"] if t["cap"] != 0)
    assert kiem(hd) == []
    khong = xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)                              # không bảng dòng: như cũ
    assert all(t["ma_dong"] is None for t in khong["cau_truc"]["tieu_de"]) and "dong_thuoc_muc" not in khong["cau_truc"]
