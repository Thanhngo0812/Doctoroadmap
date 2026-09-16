# 11 — Nạp ba tài liệu mới qua A1–A5

**What to build:** Ba tài liệu chủ dự án gửi — hai giáo trình đầy đủ và một tài liệu phẳng — đi hết ingest, A3,
nhánh chỉ mục vector, A4 và A5, để có bảng node canonical làm đầu vào cho mọi thứ còn lại.

Không sửa code ở vé này. Nếu phải sửa thì dừng và báo, vì đó là thay đổi hành vi của phase đã đóng.

**Blocked by:** None về code — chờ chủ dự án gửi tài liệu.

**Status:** ready-for-agent

- [ ] Ba tài liệu ingest xong; dán cảnh báo parse của từng tài liệu vào vé.
- [ ] A3, chỉ mục vector, A4 và A5 chạy xong cho cả ba.
- [ ] Dán bảng cỡ tài liệu vào vé: số trang, chunk, section, node, node `learnable`, media, cạnh đề xuất — dùng
      để chọn chương gán nhãn và để biết định tuyến sẽ chọn nhánh nào.
- [ ] Dán số lời gọi, token và **chi phí cộng dồn** của cả ba tài liệu; so với trần 50 USD.
- [ ] Chạy lại khi chặn mạng: `reused=true` cho cả ba.
- [ ] Không có tài liệu gốc nào bị commit vào repo.
