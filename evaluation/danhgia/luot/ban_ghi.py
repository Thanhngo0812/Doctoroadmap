"""Bản ghi lượt `danh-gia-luot-1`. Thiếu trường thì lượt không được coi là xong."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

SCHEMA = "danh-gia-luot-1"
TEN_TEP = "ban-ghi-luot.json"
# trường bắt buộc và kiểu; `seed` và `k` có thể là null (biến thể không dùng)
TRUONG = {"schema": str, "ma_luot": str, "bien_the": str, "ma_sach": str, "doc_id": str, "sha256_pdf": str, "commit": str,
          "hash_cau_hinh": str, "mo_hinh": str, "transport": str, "seed": (int, type(None)), "k": (int, type(None)),
          "luot_nhieu": int, "ngay": str, "cau_hinh": dict, "tu_luot": (str, type(None)), "buoc": list, "ket_qua": dict, "xong": bool}
TRANG_THAI = ("cho", "dang_chay", "xong", "loi")


class CauHinhDoi(ValueError):
    """Chạy tiếp một lượt đã có bản ghi nhưng hash cấu hình khác: từ chối, không sửa gì."""


def hash_cau_hinh(thanh_phan: dict) -> str:
    return hashlib.sha256(json.dumps(thanh_phan, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def moi(*, ma_luot, bien_the, ma_sach, doc_id, sha256_pdf, commit, mo_hinh, transport, seed, k, luot_nhieu, ngay, cau_hinh,
        tu_luot, ten_buoc):
    """Bản ghi mới: mọi bước ở trạng thái `cho`. Hash cấu hình gồm mọi thứ làm đổi kết quả (kể cả commit và hash của lượt nguồn)."""
    thanh_phan = {"bien_the": bien_the, "doc_id": doc_id, "sha256_pdf": sha256_pdf, "commit": commit, "mo_hinh": mo_hinh,
                  "transport": transport, "seed": seed, "k": k, "luot_nhieu": luot_nhieu, "cau_hinh": cau_hinh,
                  "tu_luot": tu_luot, "buoc": list(ten_buoc)}
    return {"schema": SCHEMA, "ma_luot": ma_luot, "bien_the": bien_the, "ma_sach": ma_sach, "doc_id": doc_id,
            "sha256_pdf": sha256_pdf, "commit": commit, "hash_cau_hinh": hash_cau_hinh(thanh_phan), "mo_hinh": mo_hinh,
            "transport": transport, "seed": seed, "k": k, "luot_nhieu": luot_nhieu, "ngay": ngay, "cau_hinh": cau_hinh,
            "tu_luot": tu_luot,
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
    for chi_so, buoc in enumerate(ban_ghi.get("buoc") or []):
        if not isinstance(buoc, dict) or buoc.get("trang_thai") not in TRANG_THAI or not buoc.get("ten"):
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
    tam.replace(duong)
