# Tên và mô tả module do LLM đặt, cho cả đồ án lẫn seminar

**Status:** accepted — 2026-10-15

LLM đặt tên và viết mô tả 1–2 câu cho **mọi** module. Mỗi lời gọi nhận năm nhóm đầu vào:
- danh sách khái niệm của module, dùng `display_name` kèm mô tả A5;
- đường mục của tác giả;
- 3–5 tên ứng viên do mã xếp hạng;
- tên và khái niệm của module ±1, chỉ để đối chiếu;
- các ràng buộc, viết đúng bằng giá trị mã kiểm.

Nếu module trùng đúng một mục sách, mặc định giữ tiêu đề tác giả. Ngoại lệ là khi tiêu đề là nhãn chung, trùng với module kề, hoặc chỉ là mã.

Mã kiểm năm luật:
- từ vựng có căn cứ;
- không mượn từ module kề;
- `node_ids` của câu mô tả hợp lệ;
- hình thức tên (≤ 60 ký tự, không trùng ±2, không là nhãn đánh số);
- mảnh tên nguyên vẹn.

Hỏng luật nào thì đi đường lùi tối giản: tiêu đề tác giả, hoặc 2–3 tên khái niệm, kèm mô tả khuôn.

Bỏ số đánh mục khỏi tên và giữ riêng trong `section_code`.

Seminar dùng cùng tên này: việc đặt tên được coi là sau A10.

Căn cứ:
- Chủ dự án chốt ngày 2026-10-11 ("sau A10 cứ LLM thoải mái, nên cách tốt nhất cho đặt tên vẫn cứ là LLM") và ngày 2026-10-15 (câu Q1: seminar
  cũng dùng tên do LLM đặt).
- [Báo cáo tên module](../../report/nghien-cuu-ten-va-mo-ta-module-2026-10-11.md), mục 6.1a và 7.6 đã sửa.

**Considered Options**

- *R7 hiện hành:* tên nền là tiêu đề mục; LLM chỉ chọn 1–3 tên khái niệm khi tên nền trùng hoặc chỉ là mã. Phương án này để lọt các lỗi đo ở
  báo cáo, mục 2:
  - nhảy cấp vì trần 12 token;
  - mảnh tên ghép;
  - "Tính chất 3";
  - không có mô tả.
- *Ba tầng: tất định trước, LLM chỉ khi kém tin cậy.* Đây là khuyến nghị ban đầu của báo cáo, vì nó phục vụ cả seminar không LLM. Bị thay theo
  quyết định của chủ dự án.
- *LLM tự do không có luật kiểm.* Bị bác: rủi ro mượn nội dung module kề là có thật (Shi và cộng sự, ICML 2023), và tiêu đề tác giả thường được
  người đọc ưa hơn (Branavan và cộng sự, ACL 2007).

**Consequences**

- Ràng buộc "Pha A không LLM, kể cả đặt tên module" của seminar nay hiểu là không áp cho khâu tên. Báo cáo seminar phải ghi rõ ranh giới mới này.
- Spec v3 R7 (cơ chế tên) và câu lý do của nó được thay bằng [spec Pha B](../pha-b-spec.md) mục 2.
- Chi phí đặt tên tăng từ vài lời gọi lên một lời gọi mỗi module: doc-4 khoảng 0,035–0,059 USD, ước. Khâu tên vẫn qua chốt chi và `--dry-run`.
- Luật quyết định khi thí nghiệm: không tự bỏ LLM nếu thua bản tất định. Ta báo đánh đổi bằng số, chủ dự án quyết. Thí nghiệm chỉ chọn biến thể
  LLM, ví dụ có hay không có đối chứng ±1.
- Lỗi cây mục (A1/A2) vẫn phải sửa ở gốc. LLM chỉ làm tên tốt hơn khi đầu vào đúng.
