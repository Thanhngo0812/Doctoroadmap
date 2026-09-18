# 11 — Nạp ba tài liệu mới qua A1–A5

**What to build:** Ba tài liệu chủ dự án gửi — hai giáo trình đầy đủ và một tài liệu phẳng — đi hết ingest, A3,
nhánh chỉ mục vector, A4 và A5, để có bảng node canonical làm đầu vào cho mọi thứ còn lại.

Không sửa code ở vé này. Nếu phải sửa thì dừng và báo, vì đó là thay đổi hành vi của phase đã đóng.

**Blocked by:** None về code — chờ chủ dự án gửi tài liệu.

**Status:** ready-for-agent — chủ dự án đã gửi `doc-1.pdf`, `doc-2.pdf`, `doc-3.pdf` (2026-09-18); xem ghi chú dưới

> **Ba tài liệu đã có trong workspace, đã nằm trong `.gitignore`.** Soi trước khi nạp (2026-09-18):
> - `doc-1.pdf` — *Bài giảng Đại số tuyến tính*, tiếng Việt, 159 trang, 208 nghìn ký tự, có `Chương` và ba cấp mục.
>   **Mọi trang đều có watermark Studocu kèm địa chỉ email cá nhân của chủ dự án.**
> - `doc-2.pdf` — *Linear Algebra Done Right, 4th ed.*, **tiếng Anh**, 404 trang, 788 nghìn ký tự, có `Chapter` và
>   `Section`. Đây là tài liệu lớn nhất, ước lượng 700–1.000 chunk.
> - `doc-3.pdf` — *15.773 Hands-on Deep Learning, Lecture 1*, **tiếng Anh**, slide, 110 trang nhưng chỉ 26 nghìn ký
>   tự, cấu trúc phẳng — đúng loại để thử nhánh cụm chủ đề.
>
> Thứ tự chạy: `doc-3` → `doc-1` → `doc-2`, và chỉ chạy `doc-2` sau khi F101 và F102 đã xong, vì nó là tài liệu
> chịu ảnh hưởng nặng nhất của hai lỗi đó.

- [ ] Ba tài liệu ingest xong; dán cảnh báo parse của từng tài liệu vào vé.
- [ ] A3, chỉ mục vector, A4 và A5 chạy xong cho cả ba.
- [ ] Dán bảng cỡ tài liệu vào vé: số trang, chunk, section, node, node `learnable`, media, cạnh đề xuất — dùng
      để chọn chương gán nhãn và để biết định tuyến sẽ chọn nhánh nào.
- [ ] Dán số lời gọi, token và **chi phí cộng dồn** của cả ba tài liệu; so với trần 50 USD.
- [ ] Chạy lại khi chặn mạng: `reused=true` cho cả ba.
- [ ] Không có tài liệu gốc nào bị commit vào repo.
- [ ] **`doc-1`: kiểm và báo số chunk còn chứa watermark.** Dòng `lOMoARcPSD|…`, `Scan to open on Studeersnel` và
      dòng có email cá nhân xuất hiện ở **cả 159 trang**; parser đang bỏ được `page_footer` (chân trang của
      `xstk-ch3-1` không lọt vào chunk nào), nhưng watermark của Studocu có thể không được gắn nhãn như vậy. Nếu
      còn sót thì **dừng và báo**: dữ liệu này sẽ đi thẳng vào prompt gửi Gemini và nằm lại trong artifact.
- [ ] Ghi rõ ngôn ngữ từng tài liệu vào bảng cỡ; `doc-2` và `doc-3` là tiếng Anh, nên phải kiểm luật ngôn ngữ của
      A5 (`token-majority-prose-vi20-v2`) có xử lý đúng không, và báo nếu mô tả sinh ra lẫn lộn hai thứ tiếng.

## Feedback bàn giao

- Vé không có thay đổi code và chưa được phép giả lập dữ liệu.
- Chặn hiện tại: workspace chưa có hai giáo trình đầy đủ và một tài liệu phẳng mà vé yêu cầu. Khi nhận đủ file,
  chạy A1–A5, ghi cảnh báo parse/số đo/chi phí rồi kiểm tra lại cache khi khóa mạng.
- Chưa có tài liệu gốc mới nào được thêm vào Git.
