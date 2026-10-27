from pathlib import Path

import copy
import unicodedata



def tao_pdf(duong_dan: Path, trang: list[str]) -> Path:
    """PDF nhỏ chỉ có chữ ASCII (phông Helvetica), mỗi phần tử là văn bản một trang."""
    doi_tuong: list[bytes] = []
    so_trang = len(trang)
    ids_trang = [3 + 2 * i for i in range(so_trang)]
    doi_tuong.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{i} 0 R" for i in ids_trang)
    doi_tuong.append(f"<< /Type /Pages /Kids [{kids}] /Count {so_trang} >>".encode())
    font_id = 3 + 2 * so_trang
    for i, van_ban in enumerate(trang):
        noi_dung = "BT /F1 11 Tf 40 760 Td 14 TL " + " ".join(
            f"({dong.replace(chr(92), '').replace('(', '').replace(')', '')}) '" for dong in van_ban.split("\n")
        ) + " ET"
        doi_tuong.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {ids_trang[i] + 1} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>".encode()
        )
        doi_tuong.append(f"<< /Length {len(noi_dung)} >>\nstream\n{noi_dung}\nendstream".encode())
    doi_tuong.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(doi_tuong, start=1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(doi_tuong) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(doi_tuong) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    duong_dan.write_bytes(bytes(out))
    return duong_dan


MANIFEST = {
    "schema": "danh-gia-sach-1",
    "ma_sach": "dev-test",
    "chu_de": "toan",
    "tap": "phat_trien",
    "pdf_sha256": "0" * 64,
    "so_trang": 6,
    "quyen": "da_xac_nhan",
    "chuong": [
        {"ma": "c10", "so": "10", "ten": "Xác suất", "trang_dau": 1, "trang_cuoi": 3, "loai": "noi_dung"},
        {"ma": "c11", "so": "11", "ten": "Biến ngẫu nhiên", "trang_dau": 4, "trang_cuoi": 5, "loai": "noi_dung"},
        {"ma": "c12", "so": "12", "ten": "Không bốc", "trang_dau": 6, "trang_cuoi": 6, "loai": "noi_dung"},
    ],
    "boc": {"seed": 1, "n_trang_toi_thieu": 1, "chuong": ["c10", "c11"]},
}




TRANG = {
    1: "Quy luật số lớn phát biểu rằng trung bình mẫu hội tụ về kỳ vọng.\nTỷ lệ thành\ncông được ước lượng bằng tần suất.",
    2: "Xác suất có điều kiện của A khi biết B là P(A|B) = P(AB)/P(B).",
    3: "Biến cố độc lập là hai biến cố mà việc xảy ra của biến cố này không ảnh hưởng đến xác suất của biến cố kia.",
    4: "Biến ngẫu nhiên rời rạc nhận các giá trị đếm được.",
    5: "Kỳ vọng của biến ngẫu nhiên là giá trị trung bình có trọng số.",
}




def nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


def khai_niem(ma, chuong, ten, trang_thai="day_o_day", trang=1, cau="", ten_khac=(), khong_chac=False, ghi_chu=""):
    return {
        "ma": ma, "chuong": chuong, "ten": ten, "ten_khac": list(ten_khac), "trang_thai": trang_thai,
        "dinh_nghia": {"trang": trang, "cau": cau}, "khong_chac": khong_chac, "ghi_chu": ghi_chu,
    }


def tho(nguoi, *muc, ma_sach="dev-test"):
    return {"schema": "danh-gia-g3-1", "ma_sach": ma_sach, "nguoi_gan": nguoi, "phien_ban_huong_dan": "g3-1",
            "khai_niem": list(muc), "tranh_chap": []}


KHO = {
    "schema": "danh-gia-g3-1", "ma_sach": "dev-test", "nguoi_gan": "hoi-y", "phien_ban_huong_dan": "g3-1",
    "chuong": ["c10", "c11"], "tranh_chap": [], "loai": [],
    "khai_niem": [
        {"ma": "G-dev-test-001", "chuong": "c10", "ten": "Tổng thể", "ten_khac": ["đám đông"], "trang_thai": "day_o_day",
         "dinh_nghia": {"trang": 1, "cau": "Tổng thể là tập hợp các phần tử."}, "khong_chac": False, "ghi_chu": ""},
        {"ma": "G-dev-test-002", "chuong": "c10", "ten": "Mẫu", "ten_khac": [], "trang_thai": "day_o_day",
         "dinh_nghia": {"trang": 1, "cau": "Mẫu là tập con của tổng thể."}, "khong_chac": False, "ghi_chu": ""},
        {"ma": "G-dev-test-003", "chuong": "c10", "ten": "Kích thước mẫu", "ten_khac": [], "trang_thai": "chi_nhac",
         "dinh_nghia": {"trang": 1, "cau": ""}, "khong_chac": False, "ghi_chu": ""},
        {"ma": "G-dev-test-004", "chuong": "c10", "ten": "Mẫu ngẫu nhiên", "ten_khac": [], "trang_thai": "day_qua_vi_du",
         "dinh_nghia": {"trang": 2, "cau": "Mẫu ngẫu nhiên là mẫu đại diện."}, "khong_chac": False, "ghi_chu": ""},
        {"ma": "G-dev-test-005", "chuong": "c11", "ten": "Phương sai", "ten_khac": [], "trang_thai": "day_o_day",
         "dinh_nghia": {"trang": 4, "cau": "Phương sai đo độ phân tán."}, "khong_chac": False, "ghi_chu": ""},
        {"ma": "G-dev-test-006", "chuong": "c11", "ten": "Kỳ vọng", "ten_khac": [], "trang_thai": "kien_thuc_nen",
         "dinh_nghia": {"trang": None, "cau": ""}, "khong_chac": False, "ghi_chu": ""},
    ],
}


def ma_khai_niem(so: int) -> str:
    return f"G-dev-test-{so:03d}"


def canh(ma, chuong, dich, nguon, loai="van_ban", trang=1, cau="Tổng thể là tập hợp các phần tử.", khong_chac=False):
    """Một quan hệ thô của danh-gia-g4-1; dich và nguon là số thứ tự khái niệm kho, hoặc nguon là dict {"ngoai": ...}."""
    return {
        "ma": ma, "chuong": chuong, "dich": ma_khai_niem(dich),
        "nguon": nguon if isinstance(nguon, dict) else ma_khai_niem(nguon), "loai": loai,
        "bang_chung": {"trang": trang if loai == "van_ban" else None, "cau": cau if loai == "van_ban" else ""},
        "khong_chac": khong_chac, "ghi_chu": "",
    }


def tho_g4(nguoi, kho_sha, *quan_he, ma_sach="dev-test"):
    return {"schema": "danh-gia-g4-1", "ma_sach": ma_sach, "nguoi_gan": nguoi, "kho_chot_sha256": kho_sha, "quan_he": list(quan_he)}
