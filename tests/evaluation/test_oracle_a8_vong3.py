"""DG-14 vòng 3: lấp các lỗ mà bộ phá độc lập của Claude tìm ra ở vòng 2 (N2-N22), cộng hai chỉnh nhỏ.

Dùng lại dữ liệu dựng tay và fixture của `test_oracle_a8.py`.
"""
import json
import unicodedata

import pytest

import luot_ho_tro as lh
from danhgia.luot import ban_ghi
from danhgia.oracle_a8 import GhiDeCanonical, dung_canonical, ghi_canonical, kiem_canonical, tim_chunk
from test_luot import chan_mang, chinh, gia, sach  # noqa: F401 — fixture dùng chung
from test_oracle_a8 import CHUNKS, CHUNKS_CT, G3, MAU_MANIFEST, chay_oracle, dung, kn


def chunk(cid, page, order, text, role="noi_dung"):
    return {"chunk_id": cid, "page": page, "order_index": order, "role": role, "text": text}


def mot_khai_niem(trang_thai, trang, cau, ma="G-S-001"):
    return {**G3, "khai_niem": [kn(ma, "Tổng thể", trang_thai, trang, cau)]}


def dung_mot(g3, chunks, mau=MAU_MANIFEST, **kw):
    return dung_canonical(g3, chunks, doc_id="D", mau_manifest=mau, g3_sha256="s" * 64, **kw)


# ---------- N2, N3: node uncertain đứng trong dãy học như taught ----------

def test_node_uncertain_co_anchor_va_chunk_day():
    cau = "Tổng thể là tập hợp các phần tử."
    payload, manifest, bao = dung(mot_khai_niem(None, 1, cau))
    n = payload["nodes"][0]
    assert n["teaching_status"] == "uncertain" and bao["co_chunk"] == 1
    assert n["anchor"] == {"chunk_id": "c1", "char_start": 0, "sentence": cau}
    assert n["teaching_chunk_ids"] == ["c1"] and n["teaching_order_index"] == 0 and n["anchor_candidate_id"] == n["members"][0]
    assert n["mentioned_in"] == []
    assert kiem_canonical(payload, manifest, {c["chunk_id"] for c in CHUNKS}) == []


# ---------- N4, N5: hoà điểm ----------

def test_hoa_diem_uu_tien_chunk_noi_dung_roi_chunk_truoc():
    cau = "Phương sai đo độ phân tán của mẫu quanh trung bình mẫu."
    assert tim_chunk(cau, 5, [chunk("a", 5, 0, cau, "vi_du"), chunk("b", 5, 1, cau, "noi_dung")])[0]["chunk_id"] == "b"
    hai = [chunk("a", 5, 0, cau), chunk("b", 5, 1, cau)]
    assert tim_chunk(cau, 5, hai)[0]["chunk_id"] == "a"
    assert tim_chunk(cau, 5, list(reversed(hai)))[0]["chunk_id"] == "a"  # không phụ thuộc thứ tự trong danh sách


# ---------- N6: chunk kế phải cùng trang hoặc trang liền sau ----------

def test_cau_vat_sang_chunk_cach_hai_trang_khong_duoc_noi():
    a = chunk("a", 4, 0, "Đoạn kết thúc ở cuối trang, câu định nghĩa vắt sang chunk")
    b = chunk("b", 6, 1, "kế tiếp ở đầu trang sau và kết thúc tại đây.")
    cau = "Đoạn kết thúc ở cuối trang, câu định nghĩa vắt sang chunk kế tiếp ở đầu trang sau và kết thúc tại đây."
    assert tim_chunk(cau, 4, [a, b])[2] == "khong_khop"
    assert tim_chunk(cau, 4, [a, {**b, "page": 5}])[2] == "ok_vat_chunk"  # đối chứng: trang liền sau thì nối được


# ---------- N8: lệch trang kèm vắt chunk vẫn là lệch trang ----------

def test_lech_trang_kem_vat_chunk_van_duoc_dem():
    cau = "Đoạn kết thúc ở cuối trang, câu định nghĩa vắt sang chunk kế tiếp ở đầu trang sau và kết thúc tại đây."
    payload, _, bao = dung_mot(mot_khai_niem("day_o_day", 3, cau), CHUNKS_CT)  # vàng ghi trang 3, câu thật ở trang 4-5
    assert bao["theo_ly_do"] == {"ok_lech_trang_vat_chunk": 1} and bao["trang_lech"] == 1
    assert payload["nodes"][0]["anchor"]["chunk_id"] == "k3"


# ---------- N12: members phải đúng tập node_id ----------

@pytest.mark.parametrize("sua", [
    lambda p: p["members"].pop(p["nodes"][0]["node_id"]),
    lambda p: p["members"].__setitem__("node_la", ["cand_la"]),
])
def test_kiem_luoc_do_members_phai_dung_tap_node_id(sua):
    payload, manifest, _ = dung()
    sua(payload)
    loi = kiem_canonical(payload, manifest, {c["chunk_id"] for c in CHUNKS})
    assert any("payload.members" in l for l in loi), loi


# ---------- N15: câu khớp nguyên văn ở giữa chunk ----------

def test_char_start_va_cau_nguyen_van_o_giua_chunk():
    van_ban = "Khi đó ta xét n lớn. Khi đó N = 5 thì ta có kết quả."
    cau = "Khi đó N = 5 thì ta có kết quả."
    payload, _, bao = dung_mot(mot_khai_niem("day_o_day", 1, cau), [chunk("m", 1, 0, van_ban)])
    n = payload["nodes"][0]
    assert bao["co_chunk"] == 1 and van_ban.index(cau) == 21
    assert n["anchor"]["char_start"] == 21 and n["anchor"]["sentence"] == cau
    assert n["evidence"][0]["char_start"] == 21 and n["evidence"][0]["quote"] == cau and n["evidence"][0]["char_end"] == 21 + len(cau)


# ---------- N22: ngưỡng nghiêm ----------

def test_nguong_nghiem_khong_gan_cau_diem_tu_075_den_09():
    from danhgia.cham.khai_niem import diem_cau
    from danhgia.oracle_a8.canonical import NGUONG_CAU
    cau = "Tổng thể là tập hợp các phần tử nghiên cứu"
    diem = diem_cau(cau, 1, {1: CHUNKS[0]["text"]})
    assert 0.75 <= diem < 0.9 and NGUONG_CAU == 0.9  # đo độc lập: giữa ngưỡng nới và ngưỡng nghiêm
    c, _, ly_do = tim_chunk(cau, 1, CHUNKS)
    assert c is None and ly_do == "khong_khop"
    assert tim_chunk(cau, 1, CHUNKS, nguong=0.75)[0]["chunk_id"] == "c1"  # đối chứng: nới ngưỡng thì gắn được


# ---------- ghi_canonical dùng lại bản cũ chỉ khi hash cấu hình trùng hẳn ----------

def test_ghi_canonical_chi_dung_lai_khi_hash_cau_hinh_trung_han(tmp_path):
    payload, manifest, _ = dung()
    kho = tmp_path / "kho"
    ghi_canonical(kho, "D", payload, manifest)
    p2, m2, _ = dung_mot(G3, CHUNKS, nguong=0.8)  # cùng G3, đổi ngưỡng
    assert m2["config"]["g3_sha256"] == manifest["config"]["g3_sha256"] and m2["config_hash"] != manifest["config_hash"]
    with pytest.raises(GhiDeCanonical, match="hash cấu hình"):
        ghi_canonical(kho, "D", p2, m2)
    mau2 = {**MAU_MANIFEST, "config": {**MAU_MANIFEST["config"], "anchor_chunks_version": 8}}  # cùng G3, đổi nguồn chunk
    p3, m3, _ = dung_mot(G3, CHUNKS, mau=mau2)
    with pytest.raises(GhiDeCanonical):
        ghi_canonical(kho, "D", p3, m3)
    assert ghi_canonical(kho, "D", payload, manifest) == 1  # đúng cấu hình cũ: dùng lại


# ---------- che_cong_thuc: từ tiếng Việt một chữ có dấu là chữ thường ----------

def test_che_cong_thuc_giu_tu_viet_mot_chu_co_dau():
    from danhgia.oracle_a8.canonical import che_cong_thuc
    assert che_cong_thuc("Biến ngẫu nhiên ở đây là hàm số") == "Biến ngẫu nhiên ở đây là hàm số"
    assert che_cong_thuc("Đó là ý à") == "Đó là ý à"
    assert che_cong_thuc("Gọi ε là sai số và x̄ là trung bình") == "Gọi [formula] là sai số và [formula] là trung bình"
    assert che_cong_thuc("ở ε ở") == "ở [formula] ở"
    assert che_cong_thuc(unicodedata.normalize("NFD", "Biến ở đây")) == unicodedata.normalize("NFC", "Biến ở đây")


# ---------- bước dung-oracle của lệnh luot: chọn phiên bản chunks, dừng khi lỗi lược đồ ----------

def _them_chunks_v2(chinh, ghi_anchor_version=None):
    """Chunks v2 (chunk_id đổi tiền tố) trong kho lượt chính; tuỳ chọn ghi anchor_chunks_version vào manifest canonical của lượt chính."""
    import shutil
    goc = chinh / "kho" / "chunks" / lh.DOC
    shutil.copytree(goc / "v1", goc / "v2")
    cs = json.loads((goc / "v2" / "chunks.json").read_text(encoding="utf-8"))
    for c in cs:
        c["chunk_id"] = "x_" + c["chunk_id"]
    (goc / "v2" / "chunks.json").write_text(json.dumps(cs), encoding="utf-8")
    if ghi_anchor_version is not None:
        mf = sorted((chinh / "kho" / "canonical" / lh.DOC).glob("v*/manifest.json"))[-1]
        m = json.loads(mf.read_text(encoding="utf-8"))
        m.setdefault("config", {})["anchor_chunks_version"] = ghi_anchor_version
        mf.write_text(json.dumps(m), encoding="utf-8")
    return {c["chunk_id"] for c in cs}


def _id_chunk_oracle(ra):
    p = json.loads((ra / "kho" / "canonical" / lh.DOC / "v1" / "canonical.json").read_text(encoding="utf-8"))
    return {c for n in p["nodes"] for c in n["defining_chunk_ids"]}


def test_oracle_dung_chunks_ban_moi_nhat_khi_canonical_chinh_khong_ghi_phien_ban(sach, gia, chinh, tmp_path):  # N17
    ids_v2 = _them_chunks_v2(chinh)
    ra = tmp_path / "oracle"
    assert chay_oracle(sach, gia, chinh, ra, co_chi=False)[0] == 0
    ids = _id_chunk_oracle(ra)
    assert ids and ids <= ids_v2  # chunk_id của bản v2, không phải bản v1 cũ nhất


def test_oracle_dung_anchor_chunks_version_cua_canonical_luot_chinh(sach, gia, chinh, tmp_path):  # N18
    ids_v2 = _them_chunks_v2(chinh, ghi_anchor_version=1)
    ra = tmp_path / "oracle"
    assert chay_oracle(sach, gia, chinh, ra, co_chi=False)[0] == 0
    ids = _id_chunk_oracle(ra)
    assert ids and not (ids & ids_v2)  # manifest ghi bản 1: chunk_id của bản 1


def test_dung_oracle_loi_luoc_do_dung_o_buoc_khong_ghi_canonical_khong_goi_roadmap(sach, gia, chinh, tmp_path, monkeypatch):  # N19
    import danhgia.oracle_a8 as o
    that = o.dung_canonical

    def hong(*a, **k):
        payload, manifest, bao = that(*a, **k)
        del payload["nodes"][0]["teaching_status"]  # làm hỏng lược đồ
        return payload, manifest, bao

    monkeypatch.setattr(o, "dung_canonical", hong)
    so_roadmap = gia.goi_mo_hinh["roadmap"]
    ra = tmp_path / "oracle"
    assert chay_oracle(sach, gia, chinh, ra)[0] == 1  # có --allow-spend mà vẫn dừng
    ban = ban_ghi.doc(ra)
    buoc = {b["ten"]: b for b in ban["buoc"]}
    assert buoc["dung-oracle"]["trang_thai"] == "loi" and "lược đồ" in (buoc["dung-oracle"]["ghi_chu"] or "")
    assert buoc["roadmap"]["trang_thai"] == "cho" and gia.goi_mo_hinh["roadmap"] == so_roadmap
    thu = ra / "kho" / "canonical" / lh.DOC
    assert not thu.exists() or not list(thu.rglob("*.json"))
    assert not ban_ghi.da_xong(ban)
