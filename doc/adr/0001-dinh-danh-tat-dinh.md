---
status: accepted
---

# Định danh chunk và section theo nội dung, không theo vị trí

`chunk_id` là hạt giống provenance của bước mention map và là tham chiếu bằng chứng xuyên suốt Pha A, nên nó
phải sống sót qua các lần ingest lại. Chúng tôi băm `section_id` từ đường dẫn section, rồi băm `chunk_id` từ
**nội dung và `section_id` của section cha**
(`doc_id | parent_section_id | normalized_text | split_index | occurrence`) thay vì từ **vị trí**
(`order_index`, `char_span`) như `B0-ingestion-spec.md` §5.2 đặc tả ban đầu — vì công thức theo vị trí làm
mọi định danh phía sau đổi hết chỉ vì một đoạn được chèn thêm ở đầu tài liệu, đúng thứ mà §9 của chính spec
đó hứa sẽ không xảy ra.

## Considered Options

**Công thức gốc §5.2 — `doc_id | order_index | char_start:char_end | normalized_text`.**
Bị loại. Chèn một đoạn ở trang 1 làm dịch `order_index` và `char_span` của **mọi** block phía sau, nên toàn bộ
định danh phía sau đổi theo, kéo gãy mọi bằng chứng đã lưu từ các lần chạy trước. `section_id` ở §4.2
(`det_section_id(doc_id, reading_order, text)`) dính đúng lỗi này, và nếu chỉ vá `chunk_id` mà bỏ quên nó thì
khoá ngoại `parent_section_id` vẫn gãy. Bộ test I5 của spec **không phát hiện được** vì nó chỉ kiểm "cùng một
file chạy hai lần" — điều kiện mà công thức theo vị trí vẫn thoả.

**Băm thuần nội dung — `doc_id | normalized_text`.**
Bị loại, dù ổn định hơn (di chuyển một block sang mục khác vẫn giữ nguyên định danh). Hai đoạn văn giống hệt
nhau ở hai chương khác nhau sẽ phải dựa hoàn toàn vào bộ đếm thứ tự để phân biệt, khiến định danh của chúng
phụ thuộc vào vị trí một cách gián tiếp và khó lần ra hơn.

## Consequences

- **`doc_id` bắt buộc là định danh logic ổn định do người gọi cấp**, không được là hash nội dung file. Nếu
  `doc_id` băm từ bytes của file thì sửa một dấu phẩy trong PDF cũng sinh `doc_id` mới và toàn bộ quyết định
  này thành vô nghĩa. Hash của file gốc được ghi riêng dưới tên `source_hash` trong manifest, dùng để phát
  hiện file đã ingest và để quyết định có tăng version hay không.

- **Đổi tên một heading vẫn làm đổi định danh của mọi chunk nằm dưới nó**, vì `section_path` quyết định
  `section_id`, rồi `section_id` nằm trong khoá băm của chunk. Đây là điểm yếu còn lại và không có phương án
  nào tránh được hoàn toàn — nó là cái giá của việc dùng
  đường dẫn để phân biệt các đoạn văn trùng nội dung. Đánh đổi này được chấp nhận vì sửa tiêu đề hiếm hơn
  nhiều so với sửa nội dung.

- **Gộp leaf block làm định danh ổn định theo nhóm, không còn theo từng block.** Sửa một block đổi nội dung
  của cả chunk gộp và vì thế đổi `chunk_id` của nhóm. Đây là mất mát thật về độ ổn định, được chấp nhận để
  chunk đủ dài cho embedding và truy hồi. Ranh giới section vẫn là hàng rào: thay đổi không lan sang section
  khác.

- **Đổi luật suy cấp heading có thể đổi gần như mọi định danh.** Luật suy cấp quyết định `section_path`, từ
  đó quyết định `section_id` và mọi `chunk_id` bên dưới. Vì vậy mỗi lần đổi luật phải tăng `algorithm_id` và
  dựng lại chỉ mục phía sau; đợt suy cấp từ đánh số dùng `section-id-v3`.

- **Đổi tokenizer, `target_tokens` hoặc `max_tokens` có thể đổi ranh giới cả nhóm block.** Artifact chunk đã
  đưa cả ba vào `config_hash`, nên cấu hình mới luôn được cắt lại thay vì dùng nhầm kết quả cũ.

- Cần ba bài test mà §11 của spec gốc không có: một bài chèn đoạn vào đầu tài liệu rồi khẳng định section và
  chunk không đổi giữ nguyên định danh, một bài đổi `max_tokens` rồi khẳng định chỉ block bị cắt lại mới đổi,
  và một bài dùng hai section anh em trùng tên để bảo đảm bộ đếm chunk không rò qua ranh giới `section_id`.
  Công thức gốc trượt bài đầu tiên; công thức dùng trực tiếp `section_path` cho chunk trượt bài thứ ba.
