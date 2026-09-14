# 01 — Hai cảnh báo trả về A3: mô tả trùng từng chữ, bằng chứng không nhắc tên

**What to build:** Chạy `a3-report` trên bốn tài liệu và thấy thêm hai loại cảnh báo, tính ngay trên artifact A3
đang có — không trích lại gì:

1. trong cùng một section, hai thực thể **khác tên** có `description_draft` **trùng từng chữ**;
2. câu bằng chứng của một thực thể **không chứa** tên, alias hay ký hiệu nào của chính nó.

Các lần A3 chạy mới cũng ghi hai cảnh báo này vào artifact. Cả hai là cảnh báo — không ứng viên nào bị loại.

## Vì sao

Đây là hai lỗi **của A3** nhưng nổ ở A4 (spec A4/A5 D11, báo cáo mục 2.2):

- 31 cặp khác tên đạt cosine ≥ 0,999 chỉ vì A3 viết **cùng một câu** cho mọi mục trong một danh sách liệt kê —
  bảy thuật toán phân loại cùng câu *"Mô hình học máy dùng cho bài toán phân loại."*. Tính trong cùng section:
  **6 câu dùng chung cho 19 tên**. (Xuyên section không tính: ca duy nhất xuyên section là một cặp trùng thật.)
- **31/377** ứng viên có câu bằng chứng không nhắc tên. Có ca hợp lệ (diễn đạt tiếng Việt cho tên tiếng Anh, chữ OCR
  hỏng), có ca yếu thật (`WebSocket` và `Concurrency` dùng chung câu *"Xây dựng các kịch bản thực hành về xử lý đa
  luồng…"*). Ticket 07 dùng lại đúng hàm này để quyết định khi nào kèm toàn văn chunk cho mô hình.

**Blocked by:** None — can start immediately.

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã triển khai và đo đúng 6 câu/19 tên, 31/377; test domain và báo cáo offline.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] Hàm thuần phát hiện mô tả trùng: trong một section, từ hai thực thể có khoá tên khác nhau trở lên mang
      `description_draft` trùng nhau sau khi gộp khoảng trắng ⇒ một cảnh báo liệt kê các tên. Media không tính.
      Hai section khác nhau có cùng câu **không** bắn.
- [x] Hàm thuần phát hiện bằng chứng không nhắc tên: không câu bằng chứng nào của thực thể chứa tên, alias hay ký hiệu
      của nó — so trên văn bản đã bỏ dấu, bỏ dấu câu, không phân biệt hoa thường. Media và thực thể chỉ có bằng chứng
      ảnh (`media_evidence_id`) không tính.
- [x] Cả hai chỉ là cảnh báo: số ứng viên trong artifact không đổi.
- [x] Lần chạy A3 mới ghi hai cảnh báo vào `warnings` theo khuôn cảnh báo gom sẵn có. `algorithm_id` của A3 **không
      đổi**, nên artifact cũ vẫn được tái dùng và không phải trích lại.
- [x] `a3-report` tính hai cảnh báo trên artifact đã có và in số đếm theo tài liệu.
- [x] Trên artifact hiện tại của bốn tài liệu: mô tả trùng = **6 câu / 19 tên**; bằng chứng không nhắc tên =
      **31/377**. Lệch thì ghi giải thích vào ticket.
- [x] Test domain đi cả nhánh bắn lẫn nhánh không bắn cho từng cảnh báo, gồm: câu tiếng Việt diễn đạt lại tên tiếng
      Anh (*"hệ thống chống thư rác"* cho `Spam Filtering`) **vẫn bắn** — đây là cảnh báo, không phải lỗi; tên chỉ khác
      dấu với câu bằng chứng **không** bắn; cùng câu mô tả ở hai section khác nhau **không** bắn.
- [x] Hàm phát hiện bằng chứng không nhắc tên đặt ở chỗ ticket 07 gọi lại được, không nhân bản logic.
- [x] Toàn bộ test hiện có vẫn xanh.
