# 09 — A10: lắp lộ trình và trang xem tĩnh

**What to build:** Từ đồ thị đã validate ra **lộ trình học**: tầng, stage, và `stage_id` gắn ngược về chunk. Kèm
một trang HTML tĩnh để người đọc kiểm được kết quả bằng mắt.

Luật ở spec D12.

**Blocked by:** 08.

**Status:** ready-for-agent

- [ ] Xếp tầng Kahn **chỉ trên đồ thị con `requires` của node `learnable`**.
- [ ] Stage là giao của một tầng với một cụm chủ đề, trần 5–8 khái niệm.
- [ ] **Phân biệt hai loại node không có tiên quyết:** đã được xét mà không tìm thấy, và chưa từng nằm trong
      phiên nào. Loại thứ hai phải được báo, không lặng lẽ rơi vào tầng 1.
- [ ] `stage_id` gắn về chunk: stage sớm nhất, kèm danh sách đầy đủ.
- [ ] Trang HTML tĩnh sinh từ artifact: stage, khái niệm trong stage, cạnh kèm chunk bằng chứng, cờ, và cạnh bị
      đánh dấu thừa.
- [ ] Test theo hai seam; đột biến tối thiểu: xếp tầng trên cả cạnh kiểu mở, gộp hai loại node không tiên quyết
      làm một, bỏ trần stage.
