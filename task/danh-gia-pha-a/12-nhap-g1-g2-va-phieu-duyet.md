# DG-12 — Gói nháp G1/G2, lỗi cài và phiếu duyệt

**Nguồn:** spec mục 5 (G1, G2, lỗi cài); công cụ D-02 ở `scripts/a1-d02/` · **Ai:** agent A; Codex làm nháp theo gói, do chủ dự án giao · **Chi phí:** 0 ·
**Chặn bởi:** lược đồ manifest ở DG-01 · **Hạn:** 31/10 · **Trạng thái:** ready-for-agent

## Làm được gì

Các bước:
1. Từ manifest và PDF, sinh **gói nháp** cho Codex, giống định dạng D-02: bảng dòng theo trang có mã dòng, hướng dẫn, validator. Codex trả cây mục, cộng vai
   trò từng mục G2.
2. Người giữ chạy **cài lỗi**: 3–5 lỗi đã biết mỗi cuốn (đổi cấp, bỏ một tiêu đề, gán sai một vai trò), ghi vào sổ riêng.
3. Từ đó sinh **phiếu duyệt** cho sinh viên: mỗi mục một dòng, cạnh số trang. Sinh viên sửa trực tiếp.
4. Đọc phiếu duyệt về cây G1 và vai trò G2 cuối. Gỡ lỗi cài nào sinh viên bỏ sót. Báo tỉ lệ bắt lỗi cài.
5. Sinh phiếu cho người duyệt thứ hai trên khoảng 30% số mục, theo seed; tính κ và % đồng ý.

## Tiêu chí

- [ ] Gói nháp và cây cuối qua validator D-02 (`kiem_nhan_d02.py`) hoặc bản chuyển tương đương.
- [ ] Lỗi cài tất định theo seed; sổ lỗi cài không lọt vào phiếu sinh viên. Test tìm chuỗi đánh dấu trong phiếu.
- [ ] Tỉ lệ bắt lỗi cài đúng trên ví dụ dựng tay.
- [ ] Bảng phá, gồm ít nhất: lỗi cài lọt vào vàng cuối; mẫu 30% không theo seed; phiếu lộ cột "lỗi cài".
