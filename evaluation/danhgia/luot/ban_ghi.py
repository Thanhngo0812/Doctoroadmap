"""Bản ghi lượt `danh-gia-luot-1`. Thiếu trường thì lượt không được coi là xong.

DG-18a: thêm `sha256_giao_thuc` (str hay null) và `tap`; bản ghi cũ thiếu hai trường này coi như null / tập phát triển."""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

SCHEMA = "danh-gia-luot-1"
TEN_TEP = "ban-ghi-luot.json"
_SO_LAN_THU_DOI_TEN = 8
# trường bắt buộc và kiểu; `seed` và `k` có thể là null (biến thể không dùng)
TRUONG = {"schema": str, "ma_luot": str, "bien_the": str, "ma_sach": str, "doc_id": str, "sha256_pdf": str, "commit": str,
          "hash_cau_hinh": str, "mo_hinh": str, "transport": str, "seed": (int, type(None)), "k": (int, type(None)),
          "luot_nhieu": int, "ngay": str, "cau_hinh": dict, "tu_luot": (str, type(None)), "buoc": list, "ket_qua": dict, "xong": bool}
TRANG_THAI = ("cho", "dang_chay", "xong", "loi")   # cộng `tu_choi_<mã>` khi sản phẩm từ chối cuốn (DG-08b)


class TuChoi(Exception):
    """Sản phẩm từ chối cuốn (`BuildRejected`): không phải lỗi chạy. `ma` là mã từ chối của sản phẩm (`chu_loi`, `ban_quet`, ...)."""

    def __init__(self, ma: str, ly_do: str):
        super().__init__(ly_do)
        self.ma, self.ly_do = ma, ly_do


class CauHinhDoi(ValueError):
    """Chạy tiếp một lượt đã có bản ghi nhưng hash cấu hình khác: từ chối, không sửa gì."""


def hash_cau_hinh(thanh_phan: dict) -> str:
    return hashlib.sha256(json.dumps(thanh_phan, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def thanh_phan(*, bien_the, doc_id, sha256_pdf, commit, mo_hinh, transport, seed, k, luot_nhieu, cau_hinh, tu_luot, ten_buoc,
               sha256_giao_thuc=None):
    """Mọi thứ làm đổi kết quả của lượt; hash cấu hình là băm của đúng dict này. Test đổi từng trường để chứng minh hash đổi theo.

    `sha256_giao_thuc` chỉ vào thành phần khi có (lượt tập thử, hay tập phát triển có khai giao thức): đổi giao thức là đổi hash cấu hình,
    còn lượt không có giao thức giữ nguyên hash như trước DG-18a."""
    tp = {"bien_the": bien_the, "doc_id": doc_id, "sha256_pdf": sha256_pdf, "commit": commit, "mo_hinh": mo_hinh,
          "transport": transport, "seed": seed, "k": k, "luot_nhieu": luot_nhieu, "cau_hinh": cau_hinh,
          "tu_luot": tu_luot, "buoc": list(ten_buoc)}
    if sha256_giao_thuc is not None:
        tp["sha256_giao_thuc"] = sha256_giao_thuc
    return tp


def moi(*, ma_luot, bien_the, ma_sach, doc_id, sha256_pdf, commit, mo_hinh, transport, seed, k, luot_nhieu, ngay, cau_hinh,
        tu_luot, ten_buoc, sha256_giao_thuc=None, tap=None):
    """Bản ghi mới: mọi bước ở trạng thái `cho`. Hash cấu hình gồm mọi thứ làm đổi kết quả (kể cả commit và hash của lượt nguồn)."""
    tp = thanh_phan(bien_the=bien_the, doc_id=doc_id, sha256_pdf=sha256_pdf, commit=commit, mo_hinh=mo_hinh, transport=transport,
                    seed=seed, k=k, luot_nhieu=luot_nhieu, cau_hinh=cau_hinh, tu_luot=tu_luot, ten_buoc=ten_buoc,
                    sha256_giao_thuc=sha256_giao_thuc)
    return {"schema": SCHEMA, "ma_luot": ma_luot, "bien_the": bien_the, "ma_sach": ma_sach, "doc_id": doc_id,
            "sha256_pdf": sha256_pdf, "commit": commit, "hash_cau_hinh": hash_cau_hinh(tp), "mo_hinh": mo_hinh,
            "transport": transport, "seed": seed, "k": k, "luot_nhieu": luot_nhieu, "ngay": ngay, "cau_hinh": cau_hinh,
            "tu_luot": tu_luot, "sha256_giao_thuc": sha256_giao_thuc, "tap": tap,
            "buoc": [{"ten": ten, "trang_thai": "cho", "bat_dau": None, "ket_thuc": None, "giay": None, "ghi_chu": None}
                     for ten in ten_buoc],
            "ket_qua": {}, "xong": False}


def kiem(ban_ghi) -> list[str]:
    """Danh sách lỗi; rỗng nghĩa là bản ghi đủ trường, đúng kiểu và các bước nhất quán."""
    if not isinstance(ban_ghi, dict):
        return ["bản ghi không phải đối tượng JSON"]
    loi = []
    for truong, kieu in TRUONG.items():
        if truong not in ban_ghi:
            loi.append(f"thiếu trường {truong}")
        elif not isinstance(ban_ghi[truong], kieu) or (kieu is int and isinstance(ban_ghi[truong], bool)):
            loi.append(f"trường {truong}: sai kiểu")
    if ban_ghi.get("schema") not in (None, SCHEMA) and "schema" in ban_ghi:
        loi.append(f"schema phải là {SCHEMA}")
    # DG-18a: bản ghi cũ thiếu hai trường này vẫn đọc được (coi như null); lượt tập thử bắt buộc có SHA giao thức dạng 64 hex
    sha = ban_ghi.get("sha256_giao_thuc")
    if sha is not None and not (isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha)):
        loi.append("trường sha256_giao_thuc: phải là chuỗi 64 ký tự hex hay null")
    if ban_ghi.get("tap") not in (None, "phat_trien", "thu"):
        loi.append("trường tap: phải là phat_trien, thu hay thiếu")
    if ban_ghi.get("tap") == "thu" and sha is None:
        loi.append("lượt tập thử thiếu sha256_giao_thuc (lượt không mang SHA giao thức đăng ký trước)")
    for chi_so, buoc in enumerate(ban_ghi.get("buoc") or []):
        if not isinstance(buoc, dict) or not buoc.get("ten") or not (
                buoc.get("trang_thai") in TRANG_THAI or str(buoc.get("trang_thai")).startswith("tu_choi_")):
            loi.append(f"buoc[{chi_so}]: thiếu tên hay trạng thái không hợp lệ")
    return loi


def da_xong(ban_ghi) -> bool:
    """Xong = đủ trường, mọi bước `xong`, và cờ `xong` đã bật. Thiếu bất kỳ điều nào thì chưa xong."""
    return (not kiem(ban_ghi) and ban_ghi["xong"] is True and bool(ban_ghi["buoc"])
            and all(b["trang_thai"] == "xong" for b in ban_ghi["buoc"]))


def doc(thu_muc) -> dict | None:
    duong = Path(thu_muc) / TEN_TEP
    return json.loads(duong.read_text(encoding="utf-8")) if duong.exists() else None


def ghi(thu_muc, ban_ghi) -> None:
    duong = Path(thu_muc) / TEN_TEP
    tam = duong.with_suffix(".tmp")
    tam.write_text(json.dumps(ban_ghi, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # Windows báo WinError 5 khi trình quét còn giữ tệp vừa ghi; thử lại một lúc rồi mới chịu lỗi.
    for lan in range(_SO_LAN_THU_DOI_TEN):
        try:
            tam.replace(duong)
            return
        except PermissionError:
            if lan == _SO_LAN_THU_DOI_TEN - 1:
                raise
            time.sleep(0.1 * (lan + 1))
