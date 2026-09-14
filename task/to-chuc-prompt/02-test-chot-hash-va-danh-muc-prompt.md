# 02 — Test chốt: hash vàng, danh mục prompt, lượt vá dùng chung file

**What to build:** Ba test giữ trật tự lâu dài:
- sửa prompt mà không cố ý thì test đỏ;
- có file prompt không ai dùng thì test đỏ;
- lượt vá tách khỏi prompt của lượt cụm thì test đỏ.

## Vì sao cần test hash vàng

Cả bốn lần đổi prompt phân hoạch trước đây đều làm flash-lite đổi cách gộp. Hash vàng biến việc sửa prompt thành một
việc phải làm **có chủ đích**: người sửa phải cập nhật số trong test, và thấy ngay nhắc nhở phải ghi lại fixture và chấm
lại.

**Blocked by:** 01 — Thư mục theo phase và hàm nạp chung

**Status:** todo

- [ ] **Hash vàng.** Giá trị lấy trên code **trước khi dời** file (chạy một lần trên bản ở ticket 00), rồi ghi cứng vào
      test:
  - A3: `prompt_hash` với few-shot mặc định, `statistics` và `technical-report`, cùng một `model_id` và `generation`
    cố định trong test;
  - A4: `CanonicalReasoning.prompt_hash(stage, schema)` cho `merge`, `repair`, `describe`, `check`, với model giả có
    `model_id` cố định.

  Sau khi dời, test phải xanh mà không sửa số nào. Đó chính là bằng chứng không hash nào đổi. Thông báo lỗi của test ghi
  rõ: *"đổi prompt là đổi hành vi — ghi lại fixture hợp đồng, chạy lại, chấm theo luật viết trước"*.
- [ ] **Danh mục.** Mọi file `.txt` dưới `prompts/` phải được nạp bởi A3 hoặc A4; mọi tên được nạp phải có file. Thấy file
      thừa hoặc file thiếu thì test nêu đúng tên.
- [ ] **Lượt vá dùng chung file.** `canonical_prompts()["repair"] == canonical_prompts()["merge"]`, và trong
      `prompts/a4/` chỉ có một file cho phân hoạch.
- [ ] Mỗi test phải hỏng khi phá đúng điều nó giữ. Nộp danh sách đột biến đã thử:
  - thêm một dấu cách vào `a4/partition.txt`;
  - thêm một file `.txt` lạ;
  - trỏ `repair` sang file khác.
- [ ] Toàn bộ test xanh, chặn mạng.
