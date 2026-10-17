# 19e — Test tích hợp: Pha B nạp đồ thị chuỗi gộp

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), Testing Decisions mục 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã cài và kiểm chứng 2026-10-17

## Vì sao

Test của vé 17c mới phủ A10 và bộ chấm. Pha B đọc đồ thị lộ trình, nên cần một test chắc rằng đồ thị chuỗi gộp nạp được qua bộ nạp của Pha B. Nghiên
cứu đã thử tay với doc-1, xstk và doc-4.

## Cần làm

- Một test tích hợp nạp đồ thị `stages` của chuỗi gộp, sinh từ fixture tài liệu thật với mô hình giả, qua bộ nạp đồ thị của Pha B.
- **Không sửa mã Pha B.** Nếu test lộ lỗi tương thích thì báo lại, để chuyển cho phiên Pha B.

## Nghiệm thu

- [x] Bộ nạp Pha B nạp được đồ thị chuỗi gộp. Node có câu neo và chunk dạy đúng dạng mà bài giảng đọc.
- [x] Một artifact v3 có `identity_map` trong fixture vẫn nạp được.
- [x] Toàn bộ test qua.

**Kiểm chứng 2026-10-17:** đồ thị `stages` từ fixture tài liệu thật đi qua bộ nạp Pha B và dựng ngữ cảnh bài giảng cho từng node được dạy; kiểm câu neo, chunk dạy và trích dẫn. Nhánh v3 có `identity_map` không rỗng. Không sửa nguồn Pha B. Chi tiết ở [báo cáo 19d–19e](../../report/v4-19de-mac-dinh-va-pha-b-2026-10-17.md).

Toàn kho: **1.617 test qua**, xem [báo cáo tích hợp](../../report/v4-19-phan-tich-va-kiem-chung-2026-10-17.md).
