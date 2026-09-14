# 01 — Spec và ADR 0007: quan hệ kiểu mở ở 2a

**What to build:** Sửa tài liệu thiết kế cho khớp hợp đồng mới trước khi có dòng code nào, để nhân viên cài theo spec
chứ không theo trí nhớ của cuộc trao đổi.

**Người làm:** Claude (reviewer)

**Blocked by:** Bước 0 — chủ dự án chốt commit mốc hay không

**Status:** todo. Chủ dự án chấp nhận v3 cộng luật kiểm nhất quán (ticket 14, 2026-09-14), nên ticket này phải xong
trước khi ticket 15 gộp nhánh vào `main`.

Ngoài các mục ở dưới, spec và ADR phải có thêm:
- luật nhất quán R1, R2 cùng tập kiểu đồng nhất;
- cơ chế thử lại rồi hoãn cụm, và phần sửa cache;
- quyết định của chủ dự án kèm số liệu: precision gộp 0,946, chấp nhận thấp hơn ngưỡng cũ 0,95;
- các giới hạn đã biết: hai kiểu gộp sai hệ thống, F83, bộ vàng do Claude gán.

- [ ] **Spec A4/A5, D4:**
  - rubric: *cha–con*, *anh em / liên quan* và *khác* đều là hai node;
  - quan hệ giữa hai node tách riêng là quan hệ kiểu mở, có câu trích làm bằng chứng;
  - `subtype_of` nghĩa là "là một loại / dạng / biến thể / trường hợp riêng";
  - schema đầu ra mới;
  - validator tách hai lớp: lỗi phân hoạch thì thử lại rồi hoãn cả cụm; lỗi quan hệ thì chỉ loại quan hệ đó.
- [ ] **D5:** lượt vá dùng cùng schema, và quan hệ từ lượt vá được giữ như ở lượt cụm.
- [ ] **D7:**
  - nguồn gốc cạnh `origins`;
  - gộp với cạnh A3 cùng bộ ba;
  - F75 chỉ áp cho `subtype_of`;
  - chất lượng quan hệ 2a chưa đo được bằng bộ vàng, và 2b phải kiểm lại mọi quan hệ.
- [ ] **Addendum:** ví dụ JSON của hợp đồng 2a; bước kiểm của code; bước 1 của 2b nói rõ quan hệ 2a cũng là đề xuất.
- [ ] **ADR 0007** — "2a đề xuất quan hệ kiểu mở; `subtype_of` không còn kênh riêng":
  - bối cảnh: số đo ở ticket 00;
  - quyết định;
  - hệ quả;
  - hai phương án đã loại: cấm bằng prompt (mô hình im lặng, mất cặp đúng) và cho agent tự đọc chunk bằng tool (phá
    thiết kế một lời gọi mỗi cụm, trong khi đầu vào không phải chỗ tắc).
- [ ] Luồng 2a (`report/luong-chi-tiet-agent-2a.md`): schema, bước kiểm, bảng chỉ số.
- [ ] Feedback: thêm con trỏ tới thư mục task này, và một dòng trong `feedback/README.md`.
