"""Hình 3 (điểm F1 theo cuốn, có CI) và Hình 4 (thác nước quy lỗi) bằng SVG viết tay, không thư viện vẽ.

Theo skill dataviz: màu từ bảng phân loại đã validate (`thuoc.MAU_KHAU`), mực chữ dùng token chữ (không bao giờ màu của chuỗi dữ liệu), lưới và trục
một bậc xám nhạt, nét 1 px, khoảng hở 2 px màu nền giữa các thanh, chấm có vòng 2 px màu nền, thanh dày tối đa 24 px, có chú giải khi từ hai chuỗi.
Nền sáng và tối đổi bằng `prefers-color-scheme` trong `<style>` của SVG. Mọi toạ độ ghi hai chữ số thập phân.
"""
from __future__ import annotations

import textwrap
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from danhgia.bao_cao import thuoc as T
from danhgia.bao_cao.bang import so

RONG = 760
TRUC_MIN, TRUC_MAX = 0.0, 1.0          # Hình 3: trục F1 từ 0 đến 1; CI của tỉ lệ luôn nằm trong đoạn này nên không bao giờ bị cắt
DAM = ' font-weight="600"'
DAY_TOI_DA = 24                        # bề dày thanh tối đa (px)

BEN_SANG = {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781", "grid": "#e1e0d9", "axis": "#c3c2b7"}
BEN_TOI = {"surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781", "grid": "#2c2c2a", "axis": "#383835"}
# Hình 3: hai chuỗi lấy hai ô đầu của bảng phân loại (xanh dương, cam)
CHUOI_HINH_3 = (("chinh", "Hệ chính", ("#2a78d6", "#3987e5")), ("b5", "B5 mô hình đọc thẳng", ("#eb6834", "#d95926")))


def slug_khau(khau):
    return khau.lower().replace("/", "-")


def _f(v):
    return f"{v:.2f}"


def _css(luat_sang, luat_toi):
    def khoi(ben, rule):
        return "".join(f"--{k}:{v};" for k, v in ben.items()) + rule
    return (f"svg{{{khoi(BEN_SANG, '')}font-family:system-ui,-apple-system,'Segoe UI',sans-serif}}"
            "text{fill:var(--ink)}.ink2{fill:var(--ink2)}.muted{fill:var(--muted)}.nen{fill:var(--surface)}"
            ".luoi{stroke:var(--grid);stroke-width:1;fill:none}.truc{stroke:var(--axis);stroke-width:1;fill:none}"
            f"{luat_sang}"
            f"@media (prefers-color-scheme: dark){{svg{{{khoi(BEN_TOI, '')}}}{luat_toi}}}")


def _khung(tieu_de, mo_ta, chieu_cao, css, than):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {RONG} {chieu_cao}" width="{RONG}" height="{chieu_cao}" role="img" '
            f'lang="vi">\n<title>{escape(tieu_de)}</title>\n<desc>{escape(mo_ta)}</desc>\n<style>{css}</style>\n'
            f'<rect class="nen" x="0" y="0" width="{RONG}" height="{chieu_cao}"/>\n{than}</svg>\n')


def kiem_xml(text):
    """Ném `xml.etree.ElementTree.ParseError` nếu SVG không hợp lệ; trả gốc cây."""
    return ET.fromstring(text)


# ------------------------------------------------------------------------------------------------ Hình 3


def hinh_3(h3, *, so_cuon_nhan="Trung bình"):
    """`h3`: kết quả `so_lieu.hinh3`: `{"sach": [{ma_sach, nhan, chinh, b5}], "trung_binh": {chinh, b5}}`."""
    x0, x1 = 210.0, RONG - 50.0
    cao_hang, y_dau = 36.0, 78.0
    hang = list(h3["sach"]) + [{"ma_sach": None, "nhan": so_cuon_nhan, **h3["trung_binh"]}]
    y_tb = y_dau + cao_hang * len(h3["sach"]) + 14.0          # dải trống ngăn hàng trung bình khỏi các cuốn
    y_cuoi = y_tb + cao_hang
    chieu_cao = int(y_cuoi + 70)

    def x(v):
        return x0 + (v - TRUC_MIN) / (TRUC_MAX - TRUC_MIN) * (x1 - x0)

    luat_sang = "".join(f".s-{k}{{fill:{m[0]};stroke:{m[0]}}}" for k, _, m in CHUOI_HINH_3)
    luat_toi = "".join(f".s-{k}{{fill:{m[1]};stroke:{m[1]}}}" for k, _, m in CHUOI_HINH_3)
    luat_sang += ".s-chinh,.s-b5{stroke-width:2}.vong{stroke:var(--surface);stroke-width:2}.vong.s-chinh,.vong.s-b5{stroke:var(--surface)}"
    luat_toi += ".vong,.vong.s-chinh,.vong.s-b5{stroke:var(--surface)}"
    p = [f'<text x="{_f(x0 - 190 + 16)}" y="24" font-size="15" font-weight="600">Hình 3. F1 cạnh tiên quyết theo từng cuốn</text>',
         f'<text class="ink2" x="{_f(x0 - 190 + 16)}" y="42" font-size="12">Chấm: giá trị từng cuốn; thanh: CI 95% (bootstrap chương). Hàng cuối: trung bình macro, CI phân cấp.</text>']
    # chú giải: luôn có vì có hai chuỗi
    lx = x0
    for k, nhan, _ in CHUOI_HINH_3:
        p.append(f'<circle class="s-{k}" cx="{_f(lx + 5)}" cy="60" r="5"/><text class="ink2" x="{_f(lx + 16)}" y="64" font-size="12">{escape(nhan)}</text>')
        lx += 190
    # lưới và trục x
    for i in range(6):
        v = TRUC_MIN + i * (TRUC_MAX - TRUC_MIN) / 5
        p.append(f'<line class="luoi" x1="{_f(x(v))}" y1="{_f(y_dau - 10)}" x2="{_f(x(v))}" y2="{_f(y_cuoi)}"/>')
        p.append(f'<text class="muted" x="{_f(x(v))}" y="{_f(y_cuoi + 18)}" font-size="11" text-anchor="middle">{so(v, 1)}</text>')
    p.append(f'<line class="truc" x1="{_f(x0)}" y1="{_f(y_cuoi)}" x2="{_f(x1)}" y2="{_f(y_cuoi)}"/>')
    p.append(f'<text class="ink2" x="{_f((x0 + x1) / 2)}" y="{_f(y_cuoi + 40)}" font-size="12" text-anchor="middle">F1 cạnh tiên quyết (trục từ 0 đến 1)</text>')
    p.append(f'<rect id="vung-ve" x="{_f(x0)}" y="{_f(y_dau - 10)}" width="{_f(x1 - x0)}" height="{_f(y_cuoi - y_dau + 10)}" fill="none" '
             f'data-truc-min="{TRUC_MIN}" data-truc-max="{TRUC_MAX}"/>')
    # hàng
    for i, h in enumerate(hang):
        la_tb = h["ma_sach"] is None
        y = (y_tb if la_tb else y_dau + cao_hang * i)
        yc = y + cao_hang / 2
        p.append(f'<text x="{_f(x0 - 12)}" y="{_f(yc + 4)}" font-size="12" text-anchor="end"'
                 f'{DAM if la_tb else ""}>{escape(h["nhan"])}</text>')
        for j, (k, _, _) in enumerate(CHUOI_HINH_3):
            v = h.get(k)
            yy = yc + (j - 0.5) * 12
            if v is None or v.get("gia_tri") is None:
                p.append(f'<text class="muted" x="{_f(x0 + 8)}" y="{_f(yy + 4)}" font-size="11" data-he="{k}">—</text>')
                continue
            if v.get("thap") is not None:
                p.append(f'<line class="ci s-{k}" data-he="{k}" x1="{_f(x(v["thap"]))}" y1="{_f(yy)}" x2="{_f(x(v["cao"]))}" y2="{_f(yy)}" stroke-width="2" '
                         f'stroke-linecap="round"/>')
            p.append(f'<circle class="diem vong s-{k}" data-he="{k}" cx="{_f(x(v["gia_tri"]))}" cy="{_f(yy)}" r="4.5">'
                     f'<title>{escape(h["nhan"])}, {escape(dict((a, b) for a, b, _ in CHUOI_HINH_3)[k])}: {so(v["gia_tri"], 3)}</title></circle>')
        if la_tb:     # chỉ hàng trung bình ghi số trực tiếp: gắn nhãn chọn lọc, không ghi mọi chấm
            for j, (k, _, _) in enumerate(CHUOI_HINH_3):
                v = h.get(k)
                if v and v.get("gia_tri") is not None:
                    p.append(f'<text x="{_f(x1 + 4)}" y="{_f(yc + (j - 0.5) * 12 + 4)}" font-size="11" text-anchor="start">{so(v["gia_tri"], 3)}</text>')
    mo_ta = ("Điểm F1 cạnh tiên quyết của hệ chính và B5 theo từng cuốn, kèm khoảng tin cậy 95%, và hàng trung bình macro. "
             + "; ".join(f'{h["nhan"]}: ' + ", ".join(f'{n} {so(h[k]["gia_tri"], 3)}' for k, n, _ in CHUOI_HINH_3 if h.get(k) and h[k].get("gia_tri") is not None)
                         for h in hang))
    svg = _khung("Hình 3. F1 cạnh tiên quyết theo từng cuốn", mo_ta, chieu_cao, _css(luat_sang, luat_toi), "\n".join(p) + "\n")
    kiem_xml(svg)
    return svg


# ------------------------------------------------------------------------------------------------ Hình 4


def _buoc_chia(tong):
    """Bước vạch trục: 1, 2 hay 5 nhân luỹ thừa 10, sao cho có từ 2 đến 5 vạch."""
    if tong <= 0:
        return 1
    for mu in range(0, 9):
        for m in (1, 2, 5):
            if tong / (m * 10 ** mu) <= 5:
                return m * 10 ** mu
    return 10 ** 9


def _cot_goc(x, y_tren, y_day, w, r):
    """Thanh mọc từ đường đáy: bo 4 px ở đầu dữ liệu (trên), vuông ở đáy."""
    h = y_day - y_tren
    r = min(r, h / 2, w / 2)
    return (f"M{_f(x)} {_f(y_day)}V{_f(y_tren + r)}Q{_f(x)} {_f(y_tren)} {_f(x + r)} {_f(y_tren)}H{_f(x + w - r)}"
            f"Q{_f(x + w)} {_f(y_tren)} {_f(x + w)} {_f(y_tren + r)}V{_f(y_day)}Z")


def hinh_4(h4):
    """`h4`: kết quả `so_lieu.thac_nuoc`: `{he, so_cuon, tong, dung, ly_do: {1..7: số hoặc None}, khong_ap}`."""
    x0, x1, y_tren, y_day = 60.0, RONG - 20.0, 96.0, 330.0
    tong = h4["tong"]
    cot = ([("tong", None, "Tổng cạnh vàng", tong, None)]
           + [("ly_do", i, T.LY_DO[i][1], h4["ly_do"][i], T.LY_DO[i][0]) for i in sorted(T.LY_DO)]
           + [("dung", None, "Lộ trình làm đúng", h4["dung"], None)])
    o = (x1 - x0) / len(cot)
    ty_le = (y_day - y_tren) / tong if tong else 1.0

    def y(v):
        return y_day - v * ty_le

    luat_sang = "".join(f".khau-{slug_khau(k)}{{fill:{m[0]}}}" for k, m in T.MAU_KHAU.items())
    luat_toi = "".join(f".khau-{slug_khau(k)}{{fill:{m[1]}}}" for k, m in T.MAU_KHAU.items())
    luat_sang += f".c-tong{{fill:{T.MAU_TONG[0]}}}.c-dung{{fill:{T.MAU_DUNG[0]}}}.noi{{stroke:var(--axis);stroke-width:1}}"
    luat_toi += f".c-tong{{fill:{T.MAU_TONG[1]}}}.c-dung{{fill:{T.MAU_DUNG[1]}}}"
    p = ['<text x="16" y="24" font-size="15" font-weight="600">Hình 4. Quan hệ tiên quyết bị mất qua từng khâu</text>',
         f'<text class="ink2" x="16" y="42" font-size="12">Tổng hợp {h4["so_cuon"]} cuốn, mức căn nghiêm: mỗi thanh giảm là số cạnh vàng trong phạm vi '
         f'mà khâu đó làm hỏng đầu tiên.</text>']
    # chú giải khâu (bảy khâu, màu đúng bảng màu khâu của Hình 1)
    lx = 16.0
    for k in T.MAU_KHAU:
        p.append(f'<rect class="khau-{slug_khau(k)}" x="{_f(lx)}" y="56" width="10" height="10" rx="2"/>'
                 f'<text class="ink2" x="{_f(lx + 15)}" y="65" font-size="11">{escape(k)}</text>')
        lx += 15 + 7 * len(k) + 14
    buoc = _buoc_chia(tong)
    v = 0
    while v <= tong:
        p.append(f'<line class="luoi" x1="{_f(x0)}" y1="{_f(y(v))}" x2="{_f(x1)}" y2="{_f(y(v))}"/>'
                 f'<text class="muted" x="{_f(x0 - 8)}" y="{_f(y(v) + 4)}" font-size="11" text-anchor="end">{v}</text>')
        v += buoc
    p.append(f'<line class="truc" x1="{_f(x0)}" y1="{_f(y_day)}" x2="{_f(x1)}" y2="{_f(y_day)}"/>')
    p.append(f'<text class="ink2" x="16" y="{_f((y_tren + y_day) / 2)}" font-size="12" text-anchor="middle" '
             f'transform="rotate(-90 16 {_f((y_tren + y_day) / 2)})">Số cạnh vàng</text>')
    muc, w = tong, min(DAY_TOI_DA, o - 8)
    for j, (loai, i, nhan, gia_tri, khau) in enumerate(cot):
        cx = x0 + o * (j + 0.5)
        xl = cx - w / 2
        if loai == "ly_do":
            lop = f"khau-{slug_khau(khau)}"
            if gia_tri is None:
                p.append(f'<text class="muted" x="{_f(cx)}" y="{_f(y_day - 8)}" font-size="11" text-anchor="middle" font-style="italic" data-ly-do="{i}">không áp</text>')
            else:
                tren, duoi = muc, muc - gia_tri
                if gia_tri > 0:
                    p.append(f'<rect class="cot {lop}" data-ly-do="{i}" data-khau="{escape(khau)}" x="{_f(xl)}" y="{_f(y(tren))}" width="{_f(w)}" '
                             f'height="{_f(y(duoi) - y(tren))}" rx="4"><title>Lý do {i}, {escape(khau)}: {escape(nhan)}, {gia_tri} cạnh</title></rect>')
                p.append(f'<text class="gia-tri" x="{_f(cx)}" y="{_f(y(tren) - 6)}" font-size="12" text-anchor="middle" data-ly-do="{i}">{gia_tri}</text>')
                muc = duoi
        else:
            lop = f"c-{loai}"
            top = y(gia_tri)
            if gia_tri > 0:
                p.append(f'<path class="cot {lop}" data-cot="{loai}" d="{_cot_goc(xl, top, y_day, w, 4)}"><title>{escape(nhan)}: {gia_tri} cạnh</title></path>')
            p.append(f'<text class="gia-tri" x="{_f(cx)}" y="{_f(top - 6)}" font-size="12" text-anchor="middle" data-cot="{loai}" font-weight="600">{gia_tri}</text>')
        dong_nhan = ([khau] if khau else []) + textwrap.wrap(nhan, width=13)
        for r, d in enumerate(dong_nhan):
            p.append(f'<text class="ink2" x="{_f(cx)}" y="{_f(y_day + 18 + 13 * r)}" font-size="11" text-anchor="middle"'
                     f'{DAM if khau and r == 0 else ""}>{escape(d)}</text>')
    mo_ta = (f"Thác nước quy lỗi {h4['so_cuon']} cuốn: {tong} cạnh vàng trong phạm vi; "
             + "; ".join(f"lý do {i} ({T.LY_DO[i][0]}, {T.LY_DO[i][1]}) " + ("không áp" if h4["ly_do"][i] is None else f'mất {h4["ly_do"][i]}') for i in sorted(T.LY_DO))
             + f"; {h4['dung']} cạnh đúng.")
    svg = _khung("Hình 4. Quan hệ tiên quyết bị mất qua từng khâu", mo_ta, 420, _css(luat_sang, luat_toi), "\n".join(p) + "\n")
    kiem_xml(svg)
    return svg
