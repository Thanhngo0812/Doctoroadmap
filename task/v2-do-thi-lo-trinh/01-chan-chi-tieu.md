# 01 — Chặn chi tiêu ngầm

**Nguồn chân lý:** spec v2, W1

**What to build:** lệnh `roadmap` không bao giờ gọi mô hình trả tiền nếu không có `--allow-spend`; khi bị chặn, nó nói
stage nào định chi.

**Blocked by:** —

**Status:** ready

## Vì sao làm trước

Sau F126 (pass phụ v4), chạy `roadmap` trên bất kỳ tài liệu nào ngoài `doc-1` sẽ lặng lẽ chạy lại pass phụ với 9 984 cặp
(~7,4 USD cho `doc-2`). Mọi vé sau đều chạy pipeline; một lệnh gõ nhầm không được phép tiêu một phần năm số dư.

## Acceptance

- [ ] `SpendGuard` bọc mô hình trả tiền trong `build_learning_graph(allow_spend=...)`; lời gọi `start_session` đầu tiên
      ném `SpendNotAllowed` khi chưa cho phép.
- [ ] Bộ điều phối gắn tên stage vào lỗi; CLI in thông báo tiếng Việt và thoát mã khác 0.
- [ ] Stage có cache vẫn chạy được khi không có cờ.
- [ ] Test: bị chặn đúng stage; có cờ thì chạy; stage có cache không bị chặn. Mỗi test đã thấy đỏ trước.
