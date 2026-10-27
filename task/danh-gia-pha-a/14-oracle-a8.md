# DG-14 — Oracle A8 trên kho chốt G3

**Nguồn:** spec mục 11 (oracle A8) · **Ai:** agent B; Claude chạy lượt thật · **Chi phí:** 0 khi cài; lượt thật nhỏ · **Chặn bởi:** DG-02, DG-08 · **Hạn:**
02/11 · **Trạng thái:** ready-for-agent

## Làm được gì

Từ kho chốt G3 của một cuốn, một adapter (seam xuất) dựng **canonical oracle** trong kho của thư mục lượt:
- mỗi khái niệm vàng thành một node, có tên và tên khác;
- câu neo gắn vào chunk chứa câu định nghĩa, tìm bằng khớp mờ trong chunk của lượt chính;
- trạng thái dạy theo ánh xạ ngược bốn sang sáu giá trị.

Sau đó chạy `roadmap` (A6 → A10) trên canonical đó, rồi xuất hợp đồng với biến thể `oracle-a8`.

## Tiêu chí

- [ ] Canonical oracle qua kiểm lược đồ canonical của pipeline. `roadmap` dry-run nhận nó.
- [ ] Khái niệm có câu định nghĩa không tìm được chunk thì được báo và đếm, không bị bỏ ngầm.
- [ ] Chạy trọn với mô hình giả trên fixture.
- [ ] Bảng phá, gồm ít nhất: gắn câu neo vào chunk sai trang; bỏ ngầm khái niệm không có chunk.
