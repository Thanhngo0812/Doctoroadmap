# 05b — Chạy lại xstk và doc-4 sau khi sửa A2, đo và đọc

**Nguồn chân lý:** [nghiên cứu vé 05](../../report/v4-05-a2-de-cuong-lap-2026-10-17.md), mục 2 và 6.
**Ai:** Claude · **Chi phí mô hình:** ước dưới 0,5 USD; dry-run trước, chủ dự án duyệt · **Chặn bởi:** [05a](05a-a2-luat-de-cuong-lap.md) ·
**Trạng thái:** chờ

## Vì sao

Mô phỏng chỉ cho biết khái niệm nào có thêm câu ứng viên. Nó không cho biết:
- lớp nhãn LLM gán gì cho các mục rời luật lặp;
- lời phán neo nói gì về các khái niệm vừa có ứng viên;
- A8 tìm lại được bao nhiêu cạnh.

Cả ba phải đo bằng lượt chạy thật.

## Cần làm

- **Ghim mã** ở commit chứa 05a, chạy từ checkout sạch như cổng 19l. Ghi SHA và bảng nguồn gốc artifact mới.
- **xstk:**
  - `label-roles` theo khuôn T10 trong `CONTEXT.md`: nhãn trên chunk v3, rồi chuyển sang chunk v2;
  - rồi `a4` (chuỗi gộp) và `roadmap`;
  - mỗi bước dry-run trước.
- **doc-4:**
  - `label-roles`;
  - `a4` và `roadmap` chỉ chạy khi dry-run báo có việc mới.
- **Đọc:**
  - nhãn LLM của 13 mục "Cách giải" và 10 mục "Câu hỏi ôn tập";
  - lời phán neo của 10 khái niệm vàng xstk trong bảng mục 2 của nghiên cứu;
  - mọi khái niệm đổi trạng thái dạy ở xstk và doc-4.
- **Đo**, so với cổng 19l:
  - số khái niệm đích trong dãy học;
  - số cạnh vàng có cả hai đầu trong dãy học;
  - E4 (`cham_gop`);
  - lời gọi, USD, phút.
- **Xem lại hai phần đã hoãn** (nghiên cứu mục 3) bằng kết quả thật: "Bài toán tìm kích thước mẫu", và luật bỏ qua khái niệm ngoài vùng nội dung.
- **Khi T-01 có vàng:** đo lại trên T-01 bằng script chỉ in trường trong allowlist.

## Nghiệm thu

- [ ] Báo cáo có SHA mã, bảng nguồn gốc artifact, chi thật so với dự toán.
- [ ] Bảng trước và sau trên xstk: khái niệm đích trong dãy học, cạnh vàng trong phạm vi, E4. Có các chỗ đã đọc.
- [ ] doc-4: nhãn của mục câu hỏi ôn tập; E4 so với cổng 19l. Đọc nếu lệch.
- [ ] Artifact mới nằm ở kho chính. Kế hoạch v4 ghi việc tiếp theo của hàng 05.
