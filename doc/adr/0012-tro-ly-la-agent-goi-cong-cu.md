# Trợ lý học tập là agent gọi công cụ trên đồ thị và chỉ mục

**Status:** accepted — 2026-10-15

Trợ lý hỏi đáp là một agent: mô hình tự chọn gọi công cụ trong một vòng lặp, rồi trả lời. Agent có bốn nhóm công cụ:
- tra cứu: `search_document`, `lookup_concept`, `get_module_info`, `why_here`, `path_to`, `traverse`, `get_media`;
- đọc bài giảng: `get_lecture`;
- tạo nội dung theo yêu cầu: `make_quiz`, `make_document`.

Vòng lặp có giới hạn:
- tối đa 5 vòng công cụ và khoảng 0,01 USD cho mỗi tin nhắn;
- vòng cuối không cho gọi công cụ;
- mỗi tin nhắn bắt đầu bằng một ngữ cảnh mồi do mã lắp: module đang mở, khái niệm liên kết được, vài đoạn truy hồi có ưu tiên module.

Trợ lý chỉ tìm trong tài liệu đã tải lên và không chặn theo tiến độ.

Ba việc không giao cho mô hình:
- **Mã làm phần chắc chắn:** khối nhắc khái niệm nền, ghi chú "học kỹ ở module N", câu từ chối khi không có nguồn.
- **Mã hậu kiểm nhãn trích dẫn.**
- **Nút bấm bài giảng và quiz gọi thẳng hàm**, không qua agent. Agent dùng **chính các hàm đó** làm công cụ.

Căn cứ:
- Chủ dự án chốt ngày 2026-10-15: "tôi muốn agent hết, để có thể cho nó tool tạo tài liệu hoặc tạo quiz trực tiếp". Bài giảng có sẵn khi bấm,
  nên agent không cần tự sinh bài giảng.
- [Báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md) mục 3 so ba kiến trúc.

**Considered Options**

- *Quy trình cố định:* mã truy hồi, mở rộng đồ thị, rồi một lời gọi sinh. Rẻ nhất (khoảng 0,0014 USD và khoảng 1,4 giây tới chữ đầu, ước),
  dễ kiểm thử. Nhưng không tạo được quiz hay tài liệu theo yêu cầu tự do, và không tự tra thêm khi thiếu.
- *Lai:* mã định tuyến, agent chỉ cho câu khó, tối đa 2 vòng. Đây là đề xuất của báo cáo. Bị thay vì chủ dự án muốn mọi yêu cầu đi qua agent
  để dùng được công cụ tạo nội dung.
- *Agent không trần.* Bị bác: token vào tăng gần theo bình phương số vòng, và giây chờ không chặn được.

**Consequences**

- Tiền và giây chờ mỗi câu cao hơn quy trình cố định (ước 0,0022–0,0034 USD cho 2–3 vòng). Ngữ cảnh mồi giữ phần lớn câu ở một lời gọi; điều
  này phải đo.
- Phải có port mô hình hội thoại có công cụ. Port giữ kín thought signature của Gemini 3 trong lượt hiện tại. Câu trả lời là văn bản Markdown có
  nhãn, vì flash-lite chưa dùng structured output cùng công cụ.
- Tỉ lệ gọi công cụ sai của flash-lite phải đo. Quá 10% thì hỏi chủ dự án trước khi thử mô hình mạnh hơn.
- **Thí nghiệm cho báo cáo đồ án so bốn cấu hình** trên cùng bộ câu hỏi thử:
  - LLM không bằng chứng;
  - RAG thuần;
  - agent không có công cụ đồ thị;
  - agent đầy đủ.

  Cấu hình thứ ba là phép ablation đo đóng góp của đồ thị.
- Câu trả lời không cache chung. Nội dung agent tạo được lưu theo người học.
- Spec B2 cũ (bảng năm công cụ, lọc `module_index <= hiện tại`) được thay bằng [spec Pha B](../pha-b-spec.md) mục 10.
