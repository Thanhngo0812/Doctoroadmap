# 12 — Chạy E1 và E2 trên bộ vàng

**What to build:** Trả lời hai câu quyết định của cả đợt, **không tốn lời gọi mô hình nào**: cạnh tiên quyết nằm
ở đâu, và bộ sinh cặp nào đáng giữ. Kết quả quyết định mention map và pass phụ có vào mặc định hay không.

**Blocked by:** 05, 11, và việc gán nhãn đã đóng băng. (Việc của Claude.)

**Status:** ready-for-agent

- [ ] Hai người gán đã nộp file, độ đồng thuận đã tính (có kể đồng thuận ngầm qua bắc cầu), và **đã hội ý** xong;
      bộ vàng đóng băng trước khi chạy.
- [ ] E1: bảng sáu loại vị trí, kèm NMI giữa cụm chủ đề và chương, cho cả hai giáo trình.
- [ ] E2: bảng theo từng bộ sinh và từng tổ hợp, kèm recall riêng và ba cấu hình định tuyến.
- [ ] Áp **luật chọn bộ sinh mặc định** đã viết trước ở D5, và ghi kết quả áp luật.
- [ ] Mọi số kèm khoảng tin cậy; chỗ nào khoảng chồng lấn thì viết "chưa phân biệt được".
- [ ] Báo cáo cả số trên hợp và trên giao nhãn của hai người, để xem độ nhạy.
