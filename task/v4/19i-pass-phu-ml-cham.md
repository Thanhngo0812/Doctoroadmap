# 19i — Pass phụ ML chậm trên tài liệu lớn

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 2 mục 5.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** sẵn sàng giao

## Vì sao

Pass phụ ML (`a8-secondary-ml-v1`) mất **592 giây** trên doc-4 ở chuỗi gộp. Trên d01-02 nó chỉ mất 18 giây, và 18d đo 3,8 phút trên doc-4 của chuỗi v3.
Chưa rõ nguyên nhân. Đồ thị nằm ở kho `tmp/v4-17i/artifacts`, `graph/doc-4/v4`, upstream v3.

## Cần làm

- Profile stage trên artifact pass chính có sẵn đó, 0 USD, ở kho thử. Tìm nút cổ chai: dựng đặc trưng, cửa sổ định nghĩa, bộ tách từ, khớp tên…
- Sửa nút cổ chai. **Đặc trưng, điểm, ngưỡng và cạnh phải giống hệt trước.**
- Không đổi khoá cache.

## Nghiệm thu

- [ ] Ghi số giây trước và sau trên doc-4 kho thử, kèm nút cổ chai đã tìm.
- [ ] Đặc trưng và điểm từng chiều trước và sau cùng băm; cạnh pass phụ y hệt.
- [ ] Toàn bộ test qua; test nghiệm thu 18d vẫn qua.
