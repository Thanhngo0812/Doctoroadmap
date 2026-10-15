# Chỉ mục mang module qua một lớp gán riêng; media đã xác nhận được hiện dù chưa gắn module

**Status:** accepted — 2026-10-15

A12 không ghi lại tệp vector. Nó sinh một **lớp gán module** cho mỗi cặp (phiên bản đồ thị, phiên bản chỉ mục). Lớp này cho mỗi chunk ba trường
`module_id`, `all_module_ids` và `module_source`. `module_source` nhận một trong ba giá trị:
- `chunk_module_map`, lấy từ bản đồ của A10;
- `hint`, lấy module của chunk dạy gần nhất đứng trước, cho chunk không dạy khái niệm nào;
- `none`.

Trường `stage_id` của chỉ mục đổi tên thành `module_id`, đúng như ADR 0010 đã hẹn.

Truy hồi **xếp ưu tiên** theo module đang mở, rồi tới các module trước, chứ **không lọc**.

Hình và bảng có cạnh `illustrates`/`tabulates` với `confirmed = true` được hiện trong bài giảng và câu trả lời, dù media chưa có `module_id`.
Media chưa xác nhận thì không bao giờ hiện cho người học.

Căn cứ:
- ADR 0002: `module_id` đứng ngoài mọi khoá băm, nên cập nhật nó không phải embed lại.
- [Báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md) mục 1.2: `chunk_module_map` chỉ phủ 28–63% chỉ mục; thêm `hint`
  thì phủ 74–99%.
- Chủ dự án chốt ngày 2026-10-11 và 2026-10-15: không chặn theo tiến độ, hiện media đã xác nhận, làm `module_hint`.

**Considered Options**

- *Ghi `module_id` thẳng vào tệp chỉ mục.* Phải sao chép tệp vector lớn (doc-4 có 671 vector 768 chiều) mỗi lần đồ thị đổi, và trộn hai vòng đời
  khác nhau vào một artifact.
- *Lọc cứng `module_index <= hiện tại`* (B2 cũ). Bị bác vì chủ dự án bỏ việc chặn theo tiến độ. Lọc cứng còn làm mất chunk bài tập và chunk không
  có module.
- *Chờ một vé riêng gắn media vào module rồi mới hiện* (A12 cũ). Lý do của điều chặn này là lọc theo tiến độ, mà lý do đó đã bỏ. Giữ chặn thì công
  cụ media của trợ lý luôn rỗng.

**Consequences**

- Chunk không có module (`none`) vẫn được truy hồi, mang nhãn vị trí "không rõ".
- Mỗi phiên bản đồ thị có lớp gán riêng. Cache bài giảng, quiz không phụ thuộc lớp này, vì chúng khoá theo ngữ cảnh đã lắp (ADR 0011).
- Gắn media vào module vẫn là việc tuỳ chọn về sau. Nếu làm thì dùng để sắp xếp, không dùng để chặn.
