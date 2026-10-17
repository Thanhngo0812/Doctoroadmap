# 19n — Gỡ ba stage cũ và nhánh A4/A5 v3

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 19m · **Trạng thái:** xong 2026-10-17 — Claude kiểm đạt, T10a đã sửa, commit chung với 19o

## Cần làm

**Gỡ:**
- stage provenance, stage `teaching` (C8) và stage danh tính;
- nhánh A4/A5 v3 có gọi mô hình;
- các giá trị `--stop-after provenance|teaching|identity` và cờ `--identity-review`.

**Giữ đường canonical chỉ lớp tên** (`--names-only`, `--prepare`) cho D-01 đã đóng băng.

**Phải giữ, vì mã khác đang dùng.** Chuyển sang module trung tính nếu module chứa chúng bị gỡ:
- hàm kiểm câu trích nguyên văn (Pha B dùng). Cụ thể là `quote_is_verbatim`: `phase_b/common.py` import nó từ `domain.provenance`. Nếu chuyển hàm,
  sửa dòng import đó trong cùng commit. Tệp bàn giao Pha B ngày 2026-10-17 đã báo trước việc này;
- schema xác minh và bộ nạp tệp duyệt (canonical dùng);
- miền danh tính (đề cử và duyệt ở canonical dùng);
- lõi neo (canonical dùng).

**Tài liệu (Claude, cùng đợt commit):** khuôn lệnh T10a trong `CONTEXT.md` còn dùng `--stop-after identity` và `--identity-review`. Sau khi gỡ, ghi rõ
khuôn này chỉ chạy được với mã trước 19n.

**Hợp đồng đọc artifact cũ:** A8, A10, bộ chấm và Pha B vẫn đọc được artifact v3 có `identity_map`.

## Nghiệm thu

- [x] Import toàn bộ gói sau khi gỡ, không lỗi.
- [x] Artifact v3 trong fixture vẫn qua A8, A10, bộ chấm và bộ nạp Pha B.
- [x] Các giá trị `--stop-after` cũ báo lỗi rõ.
- [x] Toàn bộ test qua; test của mã đã gỡ được gỡ cùng.

## Bàn giao nhân viên

Đã chuyển hàm quote sang `domain/quotes.py` và sửa import Pha B; schema/review
sang `application/identity_review.py`. Miền danh tính và AnchorCore giữ lại.
Helper ngân sách/kho thử tách sang `scripts/doc-lo-trinh/evaluation_runtime.py`.
Toàn kho **1.535 test qua**, thêm **1 ca bộ chấm v3 qua riêng**.
Chi tiết, hash đóng băng và phạm vi commit:
[báo cáo 19n–19o](../../report/v4-19no-go-stage-va-tuy-chon-cu-2026-10-17.md).
`CONTEXT.md` để Claude cập nhật T10a như đã nhận, trước commit chung.

## Kiểm của Claude 2026-10-17 — đạt

- **Kho thật, dry-run, 0 USD, không ghi artifact:**
  - `roadmap --dry-run` doc-1 tái dùng mọi stage chuỗi gộp;
  - `--stop-after identity` bị từ chối ở bước đọc lệnh;
  - doc-2 (canonical v3) nhận lỗi "chạy lại A4";
  - `DOC2ROADMAP_UPSTREAM_CHAIN=v3` chỉ sinh cảnh báo nêu tên biến.
- **Hệ quả cần biết:** 19o bỏ các mục cấu hình nên băm cấu hình canonical đổi. Lần `a4` kế tiếp trên tài liệu cũ sẽ embed lại tên và dựng canonical
  mới. Payload không đổi (test đóng băng của nhân viên). `a4 --dry-run` doc-1 báo phần embedding "sẽ chạy", các phần còn lại "chưa biết".
- **Commit:** tách bỏ hai hunk Pha B trong `cli/main.py` (module của Pha B chưa được track) và các thay đổi A1/D-01 đang dở. Chạy toàn bộ test trên
  checkout sạch của commit.
