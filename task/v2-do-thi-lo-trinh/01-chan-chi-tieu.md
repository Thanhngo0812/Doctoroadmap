# 01 — Chặn chi tiêu ngầm

**Nguồn chân lý:** spec v2, W1

**What to build:** lệnh `roadmap` không bao giờ gọi mô hình trả tiền nếu không có `--allow-spend`; khi bị chặn, nó nói
stage nào định chi.

**Blocked by:** —

**Status:** done — 2026-09-23

## Vì sao làm trước

Sau F126 (pass phụ v4), chạy `roadmap` trên bất kỳ tài liệu nào ngoài `doc-1` sẽ lặng lẽ chạy lại pass phụ với 9 984 cặp
(~7,4 USD cho `doc-2`). Mọi vé sau đều chạy pipeline; một lệnh gõ nhầm không được phép tiêu một phần năm số dư.

## Acceptance

- [x] `SpendGuard` bọc mô hình trả tiền trong `build_learning_graph(allow_spend=...)`; lời gọi `start_session` đầu tiên
      ném `SpendNotAllowed` khi chưa cho phép. Ngoại lệ **không** kế thừa `RuntimeError`, vì `run_model_jobs` coi
      `RuntimeError` là phản hồi hỏng và sẽ nuốt nó.
- [x] Bộ điều phối gắn tên stage vào lỗi; CLI in thông báo tiếng Việt và thoát mã 2.
- [x] Stage có cache vẫn chạy được khi không có cờ.
- [x] 5 test, đều thấy đỏ trước; ba đột biến (kế thừa `RuntimeError`, bỏ gắn tên stage, bỏ chốt chặn) đều bị giết.
      Toàn suite 530/530.

## Kiểm đầu–cuối

`roadmap --doc-id doc-2` không có cờ: `lỗi: stage secondary_edges cần gọi mô hình trả tiền; chạy lại với --allow-spend
nếu muốn chi`, thoát mã 2, số phiên bản `doc-2` giữ nguyên 11, không tạo checkpoint mới. Đúng cái bẫy ~7,4 USD của F126.

## Sự cố 2026-09-26 — chi ngoài dự kiến ≈ 0,64 USD

Khi sinh lộ trình bằng chuỗi mặc định mới cho các tài liệu phát triển, tôi chạy `roadmap --allow-spend` hàng loạt mà không chạy
thử không chi trước. Với doc-2 (và doc-3), chuỗi không tái dùng cạnh cũ mà **chạy lại pass phụ A8** theo luật hiện hành — đúng
rủi ro W1 đã ghi (≈ 7,4 USD cho doc-2). Phát hiện sau khoảng 15 phút qua checkpoint `secondary-…` mới, dừng tay, diệt cả vòng
lặp: doc-2 624 cặp, 1.039 lời gọi, 1,92M token vào / 98k ra ≈ 0,627 USD; doc-3 20 lời gọi ≈ 0,007 USD. Checkpoint giữ lại (chạy
tiếp được nếu sau này quyết chạy lại pass phụ).
Bài học: trước mọi `--allow-spend` trên tài liệu có artifact cũ, chạy không cờ để xem stage nào định chi. Đề xuất (cho vé mới):
lệnh chạy thử liệt kê **mọi** stage sẽ gọi mô hình kèm dự toán số lời gọi / USD — hiện chốt chặn chỉ báo stage **đầu tiên**.
