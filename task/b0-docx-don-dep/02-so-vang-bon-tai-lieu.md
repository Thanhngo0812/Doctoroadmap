# 02 — Bộ số vàng bốn tài liệu — chốt hiện trạng

**What to build:** Một bộ test chạy toàn pipeline từ fixture qua chunk cho **cả bốn tài liệu thật**
và so với số vàng đã ghim. Từ nay, mọi thay đổi luật làm lệch bất kỳ số nào ⇒ test đỏ ⇒ người sửa
cập nhật số vàng **trong cùng commit, có chủ đích** — diff của số vàng chính là biên bản review.
Đây là phiên bản tự động của phương pháp so-v1↔v2-bằng-tay đã dùng tám vòng.

Số ghim cho mỗi tài liệu:

- số section, số chunk
- số tham chiếu ảnh / bảng / công thức
- số ký tự vùng dùng riêng còn trong văn bản chunk
- vi phạm I9 = 0, định danh trùng = 0 (hai số này ghim cứng bằng 0, không bao giờ được nới)
- danh sách cảnh báo (đếm theo loại)

**Ticket này ghim HIỆN TRẠNG — kể cả cái sai đã biết**: cây DOCX gãy 12 section lạc cha, tiêu đề
slide bị hạ, 72 ký tự U+F097, chunk rác. Ghim cái sai là chủ đích: các ticket sau sửa từng luật và
phải **nhìn thấy** số vàng dịch chuyển đúng chỗ dự đoán, không hơn không kém.

**Blocked by:** 01 — cần đủ bốn fixture.

**Status:** done

- [x] Test số vàng chạy từ fixture, không đụng Docling thật, cả bốn tài liệu dưới vài giây
- [x] Số vàng ghi ở dạng đọc được trong review (một cấu trúc dữ liệu phẳng, diff sạch)
- [x] I9 và định danh trùng ghim cứng = 0 cho mọi tài liệu, tách khỏi các số được phép cập nhật
- [x] Số vàng ban đầu khớp hiện trạng: DOCX 27 section / 30 chunk / 0 tham chiếu ảnh;
      slide 32 section / 40 chunk / 2 ảnh / 13 bảng / 32 công thức / 72 ký tự vùng dùng riêng
- [x] Hai giáo trình ghim theo con số hiện hành trong artifact v2 của chúng
- [x] Có ghi chú ngay cạnh số vàng: "đổi số phải kèm giải thích trong commit" — luật làm việc,
      không phải comment giải thích code
