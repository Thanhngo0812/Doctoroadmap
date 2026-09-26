# 01 — Chạy thử có dự toán

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R10 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Vì sao
Sự cố 2026-09-26: `roadmap --allow-spend` chạy lại pass phụ A8 cho doc-2 (≈ 7,4 USD nếu để hết) mà không ai thấy trước. Chốt chặn
hiện chỉ báo stage **đầu tiên** định chi.

## Việc cần làm
- `roadmap --doc-id X --dry-run`: không gọi mô hình; đi qua chuỗi, với mỗi stage cho biết **tái dùng** (artifact cache có sẵn),
  **sẽ chạy** kèm số việc còn thiếu (cặp/khái niệm/phiên chưa có trong checkpoint) và USD ước theo giá trong `prerequisite_prompt`,
  hoặc **chưa biết** (phụ thuộc stage trước chưa có artifact).
- Mỗi use case trả tiền có phương thức lập kế hoạch thuần (đọc cache và checkpoint, đếm việc còn thiếu), dùng chung cho `--dry-run`.

## Tệp liên quan
`presentation/cli/main.py`, `composition.py`, `application/use_cases/build_learning_graph.py`, các use case A8/neo/danh tính.

## Nghiệm thu
- Test: chuỗi giả có stage cache và stage thiếu → báo đúng trạng thái từng stage; không lời gọi mô hình nào (mô hình giả ném lỗi
  nếu bị gọi).
- **Tôi kiểm:** `--dry-run` trên doc-2 phải báo pass phụ "sẽ chạy" với số cặp ≈ phần còn thiếu của checkpoint `secondary-9bb6…`.
