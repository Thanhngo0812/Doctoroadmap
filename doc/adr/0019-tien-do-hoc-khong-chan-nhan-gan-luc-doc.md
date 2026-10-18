# Tiến độ học theo khái niệm, không chặn; nhãn theo người học gắn lúc đọc, không cache

**Status:** accepted — 2026-10-18

**Tiến độ là đánh dấu "đã học" theo khái niệm, khoá theo `node_id`.** Hai nguồn đánh dấu:
- người học tự bấm "đã học", hoặc bỏ dấu;
- hệ thống tự đánh dấu khi người học làm đúng ít nhất một câu quiz của khái niệm, nhưng chỉ khi người học chưa tự chọn. Lựa chọn của người học luôn thắng.

Mở bài giảng không tính là đã học.

**Tiến độ không chặn chức năng nào.** Nó chỉ dùng cho ba việc:
- chọn tiên quyết để trợ lý nhắc (chỉ tiên quyết chưa học);
- gắn nhãn "đã học / chưa học, module m" cho tiên quyết và khối "Tiếp theo" trong bài giảng;
- ưu tiên khái niệm đã học khi tạo quiz ôn tập cả lộ trình.

**Bài giảng và ngân hàng quiz được cache chung cho mọi người học** (ADR 0011). Vì vậy:
- chữ do LLM viết phải trung tính, không nói về trạng thái của người học;
- nhãn theo người học do một bước riêng gắn lúc trả bài;
- nhãn này không vào cache, không vào `lecture_key`, và không vào prompt.

**Căn cứ:**
- Chủ dự án chốt ngày 2026-10-18 (Q9, Q23–Q25, Q30).
- Quyết định ngày 2026-10-11 "không chặn theo tiến độ" vẫn giữ.
- [Báo cáo nghiên cứu bài giảng](../../report/nghien-cuu-bai-giang-tien-quyet-goi-mo-xu-ly-hong-2026-10-18.md): gợi lại có ích cho người chưa biết;
  với người đã biết thì nên gập.

**Considered Options**

- *Không theo dõi tiến độ.* Đơn giản hơn, nhưng bài giảng chỉ nói được "ở module m", còn trợ lý nhắc khái niệm nền mà không biết người học đã học chưa.
- *Tự đánh dấu khi mở bài giảng.* Bị bác: mở không có nghĩa là đã học.
- *Mô hình trình độ (mastery, BKT) và mở khoá module.* Vẫn ngoài phạm vi theo đề cương.
- *Để LLM viết câu theo tiến độ, ví dụ "như bạn đã học".* Bị bác: bài cache chung sẽ nói sai với người chưa học, hoặc phải cache theo từng người học.

**Consequences**

- Có thêm loại bản ghi `progress` và use case `set_progress`, `get_progress`.
- Lần nộp quiz cập nhật tiến độ.
- Có luật K12, chặn cụm nói về trạng thái người học trong câu nối.
- Tiến độ khoá theo `node_id`, nên còn đúng khi đồ thị lên phiên bản mới (202/205 `node_id` của doc-1 giữ nguyên từ v45 sang v53).
