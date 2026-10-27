"""Fixture B5: sách thiên văn nhỏ, tự soạn (khác lĩnh vực các sách thử), chữ ASCII để dựng PDF thật bằng `tao_pdf`.

Phản hồi "đã ghi" là văn bản mô hình trả; không có lời gọi mạng nào trong các test dùng chúng.
"""
import hashlib
import json

TRANG = {
    1: "Chuong 1. Mat Troi\nMat Troi la ngoi sao gan Trai Dat nhat. Anh sang Mat Troi den Trai Dat sau tam phut.",
    2: "Quang pho la dai mau cua anh sang sau khi tan sac. Muon hieu quang pho phai biet Mat Troi phat ra anh sang.",
    3: "Chuong 2. Sao\nSao la khoi khi nong tu phat sang. Do sang cua sao phu thuoc vao nhiet do.",
    4: "Hang so Hubble la ty le giua toc do ra xa va khoang cach cua thien ha. Muon do hang so Hubble phai biet Quang pho.",
}


def manifest(sha="0" * 64):
    return {
        "schema": "danh-gia-sach-1", "ma_sach": "dev-thien-van", "chu_de": "thien_van", "tap": "phat_trien",
        "pdf_sha256": sha, "so_trang": 4, "quyen": "da_xac_nhan",
        "chuong": [
            {"ma": "c1", "so": "1", "ten": "Mat Troi", "trang_dau": 1, "trang_cuoi": 2, "loai": "noi_dung"},
            {"ma": "c2", "so": "2", "ten": "Sao", "trang_dau": 3, "trang_cuoi": 4, "loai": "noi_dung"},
        ],
    }


def sha256(duong):
    return hashlib.sha256(open(duong, "rb").read()).hexdigest()


C_MAT_TROI = "Mat Troi la ngoi sao gan Trai Dat nhat."
C_QUANG_PHO = "Quang pho la dai mau cua anh sang sau khi tan sac."
C_SAO = "Sao la khoi khi nong tu phat sang."
C_HUBBLE = "Hang so Hubble la ty le giua toc do ra xa va khoang cach cua thien ha."
C_PHU_THUOC = "Muon hieu quang pho phai biet Mat Troi phat ra anh sang."


def phan_hoi_a(**sua):
    """Phản hồi hợp lệ cho cả cuốn; `sua` ghi đè từng khoá cấp đỉnh."""
    du_lieu = {
        "khai_niem": [
            {"ten": "Mat Troi", "ten_khac": [], "trang": 1, "cau_dinh_nghia": C_MAT_TROI},
            {"ten": "Quang pho", "ten_khac": ["pho anh sang"], "trang": 2, "cau_dinh_nghia": C_QUANG_PHO},
            {"ten": "Sao", "ten_khac": [], "trang": 3, "cau_dinh_nghia": C_SAO},
            {"ten": "Hang so Hubble", "ten_khac": [], "trang": 4, "cau_dinh_nghia": C_HUBBLE},
        ],
        "quan_he": [
            {"nguon": "Mat Troi", "dich": "Quang pho", "trang": 2, "cau_bang_chung": C_PHU_THUOC},
            {"nguon": "Quang pho", "dich": "Hang so Hubble", "trang": 4,
             "cau_bang_chung": "Muon do hang so Hubble phai biet Quang pho."},
        ],
        "lo_trinh": {"day_hoc": ["Mat Troi", "Quang pho", "Sao", "Hang so Hubble"],
                     "module": [{"ten": "Anh sang", "khai_niem": ["Mat Troi", "Quang pho"]},
                                {"ten": "Vu tru", "khai_niem": ["Sao", "Hang so Hubble"]}]},
    }
    du_lieu.update(sua)
    return du_lieu


def van_ban_mo_hinh(du_lieu):
    return json.dumps(du_lieu, ensure_ascii=False)


def phan_hoi_http(text, *, ly_do="STOP", vao=100, ra=40, nghi=10):
    """Thân HTTP giống Gemini generateContent."""
    return json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": ly_do}],
                       "usageMetadata": {"promptTokenCount": vao, "candidatesTokenCount": ra,
                                         "thoughtsTokenCount": nghi,
                                         "totalTokenCount": vao + ra + nghi}}).encode()
