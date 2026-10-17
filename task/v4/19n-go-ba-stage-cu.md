# 19n — Gỡ ba stage cũ và nhánh A4/A5 v3

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 19m · **Trạng thái:** chờ

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

- [ ] Import toàn bộ gói sau khi gỡ, không lỗi.
- [ ] Artifact v3 trong fixture vẫn qua A8, A10, bộ chấm và bộ nạp Pha B.
- [ ] Các giá trị `--stop-after` cũ báo lỗi rõ.
- [ ] Toàn bộ test qua; test của mã đã gỡ được gỡ cùng.
