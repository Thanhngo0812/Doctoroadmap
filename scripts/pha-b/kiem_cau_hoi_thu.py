"""Kiểm định dạng bộ câu hỏi thử của trợ lý Pha B (vé SA-19). Chỉ dùng thư viện chuẩn.

Chạy:  python kiem_cau_hoi_thu.py --doc <doc_id> --thu-muc <thư mục làm việc> [--mot-phan]

Thư mục làm việc chứa:
  goi/<doc_id>/thong_tin.json, module.jsonl, khai_niem.jsonl, doan.jsonl   (nhận)
  goi/<doc_id>/cau_kiem.jsonl                                               (nhận, có thể không có)
  cau/<doc_id>.jsonl                                                        (trả: câu hỏi tự soạn)
  kiem/<doc_id>.jsonl                                                       (trả: điền câu kiểm, nếu có cau_kiem)

--mot-phan: đang làm dở; không báo lỗi thiếu chỉ tiêu, chỉ báo lỗi vượt chỉ tiêu.
Thoát mã 1 nếu có lỗi; mã 0 nếu đạt. Cảnh báo không làm hỏng, nhưng phải đọc.
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

LOAI = ("dinh_nghia", "tien_quyet", "so_sanh", "vi_du", "lo_trinh", "ngoai_tai_lieu", "nhieu_luot")
TRUONG = ("cau_id", "doc_id", "loai", "module_dang_mo", "luot_truoc", "cau_hoi", "van_phong",
          "khai_niem_ky_vong", "doan_tham_chieu", "tra_loi_duoc", "y_chinh", "kieu_ngoai", "da_tim",
          "chua_chac", "ghi_chu", "nguoi_tao")
MA_NOI_BO = re.compile(r"node_[0-9a-f]{6}|\bc_[0-9a-f]{6}|module_\d{3}")
CAU_HOI_TOI_DA = 300
Y_TOI_DA = 200
CHEP_TU = 10  # chuỗi ≥ 10 từ liền nhau trùng văn bản sách thì cảnh báo chép nguyên văn


def chuan(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def tu(text):
    return re.findall(r"[^\W_]+", text)


def doc_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


class Goi:
    def __init__(self, root, doc):
        base = root / "goi" / doc
        self.thong_tin = json.loads((base / "thong_tin.json").read_text(encoding="utf-8"))
        self.modules = {m["module_id"]: m for m in doc_jsonl(base / "module.jsonl")}
        self.khai_niem = {k["node_id"]: k for k in doc_jsonl(base / "khai_niem.jsonl")}
        self.doan = {d["chunk_id"]: d for d in doc_jsonl(base / "doan.jsonl")}
        kiem = base / "cau_kiem.jsonl"
        self.cau_kiem = {c["cau_id"]: c for c in doc_jsonl(kiem)} if kiem.exists() else {}
        self.chi_tieu = self.thong_tin["chi_tieu"]
        self.van_ban = [chuan(d["text"]) for d in self.doan.values()]
        self._ngram = None

    def ngram(self):
        if self._ngram is None:
            grams = set()
            for text in self.van_ban:
                words = tu(text)
                grams.update(" ".join(words[i:i + CHEP_TU]) for i in range(len(words) - CHEP_TU + 1))
            self._ngram = grams
        return self._ngram


def kiem_dong(r, goi, doc, loi, canh_bao, nhan):
    if not isinstance(r, dict):
        loi(f"{nhan}: không phải object JSON")
        return
    thieu = [k for k in TRUONG if k not in r]
    thua = [k for k in r if k not in TRUONG]
    if thieu or thua:
        loi(f"{nhan}: thiếu trường {thieu} / thừa trường {thua}")
        return
    if r["doc_id"] != doc:
        loi(f"{nhan}: doc_id phải là {doc}")
    loai = r["loai"]
    if loai not in LOAI:
        loi(f"{nhan}: loai lạ '{loai}'")
        return
    ngoai = loai == "ngoai_tai_lieu"
    if r["module_dang_mo"] not in goi.modules:
        loi(f"{nhan}: module_dang_mo '{r['module_dang_mo']}' không có trong goi/module.jsonl")
    cau = r["cau_hoi"]
    if not isinstance(cau, str) or not cau.strip():
        loi(f"{nhan}: cau_hoi rỗng")
    elif len(cau) > CAU_HOI_TOI_DA:
        loi(f"{nhan}: cau_hoi dài quá {CAU_HOI_TOI_DA} ký tự")
    elif MA_NOI_BO.search(cau):
        loi(f"{nhan}: cau_hoi chứa mã nội bộ (node_/c_/module_); người học không thấy mã này")
    truoc = r["luot_truoc"]
    if not isinstance(truoc, list) or not all(isinstance(x, str) and x.strip() for x in truoc):
        loi(f"{nhan}: luot_truoc phải là danh sách câu hỏi")
    elif loai == "nhieu_luot" and not 1 <= len(truoc) <= 2:
        loi(f"{nhan}: nhieu_luot cần 1–2 câu trong luot_truoc")
    elif loai != "nhieu_luot" and truoc:
        loi(f"{nhan}: chỉ nhieu_luot mới có luot_truoc")
    elif any(MA_NOI_BO.search(x) for x in truoc):
        loi(f"{nhan}: luot_truoc chứa mã nội bộ")
    if r["van_phong"] not in ("chuan", "than_mat"):
        loi(f"{nhan}: van_phong phải là 'chuan' hoặc 'than_mat'")
    kn = r["khai_niem_ky_vong"]
    if not isinstance(kn, list) or any(x not in goi.khai_niem for x in kn):
        loi(f"{nhan}: khai_niem_ky_vong có node_id không có trong goi/khai_niem.jsonl")
    elif ngoai and kn:
        loi(f"{nhan}: ngoai_tai_lieu phải để khai_niem_ky_vong = []")
    elif loai == "so_sanh" and not 2 <= len(kn) <= 3:
        loi(f"{nhan}: so_sanh cần 2–3 khái niệm")
    elif not ngoai and loai != "so_sanh" and not 1 <= len(kn) <= 3:
        loi(f"{nhan}: cần 1–3 khái niệm kỳ vọng")
    doan = r["doan_tham_chieu"]
    if not isinstance(doan, list) or any(x not in goi.doan for x in doan):
        loi(f"{nhan}: doan_tham_chieu có chunk_id không có trong goi/doan.jsonl")
        doan = []
    elif ngoai and doan:
        loi(f"{nhan}: ngoai_tai_lieu phải để doan_tham_chieu = []")
    elif not ngoai and not 1 <= len(doan) <= 3:
        loi(f"{nhan}: cần 1–3 đoạn tham chiếu")
    if not isinstance(r["tra_loi_duoc"], bool):
        loi(f"{nhan}: tra_loi_duoc phải là true/false")
    elif r["tra_loi_duoc"] == ngoai:
        loi(f"{nhan}: tra_loi_duoc phải là {'false' if ngoai else 'true'} với loai {loai}")
    y = r["y_chinh"]
    if not isinstance(y, list):
        loi(f"{nhan}: y_chinh phải là danh sách")
    elif ngoai and y:
        loi(f"{nhan}: ngoai_tai_lieu phải để y_chinh = []")
    elif not ngoai:
        if not 1 <= len(y) <= 3:
            loi(f"{nhan}: cần 1–3 ý chính")
        for item in y:
            if not isinstance(item, dict) or set(item) != {"y", "doan"}:
                loi(f"{nhan}: mỗi ý chính là {{\"y\": …, \"doan\": …}}")
            elif not isinstance(item["y"], str) or not 0 < len(item["y"].strip()) <= Y_TOI_DA:
                loi(f"{nhan}: ý chính rỗng hoặc dài quá {Y_TOI_DA} ký tự")
            elif item["doan"] not in doan:
                loi(f"{nhan}: ý chính trỏ tới đoạn '{item['doan']}' không nằm trong doan_tham_chieu")
    kieu = r["kieu_ngoai"]
    if ngoai and kieu not in ("gan_chu_de", "lac_de"):
        loi(f"{nhan}: ngoai_tai_lieu cần kieu_ngoai là 'gan_chu_de' hoặc 'lac_de'")
    elif not ngoai and kieu is not None:
        loi(f"{nhan}: kieu_ngoai chỉ dùng cho ngoai_tai_lieu, còn lại để null")
    tim = r["da_tim"]
    if not isinstance(tim, list) or not all(isinstance(x, str) and x.strip() for x in tim):
        loi(f"{nhan}: da_tim phải là danh sách từ")
    elif ngoai and len(tim) < 2:
        loi(f"{nhan}: ngoai_tai_lieu cần ít nhất 2 từ đã tìm trong da_tim")
    elif not ngoai and tim:
        loi(f"{nhan}: da_tim chỉ dùng cho ngoai_tai_lieu")
    elif ngoai:
        for term in tim:
            if any(chuan(term) in text for text in goi.van_ban):
                canh_bao(f"{nhan}: từ đã tìm '{term}' CÓ trong tài liệu — xem lại câu có thật ngoài tài liệu không")
    if not isinstance(r["chua_chac"], bool):
        loi(f"{nhan}: chua_chac phải là true/false")
    elif r["chua_chac"] and not str(r["ghi_chu"]).strip():
        loi(f"{nhan}: chua_chac = true thì ghi_chu phải nói chỗ chưa chắc")
    if not isinstance(r["nguoi_tao"], str) or not r["nguoi_tao"].strip():
        loi(f"{nhan}: nguoi_tao rỗng")
    if isinstance(cau, str):
        words = tu(chuan(cau))
        grams = goi.ngram()
        if any(" ".join(words[i:i + CHEP_TU]) in grams for i in range(len(words) - CHEP_TU + 1)):
            canh_bao(f"{nhan}: câu hỏi chép nguyên văn ≥ {CHEP_TU} từ của sách — viết lại bằng lời người học")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--thu-muc", default=".")
    ap.add_argument("--mot-phan", action="store_true")
    args = ap.parse_args()
    root = Path(args.thu_muc)
    goi = Goi(root, args.doc)
    errors, warnings = [], []
    cau_path = root / "cau" / f"{args.doc}.jsonl"
    rows = []
    if not cau_path.exists():
        print(f"chưa có {cau_path.as_posix()}; tạo tệp này để ghi câu")
    else:
        with open(cau_path, encoding="utf-8") as f:
            for no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    rows.append((no, json.loads(line)))
                except json.JSONDecodeError as e:
                    errors.append(f"cau dòng {no}: JSON hỏng ({e.msg})")
    seen_id, seen_text, counts = set(), {}, Counter()
    ngoai_gan, than_mat, ten_trong_cau_cuoi, nhieu = 0, 0, 0, 0
    quan_he = Counter()
    for no, r in rows:
        nhan = f"cau dòng {no}"
        kiem_dong(r, goi, args.doc, errors.append, warnings.append, nhan)
        if not isinstance(r, dict) or any(k not in r for k in TRUONG) or r.get("loai") not in LOAI:
            continue
        if not re.fullmatch(re.escape(args.doc) + r"-q\d{3}", str(r["cau_id"])):
            errors.append(f"{nhan}: cau_id phải có dạng {args.doc}-q001")
        if r["cau_id"] in seen_id:
            errors.append(f"{nhan}: cau_id '{r['cau_id']}' lặp")
        seen_id.add(r["cau_id"])
        if isinstance(r["luot_truoc"], list):
            key = chuan(" | ".join([*map(str, r["luot_truoc"]), str(r["cau_hoi"])]))
            if key in seen_text:
                errors.append(f"{nhan}: câu hỏi trùng {seen_text[key]}")
            seen_text.setdefault(key, r["cau_id"])
        counts[r["loai"]] += 1
        ngoai_gan += r["loai"] == "ngoai_tai_lieu" and r["kieu_ngoai"] == "gan_chu_de"
        than_mat += r["van_phong"] == "than_mat"
        if r["loai"] == "nhieu_luot":
            nhieu += 1
            names = [chuan(goi.khai_niem[n]["ten"]) for n in r["khai_niem_ky_vong"] if n in goi.khai_niem]
            ten_trong_cau_cuoi += any(n and n in chuan(r["cau_hoi"]) for n in names)
        if r["loai"] != "ngoai_tai_lieu" and r["module_dang_mo"] in goi.modules:
            mo = goi.modules[r["module_dang_mo"]]["so_thu_tu"]
            for n in r["khai_niem_ky_vong"]:
                m = goi.khai_niem.get(n, {}).get("module_id")
                if m in goi.modules:
                    o = goi.modules[m]["so_thu_tu"]
                    quan_he["cung_module" if o == mo else "module_sau" if o > mo else "module_truoc"] += 1
    for loai in LOAI:
        need, have = goi.chi_tieu.get(loai, 0), counts[loai]
        if have > need:
            errors.append(f"chỉ tiêu: {loai} có {have}, vượt {need}")
        elif have < need and not args.mot_phan:
            errors.append(f"chỉ tiêu: {loai} có {have}, còn thiếu {need - have}")
    if not args.mot_phan:
        if counts["ngoai_tai_lieu"] and ngoai_gan * 2 < counts["ngoai_tai_lieu"]:
            errors.append(f"ngoai_tai_lieu: cần ít nhất một nửa là gan_chu_de, hiện {ngoai_gan}/{counts['ngoai_tai_lieu']}")
        total = sum(counts.values())
        if total and than_mat < 0.15 * total:
            warnings.append(f"van_phong: chỉ {than_mat}/{total} câu than_mat, đích ≥ 15%")
        if nhieu and ten_trong_cau_cuoi * 2 > nhieu:
            warnings.append(f"nhieu_luot: {ten_trong_cau_cuoi}/{nhieu} câu cuối nêu thẳng tên khái niệm, đích ≤ một nửa")
        lien = sum(quan_he.values())
        if lien and quan_he["module_sau"] < 0.15 * lien:
            warnings.append(f"module_dang_mo: chỉ {quan_he['module_sau']}/{lien} khái niệm nằm ở module sau, đích ≥ 15%")
    if goi.cau_kiem:
        kiem_path = root / "kiem" / f"{args.doc}.jsonl"
        kiem_rows = doc_jsonl(kiem_path) if kiem_path.exists() else []
        got = {}
        for i, r in enumerate(kiem_rows, 1):
            nhan = f"kiem dòng {i}"
            kiem_dong(r, goi, args.doc, errors.append, warnings.append, nhan)
            cid = r.get("cau_id") if isinstance(r, dict) else None
            given = goi.cau_kiem.get(cid)
            if given is None:
                errors.append(f"{nhan}: cau_id '{cid}' không có trong goi/cau_kiem.jsonl")
                continue
            if cid in got:
                errors.append(f"{nhan}: cau_id '{cid}' lặp")
            got[cid] = r
            for k in ("loai", "module_dang_mo", "luot_truoc", "cau_hoi"):
                if r.get(k) != given.get(k):
                    errors.append(f"{nhan}: không được sửa trường {k} của câu kiểm")
        missing = [cid for cid in goi.cau_kiem if cid not in got]
        if missing and not args.mot_phan:
            errors.append(f"kiem: còn {len(missing)} câu kiểm chưa điền")
    print(f"{args.doc}: {sum(counts.values())}/{sum(goi.chi_tieu.values())} câu; "
          + ", ".join(f"{k} {counts[k]}/{goi.chi_tieu.get(k, 0)}" for k in LOAI))
    print(f"quan hệ khái niệm với module đang mở: {dict(quan_he)}; thân mật {than_mat}; ngoài tài liệu gần chủ đề {ngoai_gan}")
    for w in warnings:
        print("CẢNH BÁO", w)
    for e in errors:
        print("LỖI", e)
    print("ĐẠT" if not errors else f"CHƯA ĐẠT: {len(errors)} lỗi")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
