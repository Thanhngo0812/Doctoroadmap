# 09 — A10: lắp lộ trình và trang xem tĩnh

**What to build:** Từ đồ thị đã validate ra **lộ trình học**: tầng, stage, và `stage_id` gắn ngược về chunk. Kèm
một trang HTML tĩnh để người đọc kiểm được kết quả bằng mắt.

Luật ở spec D12.

> **Phạm vi (chủ dự án chốt 2026-09-17, hướng c):** vé này là **bản tối thiểu** để sản phẩm có lộ trình xem được. Nó
> không thuộc phần tuyên bố khoa học, và thiết kế A10 sẽ được nghiên cứu riêng sau đợt này. Đừng tối ưu thêm ngoài D12;
> chỉ sửa theo review vòng 30 (F88: xếp tầng trên đồ thị co, tầng theo đường dài nhất).

**Blocked by:** 08.

**Status:** done — 2026-09-16

- [x] Xếp tầng Kahn **chỉ trên đồ thị con `requires` của node `learnable`**.
- [x] F88: co SCC hai node trước Kahn; các node trong khối cùng tầng; từ chối SCC lớn hơn hai node còn sót.
- [x] Stage là giao của một tầng với một cụm chủ đề, trần 5–8 khái niệm.
- [x] **Phân biệt hai loại node không có tiên quyết:** đã được xét mà không tìm thấy, và chưa từng nằm trong
      phiên nào. Loại thứ hai phải được báo, không lặng lẽ rơi vào tầng 1.
- [x] `stage_id` gắn về chunk: stage sớm nhất, kèm danh sách đầy đủ.
- [x] Trang HTML tĩnh sinh từ artifact: stage, khái niệm trong stage, cạnh kèm chunk bằng chứng, cờ, và cạnh bị
      đánh dấu thừa.
- [x] Test theo hai seam; đột biến tối thiểu: xếp tầng trên cả cạnh kiểu mở, gộp hai loại node không tiên quyết
      làm một, bỏ trần stage.

## Feedback nghiệm thu

- CLI công khai duy nhất: `doc2roadmap roadmap --doc-id <id> --stop-after clusters|mentions|edges|stages`.
  Orchestrator chạy đúng bốn stage của D1 và dùng checkpoint của từng stage.
- Chạy lại `baocao-canhan` sau F88 hoàn tất graph `v78`: quality gate đạt, `roadmap_mode=requires`; SCC
  `ERD ↔ Thiết kế Cơ sở dữ liệu` được co, cả hai ở layer 1 và cùng stage; kết quả có 5 tầng, 19 stage, 0 node chưa
  được xét. Chạy lại dùng đúng v78 với `reused=true`.
- Trang `roadmap.html` tĩnh nằm cùng artifact, hiển thị stage, node, cạnh/chunk bằng chứng, cờ và đường thay thế
  của cạnh thừa.
- Mutation đã thử và đều bị test bắt: cho cạnh kiểu mở lọt vào xử lý tầng/coverage; gộp `unreviewed` với
  `reviewed_no_prerequisite`; bỏ trần stage.
