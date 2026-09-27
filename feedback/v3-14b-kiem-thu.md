# Feedback triển khai v3-14b

**2026-09-27 — đã triển khai, test và chạy doc-2; chờ reviewer nghiệm thu.** [Báo cáo chi tiết](../report/v3-14b-ket-qua-2026-09-27.md) · [vé 14b](../task/v3-lo-trinh-doc-duoc/14b-nhan-vai-tro-chia-lo.md).

- Chia tối đa 40 tiêu đề/lô theo chương; trước và sau chương là lô riêng. Nhãn vi phạm cấu trúc hỏi lại một lần trong lô tối đa 10, rồi mới về `noi_dung` kèm cảnh báo.
- Doc-2: 106 chunk gắn nhầm `de_cuong` trên cây cũ → **0**; chuyển vai trò từ cây mới được **1.032/1.038 chunk**; 0 neo ở vùng không dạy. Bốn mục bài giảng reviewer nêu đều là `noi_dung`.
- Trong 42 khái niệm từng mất trạng thái dạy, **24 phục hồi, 18 chưa**. Q6 doc-2 **2/57**, Q7 **0,58045**, Q7b **0,92105**; R11 còn **118** khái niệm chỉ-nhắc trong dãy học, xử lý ở vé 07. Không tuyên bố 18 trường hợp là lỗi vai trò khi chưa đọc bằng chứng neo.
- Test unit/integration xanh, ID/text/offset chunk giữ nguyên; không chạy lại A8, không đọc bộ vàng giữ lại. Tổng chi chung 05+14+14b **0,65896475/1 USD**. T19 vẫn chờ chủ dự án.
