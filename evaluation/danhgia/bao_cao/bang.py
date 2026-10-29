"""Bảng 9–12 dạng Markdown (bản hội đồng mục 13). Chỉ định dạng: số đã tính nguyên ở `so_lieu.py`, làm tròn ở đây và chỉ ở đây.

Quy ước hiển thị: dấu thập phân là phẩy; ô không có số là "—" (không bao giờ 0); khoảng tin cậy `[thấp; cao]`.
"""
from __future__ import annotations

from danhgia.bao_cao import so_lieu as S
from danhgia.bao_cao import thuoc as T

KHONG_CO = "—"


def so(x, chu_so, *, dau=False):
    if x is None:
        return KHONG_CO
    s = f"{x:+.{chu_so}f}" if dau else f"{x:.{chu_so}f}"
    if float(s) == 0:
        s = f"{0:.{chu_so}f}"
    return s.replace(".", ",")


def _khoang(thap, cao, chu_so, *, dau=False):
    return f"[{so(thap, chu_so, dau=dau)}; {so(cao, chu_so, dau=dau)}]"


def o_text(o, chu_so, n_cuon):
    """Ô một số kèm CI. `o` là kết quả `Tinh.o`; không có dòng hay macro None thì "—"."""
    if o is None or o["macro"] is None:
        return KHONG_CO
    ket = so(o["macro"], chu_so)
    if o["thap"] is not None:
        ket += " " + _khoang(o["thap"], o["cao"], chu_so)
    if o["so_cuon_co_so"] < n_cuon:
        ket += f" ({o['so_cuon_co_so']}/{n_cuon} cuốn có số)"
    return ket


def _hang(*cot):
    return "| " + " | ".join(cot) + " |"


def _bang(ten, tieu_de, hang, chu_thich=()):
    dong = [ten, "", _hang(*tieu_de), _hang(*["---"] * len(tieu_de)), *hang]
    if chu_thich:
        dong += ["", *chu_thich]
    return "\n".join(dong) + "\n"


def _chu_so(thuoc):
    return {T.THUOC_PHUT: 1, T.THUOC_PHUT_KHONG_CHO: 1, T.THUOC_USD: 2}.get(thuoc, 3)


class Boi:
    """Gói đầu vào cho mọi bảng: đối tượng tính, các lượt nhiễu, kiểm định, dải nhiễu, G5."""

    def __init__(self, tinh, *, nhieu=(), g5=None, doi_he=None):
        self.tinh, self.nhieu, self.g5, self.doi_he = tinh, list(nhieu), g5, doi_he or {}
        self.n = len(tinh.sach)
        self.kd = tinh.kiem_dinh_chinh_thuc()
        self.dai = S.dai_nhieu(tinh, self.nhieu)

    def trong_dai(self, he, thuoc):
        if he in ("chinh", T.HE_TRAN_NGUOI) or thuoc not in self.dai:
            return False
        o, oc = self.tinh.o(he, thuoc), self.tinh.o("chinh", thuoc)
        return S.trong_dai_nhieu(o and o["macro"], oc and oc["macro"], self.dai[thuoc])


def bang_9(b):
    hang = []
    for he, nhan in T.HE_BANG_9:
        o_cot = []
        for _, _, thuoc, chu_so, _ in T.COT_BANG_9:
            if he == T.HE_TRAN_NGUOI and thuoc != T.THUOC_F1:
                o_cot.append(KHONG_CO)      # trần người chỉ có F1 cạnh: các cột khác không áp dụng
                continue
            text = o_text(b.tinh.o(he, thuoc), chu_so, b.n)
            if text != KHONG_CO and b.trong_dai(he, thuoc):
                text += " (trong dải nhiễu)"
            o_cot.append(text)
        hang.append(_hang(nhan, *o_cot))
    ghi_chu = [f"Ghi chú. Mỗi ô là trung bình macro theo cuốn của {b.n} cuốn, khoảng tin cậy 95% bootstrap phân cấp (cuốn rồi chương). "
               "Q6 càng thấp càng tốt; ô không có số hiện —. Trần người chỉ có F1 cạnh; các cột khác không áp dụng."]
    phu = b.tinh.o("chinh", T.THUOC_PHUT_KHONG_CHO)
    if phu is not None:
        ghi_chu.append(f"Phút/cuốn của hệ chính không tính phần chờ embedding: {o_text(phu, 1, b.n)}.")
    ghi_chu.append("Chi phí của B1, B2 chỉ gồm phần tính lại từ artifact đã lưu, không gồm lượt chạy hệ chính.")
    kd_dong = []
    nhan_kd = {"q6_chinh_so_b1": "Q6, hệ chính so với B1", "f1_chinh_so_b5": "F1 cạnh, hệ chính so với B5",
               "bang_chung_chinh_so_b5": "bằng chứng có thật, hệ chính so với B5"}
    for ten, m in b.kd.items():
        if m["p"] is None:
            kd_dong.append(f"- {nhan_kd[ten]}: {KHONG_CO} ({m['loi']})")
            continue
        kd_dong.append(f"- {nhan_kd[ten]}: hiệu {so(m['hieu'], 3, dau=True)}; p hoán vị {so(m['p'], 4)}, p sau Holm {so(m['p_holm'], 4)}; "
                       f"sign test theo cuốn {m['thang']} thắng, {m['thua']} thua, {m['hoa']} hoà, p {so(m['p_sign'], 4)}")
    so_lan = f"{b.tinh.so_vong:,}".replace(",", ".")
    ghi_chu += ["", f"Ba phép kiểm định chính thức (hoán vị ghép cặp {so_lan} lần, hai phía, hiệu chỉnh Holm cho cả ba):", *kd_dong]
    dai = [f"{nhan}: {so(b.dai[t]['min'], 3)}–{so(b.dai[t]['max'], 3)}" for _, nhan, t, _, _ in T.COT_BANG_9[:4] if b.dai.get(t)]
    if dai:
        so_luot = max(d["so_luot"] for d in b.dai.values() if d)
        ghi_chu += ["", f"Dải nhiễu của hệ chính qua {so_luot} lượt (min–max): " + "; ".join(dai)
                    + ". Ô của hệ so sánh có chênh với hệ chính nhỏ hơn bề rộng dải thì đánh dấu \"trong dải nhiễu\"."]
    return _bang(f"Bảng 9. Kết quả đầu-cuối trên {b.n} giáo trình (khoảng tin cậy 95% trong ngoặc vuông)",
                 ["Hệ", *[c[1] for c in T.COT_BANG_9]], hang, ghi_chu)


def bang_10(b):
    hang = []
    for khau, nhan, thuoc_list, co_tran in T.BANG_10:
        def cot(he):
            phan = []
            for nhan_phu, thuoc in thuoc_list:
                t = o_text(b.tinh.o(he, thuoc), 3, b.n)
                phan.append(f"{nhan_phu} {t}".strip() if len(thuoc_list) > 1 else t)
            return " / ".join(phan)
        hang.append(_hang(khau, nhan, cot("chinh"), cot(T.HE_TRAN_NGUOI) if co_tran else KHONG_CO))
    return _bang("Bảng 10. Kết quả từng khâu", ["Khâu", "Thước chính", "Hệ chính", "Trần người"], hang,
                 ["Ô trần người của khâu không có đồng thuận giữa hai sinh viên hiện —."])


def _hieu_text(b, he, nhan, thuoc, chu_so):
    h = b.tinh.hieu(he, "chinh", thuoc)
    if h is None or h["hieu"] is None:
        return f"{nhan} {KHONG_CO}"
    text = f"{nhan} {so(h['hieu'], chu_so, dau=True)}"
    if h["thap"] is not None:
        text += " " + _khoang(h["thap"], h["cao"], chu_so, dau=True)
    dai = b.dai.get(thuoc)
    if dai is not None and abs(h["hieu"]) < dai["max"] - dai["min"]:
        text += " (trong dải nhiễu)"
    return text


def bang_11(b):
    hang, da_oracle = [], False
    for he, nhan, chi_so, nhom in T.BANG_11:
        if nhom == "oracle" and not da_oracle:
            hang.append(_hang("**Thiết lập oracle (không đặt ngang hệ thật)**", "", ""))
            da_oracle = True
        co_dong = any(b.tinh.o(he, t) is not None for _, t, _ in chi_so)
        if not co_dong:
            hang.append(_hang(nhan, f"{KHONG_CO} (không chạy)", KHONG_CO))
            continue
        thay_doi = "; ".join(_hieu_text(b, he, nhan_cs, t, cs) for nhan_cs, t, cs in chi_so)
        usd, phut = b.tinh.o(he, T.THUOC_USD), b.tinh.o(he, T.THUOC_PHUT)
        chi_phi = "; ".join(x for x in (
            f"{so(usd['macro'], 2)} USD" if usd and usd["macro"] is not None else "",
            f"{so(phut['macro'], 1)} phút" if phut and phut["macro"] is not None else "") if x) or KHONG_CO
        hang.append(_hang(nhan, thay_doi, chi_phi))
    return _bang("Bảng 11. Thí nghiệm bỏ hoặc thay bộ phận", ["Thí nghiệm", "Thay đổi so với hệ chính", "Chi phí thay đổi"], hang,
                 ["Thay đổi = chỉ số của biến thể trừ chỉ số của hệ chính trên các cuốn có ở cả hai, kèm khoảng tin cậy 95% bootstrap phân cấp ghép cặp. "
                  "Chi phí là phần ghi nhận trong hợp đồng của biến thể, không gồm phần dùng lại từ lượt chính."])


def bang_12(b):
    g = b.g5
    cac_he = [("chinh", "Hệ chính"), ("b1", "B1 mục lục"), ("b5", "B5 mô hình đọc thẳng")]
    if g is None:
        rubric = {h: KHONG_CO for h, _ in cac_he}
        thang = dict(rubric)
    else:
        rubric = {h: so(g["rubric"][h]["trung_binh"], 2) if h in g["rubric"] else KHONG_CO for h, _ in cac_he}
        thang = {}
        for h, _ in cac_he:
            t = g["ti_le_thang"].get(h)
            thang[h] = KHONG_CO if not t or t["ti_le"] is None else f"{so(t['ti_le'], 3)} [{so(t['wilson'][0], 3)}; {so(t['wilson'][1], 3)}] ({t['thang']}/{t['n']})"
    hang = [_hang("Điểm rubric trung bình (thang 7)", *[rubric[h] for h, _ in cac_he]),
            _hang("Tỉ lệ thắng khi so cặp (tính trên các cặp có hệ đó)", *[thang[h] for h, _ in cac_he])]
    chu_thich = ["Kết quả thăm dò, không kiểm định. Khoảng trong ngoặc vuông là Wilson 95% trên số lượt so cặp gộp mọi người chấm; hoà tính vào mẫu số. "
                 "Ba hệ so theo vòng tròn nên mỗi hệ xuất hiện ở hai cặp."]
    if g is not None and g["cap"]:
        hang_cap = [_hang("Cặp", "Thắng (trái)", "Thắng (phải)", "Hoà", "Tỉ lệ thắng (trái)")]
        hang_cap.append(_hang(*["---"] * 5))
        for c in sorted(g["cap"].values(), key=lambda c: [T.thu_tu_he(h) for h in c["he"]]):
            trai, phai = c["he"]
            n = c["thang"][trai] + c["thang"][phai] + c["hoa"]
            hang_cap.append(_hang(f"{T.HE_NHAN.get(trai, trai)} ~ {T.HE_NHAN.get(phai, phai)}", str(c["thang"][trai]), str(c["thang"][phai]),
                                  str(c["hoa"]), so(c["thang"][trai] / n, 3) if n else KHONG_CO))
        chu_thich += ["", "Theo cặp:", "", *hang_cap]
    return _bang("Bảng 12. Đánh giá của người học (sinh viên chấm lộ trình, mù tên hệ)", ["Tiêu chí", *[n for _, n in cac_he]], hang, chu_thich)


def tao_bang(b):
    return {"bang-9.md": bang_9(b), "bang-10.md": bang_10(b), "bang-11.md": bang_11(b), "bang-12.md": bang_12(b)}
