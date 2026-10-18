# Phạm vi phiên là nơi lưu và nơi ưu tiên tìm, neo vào khái niệm

**Status:** accepted — 2026-10-18

Mỗi phiên chat, tài liệu và lần làm quiz có một **phạm vi**: cả lộ trình, hoặc một module.

**Phạm vi chỉ quyết hai việc:**
- nội dung được lưu và liệt kê ở đâu;
- trợ lý ưu tiên tìm ở đâu.

**Phạm vi không giới hạn chỗ tìm.**
- Hỏi trong phiên module về khái niệm của module khác thì trợ lý vẫn trả lời, kèm thẻ "nội dung ở module N", do mã gắn.
- Phiên ở trang lộ trình không có module đang mở, và tìm khắp tài liệu.

**Phạm vi module lưu danh sách `node_id` của module lúc tạo, không lưu mã module.**
- Mỗi lần dùng, mã giải phạm vi sang module hiện hành có Jaccard cao nhất trên tập khái niệm.
- Dưới ngưỡng 0,5 thì phạm vi bị coi là đã cũ: phiên chạy như phiên lộ trình, kèm ghi chú.
- Module của một tài liệu hay lần làm quiz được suy lúc liệt kê, từ `node_ids` của nó.

**Căn cứ:**
- Chủ dự án chốt ở đợt tra hỏi ngày 2026-10-18 (Q1, Q2, Q19–Q22).
- [Báo cáo nghiên cứu giao diện hai tầng](../../report/nghien-cuu-giao-dien-hai-tang-pham-vi-phien-2026-10-18.md):
  - **Hai mẫu có sẵn trên thị trường:** mẫu "vùng chứa" giữ phiên và tệp (NotebookLM, ChatGPT Projects, Claude Projects), và mẫu chat gắn trang nội dung
    (Khanmigo, Coursera).
  - **Chưa sản phẩm nào có hai cấp lồng nhau,** nên luật ở đây là của dự án.
- **Số đo trên doc-1 từ v45 sang v53:**
  - 33 mã module vẫn còn, nhưng chỉ 2 module giữ nguyên tập khái niệm (Jaccard trung bình 0,26);
  - 202/205 `node_id` còn nguyên.

  Mã module là nhãn theo vị trí, không phải danh tính.

**Considered Options**

- *Phạm vi là ranh giới:* phiên module chỉ trả lời trong module đó. Bị bác, vì người học sẽ bị từ chối những câu tài liệu trả lời được. Điều này cũng trái
  ADR 0012 ("module đang mở là ưu tiên, không phải ranh giới").
- *Tự dời phiên* sang module của câu hỏi. Bị bác: lịch sử phiên bị xé lẻ, và người học không đoán được phiên của mình ở đâu.
- *Neo phạm vi vào mã module.* Bị bác vì số đo trên. Một phiên có thể lặng lẽ trỏ sang module khác sau khi phía pha A chạy lại.
- *Ghim phiên vào phiên bản đồ thị cũ.* Bị bác: phải giữ và đọc mãi đồ thị cũ, trong khi bài giảng và trợ lý chạy trên đồ thị hiện hành.

**Consequences**

- Lõi trợ lý phải chạy được khi không có module đang mở. Thay thẻ module bằng thẻ lộ trình, và tắt khối nhắc nền ở phạm vi lộ trình.
- Phiên phải lưu đủ mọi lượt để mở lại được. Mô hình vẫn chỉ nhận 3 lượt cuối.
- Một nội dung có thể hiện ở hai thư viện: thư viện nơi tạo, và thư viện của module chứa khái niệm của nó, kèm nhãn "tạo ở nơi khác".
- Chưa cho dời phiên giữa các phạm vi. Trường `scope` vẫn để đổi được, để thêm sau.
