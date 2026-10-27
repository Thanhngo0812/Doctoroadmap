"""Gói nháp G1/G2 cho người làm nháp (Codex): bảng dòng theo trang có mã dòng, hướng dẫn ngắn, validator chạy bằng thư viện chuẩn.

Bảng dòng do `danhgia.xuat.bang_dong` dựng bằng bộ đọc nhẹ của pipeline (cùng mã dòng với đầu ra A1); gói này chỉ nhận bảng đó.
"""
import hashlib
import json
import shutil
from pathlib import Path

from danhgia.g1g2 import kiem_cay

HUONG_DAN = """\
# Hướng dẫn làm nháp G1 (cây mục) và G2 (vai trò vùng)

Việc của bạn: đọc cuốn giáo trình qua bảng dòng `dong/<sách>.jsonl` và trả `cay-muc/<sách>.jsonl`, mỗi tiêu đề một dòng JSON, theo thứ tự đọc.
Đây là **bản nháp**: một sinh viên sẽ duyệt lại từng mục. Hãy làm cẩn thận như thể không ai duyệt; đừng cố ý để sót.

## Đầu vào
- `dong/<sách>.jsonl`: mỗi dòng chữ của cả cuốn, có `id` (`p0031-l002` = trang PDF 31, dòng 2), `trang`, `text`, `bbox` ([trái, trên, phải, dưới], toạ độ PDF gốc dưới-trái), `co_chu` (cỡ chữ), `dam` (true nếu phần lớn chữ đậm). Cỡ chữ và chữ đậm giúp nhận tiêu đề.
- `muc_luc_dien_tu/<sách>.json`: bookmark của PDF nếu có (có thể rỗng hoặc sai).
- Trang PDF được đếm từ 1, không phải số in trên sách.

## Đầu ra: một tiêu đề một dòng JSON
{"sach": "<sách>", "id": "h010", "dong": ["p0031-l002", "p0031-l003"], "text": "CHƯƠNG 3. NHỊP ĐIỆU", "cap": 1, "cha": null, "vung": "noi_dung", "vai_tro": "noi_dung", "ghi_chu": ""}

| trường | luật |
|---|---|
| `id` | `h` cộng số, không trùng, tăng dần theo thứ tự đọc |
| `dong` | ít nhất một mã dòng có thật, theo thứ tự đọc; một mã dòng không thuộc hai tiêu đề. Tiêu đề nhiều dòng ghi đủ các mã dòng |
| `text` | chữ của tiêu đề, không rỗng |
| `cap` | số nguyên 1–6, là độ sâu trong cây logic của sách (không theo cỡ chữ). Có "Phần" thì Phần là cấp 1, Chương là cấp 2; không có thì Chương là cấp 1. "Lời nói đầu", "Mục lục", "Tài liệu tham khảo", "Phụ lục" luôn là cấp 1 |
| `cha` | null khi `cap` là 1; nếu không, là `id` của tiêu đề đang mở ở cấp liền trên, trong cùng nhánh logic. Mục `mo_dau` và `hanh_chinh` là nhánh riêng, không đóng nhánh nội dung đang mở |
| `vai_tro` | vai trò vùng G2 của mục, một trong sáu giá trị dưới đây. Có ở **mọi** tiêu đề |
| `vung` | = `vai_tro` nếu `cap` là 1; null nếu cấp khác |
| `ghi_chu` | `""`, `"nghi"` khi không chắc, hoặc lời ngắn |

## Sáu vai trò
| `vai_tro` | dùng cho |
|---|---|
| `mo_dau` | lời nói đầu, lời giới thiệu, mục lục, danh mục từ viết tắt |
| `noi_dung` | phần, chương, mục dạy nội dung |
| `bai_tap` | bài tập, câu hỏi ôn tập, đề thi, đứng riêng hoặc ở cuối chương |
| `de_cuong` | đề cương, mục tiêu học phần, kế hoạch giảng dạy |
| `hanh_chinh` | quyết định ban hành, thông tin tác giả, trang hành chính có tiêu đề |
| `cuoi_sach` | tài liệu tham khảo, phụ lục, chỉ mục, đáp số |

Mục con thường cùng vai trò với mục cha; ghi vai trò khác khi mục con thật sự thuộc loại khác (ví dụ "Câu hỏi ôn tập" cuối một chương nội dung là `bai_tap`).

## Cái không phải tiêu đề
Đầu trang, chân trang, số trang; chữ trong hình, bảng, công thức; chú thích hình; tên sách, tác giả trên bìa; mục liệt kê "1.", "a)" chỉ là ý trong đoạn.

## Kiểm trước khi trả
`python kiem_cay.py --sach <sách> --thu-muc .` (chỉ cần Python, không cần gói nào). Phải in `ĐẠT`. Không sửa `dong/` để qua kiểm.
"""


def bookmark(pdf: str | Path) -> list[dict]:
    import pypdfium2

    doc = pypdfium2.PdfDocument(Path(pdf).read_bytes())
    try:
        ket = []
        for muc in doc.get_toc():
            dich = muc.get_dest()
            chi_so = dich.get_index() if dich else None
            ket.append({"text": muc.get_title(), "cap": muc.level + 1, "trang": None if chi_so is None else chi_so + 1})
        return ket
    finally:
        doc.close()


def ghi_jsonl(duong, ds):
    Path(duong).parent.mkdir(parents=True, exist_ok=True)
    Path(duong).write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in ds), encoding="utf-8")


def sinh_goi(manifest: dict, pdf: str | Path, ra: str | Path, dong: list[dict]) -> Path:
    """`dong`: bảng dòng dựng bởi `danhgia.xuat.bang_dong` (seam xuất); gói này không đọc PDF để lấy dòng."""
    ma = manifest["ma_sach"]
    sha = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    if sha != manifest["pdf_sha256"]:
        raise ValueError("sha256 của PDF không khớp manifest")
    ra = Path(ra)
    ghi_jsonl(ra / "dong" / f"{ma}.jsonl", dong)
    (ra / "cay-muc").mkdir(parents=True, exist_ok=True)
    (ra / "chon-trang-mau").mkdir(exist_ok=True)
    (ra / "chon-trang-mau" / f"{ma}.json").write_text('{"trang": []}\n', encoding="utf-8")  # D-02 đòi tệp này; G1 không có trang L2
    (ra / "muc_luc_dien_tu").mkdir(exist_ok=True)
    (ra / "muc_luc_dien_tu" / f"{ma}.json").write_text(json.dumps(bookmark(pdf), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    shutil.copyfile(Path(kiem_cay.__file__), ra / "kiem_cay.py")
    (ra / "HUONG-DAN.md").write_text(HUONG_DAN, encoding="utf-8")
    thong_tin = {"ma_sach": ma, "so_trang": len({d["trang"] for d in dong}), "so_dong": len(dong),
                 "sha256_dong": hashlib.sha256((ra / "dong" / f"{ma}.jsonl").read_bytes()).hexdigest()}
    (ra / "thong-tin.json").write_text(json.dumps(thong_tin, indent=1) + "\n", encoding="utf-8")
    return ra
