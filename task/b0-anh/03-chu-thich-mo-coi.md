# 03 — Chú thích mồ côi và thống kê chú thích

**What to build:** Người đọc corpus tìm được `Hình 2` là gì. Hiện thân bài viết *"Hình 2 chứa một tập ví dụ"*
nhưng câu chú thích `'Hình 2: Tập các bức ảnh và các mô tả về chúng.'` **không tồn tại ở bất cứ đâu** trong
artifact — không trong cây parse, không trong chunk, không trong chuỗi văn bản đầy đủ.

Nguyên nhân: thư viện parse gắn chú thích cho **tối đa một** hình trong một cụm. Cụm ba hình ở trang 7 nhận ba
dòng mô tả riêng, còn chú thích chung của cả cụm không thuộc về hình nào — và adapter bỏ **mọi** item nhãn chú
thích vô điều kiện, với giả định rằng chúng luôn quay lại qua liên kết hình–chú thích. Giả định đó đúng 8/9
lần.

Kèm theo: thống kê parse hiện ghi `caption: 9` bị bỏ, nhưng **không phân biệt** "bỏ vì đã lấy lại được" với
"bỏ vì mất hẳn". Đó là lý do lỗi này sống sót qua hai vòng review.

**Blocked by:** Không — bắt đầu ngay. Không phụ thuộc nhánh ảnh: chú thích mồ côi là chuyện của văn bản.

**Status:** completed — 2026-08-20

- [x] Chú thích mà không hình nào nhận trở thành **khối văn bản bình thường**, tại đúng vị trí đọc của nó
- [x] **Không** gán ghép theo toạ độ — chính việc thư viện parse đoán sai ranh giới cụm đã tạo ra vấn đề này
- [x] Thống kê parse phân biệt chú thích bị bỏ vì đã lấy lại được với chú thích bị bỏ vì mồ côi
- [x] Hai con số lệch nhau thì ghi một lý do cảnh báo, kèm nguyên văn chú thích mồ côi
- [x] Tăng phiên bản adapter
- [x] Có test trên fixture parse thật: chú thích cụm hình trang 7 **có mặt** trong cây tài liệu
- [x] Có test: nó nằm đúng chỗ trong thứ tự đọc, không bị đẩy xuống cuối
- [x] Có test: tám chú thích còn lại **vẫn** bị bỏ, vì chúng đã là nội dung của node hình rồi — không được nhân đôi
- [x] Có test: cảnh báo mồ côi bật đúng một lần cho tài liệu này
