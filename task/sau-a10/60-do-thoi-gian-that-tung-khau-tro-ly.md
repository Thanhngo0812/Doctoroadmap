# SA-60 — Đo thời gian thật từng khâu của trợ lý (Vertex và Developer API)

**Nguồn:** SA-55 (TTFT p50 15,8 s, riêng mô hình 0,95 s); SA-59 (`report/pha-b-sa59-2026-10-22.md`, mục 8).

SA-59 cắt phần đo được ở 0 USD, nhưng phần chờ giả lập chỉ còn khoảng 0,4 s. Như vậy hơn 14 s còn lại nằm ở chỗ chỉ đo thật mới thấy. Ứng viên:
- độ trễ hay bị bóp quota của embedding qua Vertex (mỗi văn bản một request);
- việc ghi lại cả kho JSON 6,5 MB, khoảng 235 ms mỗi lần ghi, nhân với số lần ghi mỗi lượt;
- lời gọi công cụ do mô hình chọn.

**Ai:** agent Sonnet · Claude nghiệm thu · **Chi phí mô hình:** dự kiến dưới 0,05 USD, chỉ `gemini-3.1-flash-lite` và mô hình embedding đang dùng; dry-run trước,
**chờ chủ dự án duyệt** · **Chặn bởi:** không · **Trạng thái:** chờ duyệt tiền

## Cần làm

- Chọn 12 lượt từ bộ câu SA-55: 6 lượt phiên module, 6 lượt phiên lộ trình, trên doc-1 và nhap-mon-ml.
- Thêm bộ ghi giờ cho từng khâu **trong bộ chạy**, không sửa mã sản phẩm:
  - mỗi lời gọi embedding: thời gian, số văn bản, mã HTTP, số lần thử lại;
  - mỗi lần ghi kho, cộng tổng số lần ghi trong lượt;
  - tìm kiếm;
  - lời gọi mô hình đầu tiên.
- Chạy hai lần trên cùng 12 lượt:
  1. qua Vertex, cấu hình hiện tại;
  2. qua Gemini Developer API, nếu `.env` có khoá. Không có khoá thì bỏ lần này và ghi vào báo cáo.
- Chạy thêm một lần với kho Pha B trong bộ nhớ (`InMemoryPhaseBStore`), để tách chi phí ghi kho JSON khỏi phần còn lại.

## Tiêu chí nghiệm thu

- [ ] Dry-run có số lượt, số lời gọi tối đa và USD tối đa. Chỉ chạy thật sau khi chủ dự án duyệt; trích tin nhắn duyệt vào báo cáo.
- [ ] Bảng thời gian theo khâu (p50, p90) cho từng lần chạy, kèm số lời gọi embedding và số lần thử lại mỗi lượt.
- [ ] Kết luận khâu nào chiếm phần lớn thời gian chờ, kèm số. Đề xuất cách cắt; không tự cài.
- [ ] Không để sót tiến trình nền. Không in bí mật.
