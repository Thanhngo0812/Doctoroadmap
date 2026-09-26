# 12 — Cạnh theo định nghĩa ở A8

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R12 · **Ai:** nhân viên · **Phụ thuộc:** 03–11 · **Chi phí mô hình:** ≈ 1–7 USD / tài liệu — chủ dự án duyệt trước khi chạy

**Trạng thái:** chờ giao

## Việc cần làm
- Dời neo (C8 v3) và danh tính lên trước A8 (W17 của spec v2): A8 nhận khái niệm đã có câu neo và bản đồ danh tính.
- Hai loại cạnh: `can_de_hieu` (căn cứ là đoạn định nghĩa/câu neo của đích, cụm trích kiểm bằng mã) và `cong_cu` (tiên quyết chỉ dùng
  trong ví dụ, bài tập, phương pháp giải — nên biết trước khi làm bài). Chỉ `can_de_hieu` ràng buộc dãy học và "cần:".
- Prompt pass chính/phụ đổi tương ứng; đăng ký lại `prompt_hash` có chủ đích.

## Nghiệm thu
- Test: cạnh có căn cứ chỉ ở ví dụ → `cong_cu`; cạnh có cụm trích trong câu neo của đích → `can_de_hieu`; cụm trích không có trong câu
  neo → bị từ chối.
- **Tôi kiểm (trên dữ liệu phát triển, sau khi chủ dự án duyệt chi):** đọc lộ trình doc-1, doc-2; Q7b doc-1 phải tăng rõ (hiện 59%) mà
  Q6 không tụt quá sàn nhiễu; chấm mù nhỏ kiểu T11 trên cạnh `can_de_hieu` mới nếu chủ dự án muốn.
