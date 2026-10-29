"""Vé DG-17: cổng allowlist trên mọi lệnh con của `python -m danhgia`.

Mỗi lệnh con (cả năm lệnh khai báo thẳng trong `_tham_so` lẫn mọi mục của `_LENH`) phải thuộc đúng một trong ba danh sách dưới đây. Lệnh mới thêm sau này mà
chưa được phân loại thì `test_moi_lenh_con_deu_duoc_phan_loai` đỏ.

- `DA_KIEM_BI_MAT`: có test cài chuỗi bí mật giả vào trường lồng, tên khái niệm và câu, chạy lệnh và thấy chuỗi không ra stdout, stderr, hay tệp ra.
  Giá trị là tên test chứa bằng chứng; `test_diem_toi_test_bi_mat_ton_tai` kiểm tên đó có thật.
- `KHONG_NHAN_DU_LIEU_TAP_THU`: không nhận dữ liệu tập thử, kèm một dòng lý do.
- `CHUA_KIEM_BI_MAT`: **nợ đã khai báo**: lệnh nhận dữ liệu có tên khái niệm hay câu, chưa có test bí mật riêng. Danh sách này phải ngắn dần; lý do ghi lệnh in gì.
"""
import importlib
import json

import pytest

from danhgia import __main__ as cli
from danhgia.__main__ import main
from danhgia.bao_cao import cong
from tests.evaluation import bang_hinh_ho_tro as H
from tests.evaluation import test_cham_a1a2 as a1a2_t
from tests.evaluation import test_datasheet as ds_t
from tests.evaluation import test_quy_loi as ql_t
from tests.evaluation import test_thuoc_khai_niem as tkn_t

SECRET = "BI-MAT-GIA-KHAI-NIEM-XYZ"

DA_KIEM_BI_MAT = {
    "quy-loi": "tests.evaluation.test_quy_loi:test_cli_tap_thu_chi_in_so_khong_in_ten_khai_niem",
    "bang-hinh": "tests.evaluation.test_cong_allowlist:test_bang_hinh_tap_thu_khong_lo_bi_mat",
    "datasheet": "tests.evaluation.test_datasheet:test_man_hinh_va_tep_khong_lo_chuoi_bi_mat_tren_tap_thu",
    "thuoc-khai-niem": "tests.evaluation.test_cong_allowlist:test_thuoc_khai_niem_khong_lo_bi_mat",
    "cham-a1a2": "tests.evaluation.test_cong_allowlist:test_cham_a1a2_khong_lo_bi_mat",
    "cham": "tests.evaluation.test_cong_allowlist:test_cham_khong_lo_bi_mat",
    "kiem": "tests.evaluation.test_cong_allowlist:test_kiem_khong_lo_bi_mat",
}
KHONG_NHAN_DU_LIEU_TAP_THU = {}
CHUA_KIEM_BI_MAT = {
    "xuat": "đọc kho artifact của hệ; in số khái niệm, số cạnh, số dòng căn được (f-string với len); cần kho dựng sẵn để cài chuỗi bí mật",
    "chuyen-vang": "đọc kho và vàng A8 cũ; in `json.dumps(bao_cao)` của bộ chuyển, chưa kiểm khoá nào trong đó",
    "doi-chieu": "đọc kho và vàng cũ; in bảng đối chiếu và `ghi_chu` dạng json, chưa kiểm nội dung",
    "phieu-g3": "đọc phiếu G3 của sinh viên; in số đếm nhưng cũng in `LỖI <e>` và `CẢNH BÁO` do validator sinh, có thể kèm nội dung ô",
    "phieu-g4": "đọc phiếu G4 của sinh viên; như phieu-g3: in `LỖI <e>` và `CẢNH BÁO` của validator",
    "can-khai-niem": "đọc vàng G3, G4 và hợp đồng; in số đếm, `LỖI <x>` và json đồng thuận",
    "phieu-g5": "đọc phiếu G5 đã phán; in số precision, đối chứng và `LỖI <x>` của validator",
    "b5": "chạy baseline mô hình đọc thẳng; in json báo cáo dry-run và thông báo lỗi manifest/PDF",
    "baseline": "đọc kho và hợp đồng hệ chính; in số khái niệm, số cạnh (f-string với len)",
    "phat-lai": "đọc kho; in json kết quả kiểm `khong-doi` và số đếm oracle",
    "g1g2": "đọc gói G1/G2 (tiêu đề sách); in số dòng, `LỖI <x>` của validator và json đồng thuận",
    "luot": "điều phối lượt chạy; in dòng kiểm lượt (`--kiem`) và thông báo từ chối, kèm đường dẫn",
}


def cac_lenh_con():
    goc = cli._tham_so()
    (hanh_dong,) = [a for a in goc._actions if a.__class__.__name__ == "_SubParsersAction"]
    return set(hanh_dong.choices)


@pytest.fixture
def gom(capsys):
    """Chạy lệnh, trả toàn bộ chữ ra màn hình (stdout, stderr và thông điệp thoát)."""
    def chay(argv):
        thoat = ""
        try:
            main(argv)
        except SystemExit as e:
            thoat = str(e.code)
        ra = capsys.readouterr()
        return ra.out + ra.err + thoat
    return chay


# ------------------------------------------------------------------------------------------------ phân loại


def test_moi_lenh_con_deu_duoc_phan_loai():
    lenh = cac_lenh_con()
    assert set(cli._LENH) <= lenh and {"xuat", "kiem", "chuyen-vang", "cham", "doi-chieu"} <= lenh
    ba = (set(DA_KIEM_BI_MAT), set(KHONG_NHAN_DU_LIEU_TAP_THU), set(CHUA_KIEM_BI_MAT))
    assert not (ba[0] & ba[1]) and not (ba[0] & ba[2]) and not (ba[1] & ba[2]), "một lệnh chỉ thuộc một danh sách"
    chua = lenh - set().union(*ba)
    assert not chua, f"lệnh chưa phân loại: {sorted(chua)}"
    thua = set().union(*ba) - lenh
    assert not thua, f"danh sách nhắc tới lệnh không còn: {sorted(thua)}"
    for ten, ly_do in (*KHONG_NHAN_DU_LIEU_TAP_THU.items(), *CHUA_KIEM_BI_MAT.items()):
        assert len(ly_do) >= 20, f"{ten}: thiếu lý do"


def test_lenh_moi_chua_phan_loai_lam_cong_do(monkeypatch):
    """Bảng phá: thêm một lệnh vào `_LENH` mà chưa phân loại thì phép kiểm trên phải đỏ."""
    class Gia:
        @staticmethod
        def them_lenh(parser):
            parser.set_defaults(chay=lambda a: 0)
    monkeypatch.setitem(cli._LENH, "lenh-moi-chua-phan-loai", "tests.evaluation.test_cong_allowlist")
    monkeypatch.setattr(importlib.import_module("tests.evaluation.test_cong_allowlist"), "them_lenh", Gia.them_lenh, raising=False)
    with pytest.raises(AssertionError, match="lenh-moi-chua-phan-loai"):
        test_moi_lenh_con_deu_duoc_phan_loai()


def test_diem_toi_test_bi_mat_ton_tai():
    for lenh, diem in DA_KIEM_BI_MAT.items():
        mo_dun, _, ten = diem.partition(":")
        assert callable(getattr(importlib.import_module(mo_dun), ten, None)), f"{lenh}: không có test {diem}"


# ------------------------------------------------------------------------------------------------ test bí mật


def _ro_ri_khi_in_ngay_tho(gom, monkeypatch, mo_dun, argv, text_chua_bi_mat):
    """Bằng chứng đỏ: mô-đun lệnh in kèm nguyên văn đầu vào (bản in ngây thơ) thì cùng phép kiểm bắt được chuỗi bí mật."""
    mo = importlib.import_module(mo_dun)
    in_goc = print
    monkeypatch.setattr(mo, "print", lambda *a, **k: in_goc(*a, text_chua_bi_mat, **k), raising=False)
    return SECRET in gom(argv)


def _bi_mat_vao_tep(*tep):
    for t in tep:
        assert SECRET in open(t, encoding="utf-8").read(), f"{t} phải chứa chuỗi bí mật (trường lồng, tên khái niệm hay câu)"


def test_cong_in_ngay_tho_lo_con_cong_thi_khong(capsys):
    du_lieu = {"tap_thu": True, "ten": {"long": SECRET}}
    print(du_lieu)                                                            # bản in ngây thơ: lộ
    assert SECRET in capsys.readouterr().out
    with pytest.raises(ValueError):
        cong.in_allowlist(du_lieu, ("tap_thu", "ten"))
    assert SECRET not in capsys.readouterr().out


def test_bang_hinh_tap_thu_khong_lo_bi_mat(tmp_path, monkeypatch, gom):
    argv = H.dung_thu_muc(tmp_path, tap="thu", them_manifest={"stats": {"long": {"khai_niem": {SECRET: 1}}, "cau": SECRET}}) + [
        "--so-vong", "50", "--ra", str(tmp_path / "ra")]
    _bi_mat_vao_tep(tmp_path / "m-A.json", tmp_path / "hd-chinh-A.json")
    text = gom(argv)
    assert SECRET not in text and "tap_thu true" in text
    for tep in (tmp_path / "ra").iterdir():
        assert SECRET not in tep.read_text(encoding="utf-8"), tep.name
    # đỏ trên bản in ngây thơ: thay cổng bằng in nguyên manifest
    moi = importlib.import_module("danhgia.bao_cao.lenh_bang_hinh")
    manifest_text = (tmp_path / "m-A.json").read_text(encoding="utf-8")
    monkeypatch.setattr(moi.cong, "in_allowlist", lambda du_lieu, cho_phep, **k: print(manifest_text))
    assert SECRET in gom(argv)


def test_thuoc_khai_niem_khong_lo_bi_mat(tmp_path, monkeypatch, gom):
    hd = tkn_t.truy_nguyen_fixture()
    for k in hd["khai_niem"]:
        k["ten"], k["ten_khac"] = f"{SECRET}-{k['ma']}", [SECRET]
        if k["cau_neo"]:
            k["cau_neo"]["ghi_chu_long"] = {"sau": SECRET}
    g3 = tkn_t.g3_(tkn_t.vang("G1", "c1", trang=1, cau="Cao độ là độ cao thấp của âm thanh.", ten=SECRET))
    g3["ghi_chu_long"] = {"sau": SECRET}
    tep = {"hd": hd, "g3": g3, "g4": tkn_t.dt.g4(tkn_t.MA, []), "can": tkn_t.dt.can(tkn_t.MA, [("G1", "t1", "khop")]), "ax": tkn_t.ANH_XA, "vb": tkn_t.TRANG}
    argv = ["thuoc-khai-niem", *sum(([f"--{k}", H.ghi_json(tmp_path / f"{n}.json", tep[n])] for k, n in
                                    (("hop-dong", "hd"), ("g3", "g3"), ("g4", "g4"), ("can", "can"), ("anh-xa", "ax"), ("van-ban", "vb"))), []),
            "--ra", str(tmp_path / "bang.json")]
    _bi_mat_vao_tep(tmp_path / "hd.json", tmp_path / "g3.json")
    text = gom(argv)
    assert "a3.do_phu.nghiem" in text and SECRET not in text
    assert SECRET not in (tmp_path / "bang.json").read_text(encoding="utf-8")
    assert _ro_ri_khi_in_ngay_tho(gom, monkeypatch, "danhgia.cham.lenh_khai_niem", argv, (tmp_path / "g3.json").read_text(encoding="utf-8"))


def test_cham_a1a2_khong_lo_bi_mat(tmp_path, monkeypatch, gom):
    vang = [{**h, "text": f"{SECRET} {h['text']}"} for h in a1a2_t.VANG]
    du_doan = {**a1a2_t.DU_DOAN, "headings": [{**h, "text": f"{SECRET} {h['text']}"} for h in a1a2_t.DU_DOAN["headings"]]}
    bang = [{**d, "text": f"{SECRET} {d['text']}"} for d in a1a2_t.BANG]
    argv = ["cham-a1a2", "--vang", H.ghi_json(tmp_path / "vang.json", vang), "--du-doan", H.ghi_json(tmp_path / "dd.json", du_doan), "--dong",
            H.ghi_json(tmp_path / "dong.json", bang), "--he", "chinh", "--ma-sach", a1a2_t.MA, "--ra", str(tmp_path / "bang.json")]
    _bi_mat_vao_tep(tmp_path / "vang.json", tmp_path / "dong.json")
    text = gom(argv)
    assert "a1.m1" in text and SECRET not in text
    assert SECRET not in (tmp_path / "bang.json").read_text(encoding="utf-8")
    assert _ro_ri_khi_in_ngay_tho(gom, monkeypatch, "danhgia.cham.lenh_a1a2", argv, (tmp_path / "dong.json").read_text(encoding="utf-8"))


def _bo_tep_the_gioi(tmp_path):
    ql_t._bo_tep(tmp_path, "thu")                                                    # hd, g3, g4, can: tên khái niệm bí mật nằm trong G3 và hợp đồng
    hd = json.loads((tmp_path / "hd.json").read_text(encoding="utf-8"))
    for k in hd["khai_niem"]:
        k["cau_neo"] = {"trang": 1, "cau": f"{SECRET} câu", "ma_chunk": "c"}
    H.ghi_json(tmp_path / "hd.json", hd)
    return {n: str(tmp_path / f"{n}.json") for n in ("hd", "g3", "g4", "can")}


def test_cham_khong_lo_bi_mat(tmp_path, monkeypatch, gom):
    t = _bo_tep_the_gioi(tmp_path)
    argv = ["cham", "--hop-dong", t["hd"], "--g3", t["g3"], "--g4", t["g4"], "--can", t["can"], "--ra", str(tmp_path / "bang.json")]
    _bi_mat_vao_tep(t["hd"], t["g3"])
    text = gom(argv)
    assert "a10.q6.nghiem" in text and SECRET not in text
    assert SECRET not in (tmp_path / "bang.json").read_text(encoding="utf-8")
    assert _ro_ri_khi_in_ngay_tho(gom, monkeypatch, "danhgia.__main__", argv, open(t["g3"], encoding="utf-8").read())


def test_kiem_khong_lo_bi_mat(tmp_path, monkeypatch, gom):
    t = _bo_tep_the_gioi(tmp_path)
    argv = ["kiem", t["hd"]]
    _bi_mat_vao_tep(t["hd"])
    text = gom(argv)
    assert "hợp lệ" in text and SECRET not in text
    assert _ro_ri_khi_in_ngay_tho(gom, monkeypatch, "danhgia.__main__", argv, open(t["hd"], encoding="utf-8").read())
