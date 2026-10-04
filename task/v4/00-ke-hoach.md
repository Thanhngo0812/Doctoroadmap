# v4 — Nhanh, rẻ, vẫn chuẩn: kế hoạch vé

**Nguyên tắc số một (chủ dự án, 2026-10-03):** đây là ứng dụng phục vụ người dùng, nên phải tối ưu **phút/cuốn** và **USD/cuốn** trước hết.
- Mỗi vé đo hai số trước và sau sửa, trên cùng bộ tài liệu: phút/cuốn và USD/cuốn.
- Chất lượng vẫn đo trên vàng. Cách tiết kiệm nào làm tụt chất lượng thì báo đánh đổi bằng số, chủ dự án quyết.
- Đường gọi sản phẩm là Gemini Developer API, song song cao. Vertex chỉ dùng khi còn credit.

**Nguồn:** [nghiên cứu tiền và thời gian](../../report/nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md) ·
[kết quả tập giữ lại v3](../../report/ket-qua-tap-giu-lai-v3-2026-10-04.md) · mục "Hướng v4" của
[kế hoạch v3](../v3-lo-trinh-doc-duoc/00-ke-hoach.md).

**Mốc v3:** doc-4 (giáo trình trọn cuốn) tốn khoảng 50 USD; riêng A8 pass phụ 45,9 USD (91%) và khoảng 4,5–5 giờ trên Vertex.

**Trạng thái:** soạn 2026-10-04, chờ chủ dự án duyệt thứ tự và giao vé.

## Dữ liệu dùng được

- Tập giữ lại v3 (xstk, doc-4) **đã dùng**. Từ v4, hai tài liệu này là tài liệu phát triển, cùng sáu tài liệu cũ.
- Mọi sửa chất lượng của v4 cần **tập giữ lại mới**: tài liệu mới và vàng mới, chọn trước khi sửa. Đổi tiền và thời gian mà đầu ra y hệt
  (như v4-01) thì không cần.

## Vé

| vé | việc | ai | chi phí mô hình | trạng thái |
|---|---|---|---|---|
| [01](01-pass-phu-hoi-luoi.md) | A8 pass phụ hỏi lười thứ tự thứ hai: đầu ra y hệt, bớt 19–38% lời gọi | nhân viên | 0 (phát lại) | chờ giao |
| [02](02-thoi-gian-moi-khau.md) | mọi stage ghi thời gian chạy; Claude viết báo cáo phút/USD mỗi cuốn | nhân viên + Claude | 0 | chờ giao |
| 03 | thử hồ sơ cặp gọn cho pass phụ (bớt toàn văn đoạn) | Claude soạn sau 01 | khoảng 2–4 USD, chờ duyệt | chưa soạn |
| 04 | đọc nhật ký phản hồi lỗi của pass phụ (12% cặp doc-4) | Claude | 0 | chưa làm |
| 05 | sửa chất lượng từ tập giữ lại: A2 "Cách giải", C8 bỏ qua khái niệm ngoài nội dung, R17, cạnh khái niệm khung | Claude soạn | cần tập giữ lại mới | chưa soạn |
| T-01 | chọn 2 tài liệu mới và người gán vàng cho tập giữ lại v4 | **chủ dự án** | 0 | chưa làm |
| — | lọc cặp bằng học máy trước pass phụ | chủ dự án giao sau | — | ý tưởng |
