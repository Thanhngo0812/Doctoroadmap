# v4-02 — Mọi stage ghi thời gian chạy và lời gọi mô hình

**Nguồn chân lý:** nguyên tắc số một của v4 (phút/cuốn, USD/cuốn) · **Ai:** nhân viên (ghi số), Claude (báo cáo) · **Phụ thuộc:** — ·
**Chi phí mô hình:** 0

**Trạng thái:** chờ giao.

## Vì sao (Claude, 2026-10-04)
- Muốn tối ưu phút/cuốn thì phải đo được phút theo từng khâu. Hiện chỉ cụm và nhắc tên ghi `runtime_seconds`. Các khâu gọi mô hình (A2,
  A3, A4/A5, A7, neo, danh tính, A8 chính, A8 phụ, tên khái niệm, tên module) chỉ ghi token, không ghi thời gian.
- `created_at` không dùng thay được: giữa hai stage có thời gian chờ chủ dự án duyệt chi, tạm dừng máy, dry-run.

## Việc cần làm
- Mọi stage ghi vào `stats`:
  - `runtime_seconds`: thời gian chạy thật của `execute` trong lượt tạo artifact. Nếu chạy tiếp từ điểm lưu thì cộng các đoạn chạy;
    điểm lưu giữ phần đã chạy;
  - số lời gọi mô hình, token vào, token ra, gồm cả thử lại và sửa phản hồi, theo cùng tên trường cho mọi stage (`model_calls`,
    `input_tokens`, `output_tokens`).
- Các trường này **không** vào config hash; artifact cũ vẫn tái dùng được.
- A1 (ingest) ghi số trang và thời gian parse trong manifest chunks.

## Nghiệm thu
- **Test:** mỗi stage có `runtime_seconds` và ba trường đếm; config hash không đổi khi chỉ có số đo khác; chạy tiếp từ điểm lưu thì cộng
  thời gian.
- **Chạy thử 0 USD:** dry-run một tài liệu nhỏ không làm hỏng cache.
- **Claude:** viết `scripts/do-chi-phi/bao_cao.py`, in phút và USD theo khâu cho một tài liệu từ manifest, để mọi vé v4 báo trước và sau
  bằng cùng một lệnh.
