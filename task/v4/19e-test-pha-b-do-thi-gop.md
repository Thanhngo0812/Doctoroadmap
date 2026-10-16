# 19e — Test tích hợp: Pha B nạp đồ thị chuỗi gộp

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), Testing Decisions mục 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** sẵn sàng giao

## Vì sao

Test của vé 17c mới phủ A10 và bộ chấm. Pha B đọc đồ thị lộ trình, nên cần một test chắc rằng đồ thị chuỗi gộp nạp được qua bộ nạp của Pha B. Nghiên
cứu đã thử tay với doc-1, xstk và doc-4.

## Cần làm

- Một test tích hợp nạp đồ thị `stages` của chuỗi gộp, sinh từ fixture tài liệu thật với mô hình giả, qua bộ nạp đồ thị của Pha B.
- **Không sửa mã Pha B.** Nếu test lộ lỗi tương thích thì báo lại, để chuyển cho phiên Pha B.

## Nghiệm thu

- [ ] Bộ nạp Pha B nạp được đồ thị chuỗi gộp. Node có câu neo và chunk dạy đúng dạng mà bài giảng đọc.
- [ ] Một artifact v3 có `identity_map` trong fixture vẫn nạp được.
- [ ] Toàn bộ test qua.
