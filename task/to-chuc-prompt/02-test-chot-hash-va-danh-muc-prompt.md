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

**Status:** done — 2026-09-15

- [x] **Hash vàng.** Giá trị lấy trên code **trước khi dời** file (chạy một lần trên bản ở ticket 00), rồi ghi cứng vào
      test:
  - A3: `prompt_hash` với few-shot mặc định, `statistics` và `technical-report`, cùng một `model_id` và `generation`
    cố định trong test;
  - A4: `CanonicalReasoning.prompt_hash(stage, schema)` cho `merge`, `repair`, `describe`, `check`, với model giả có
    `model_id` cố định.

  Sau khi dời, test phải xanh mà không sửa số nào. Đó chính là bằng chứng không hash nào đổi. Thông báo lỗi của test ghi
  rõ: *"đổi prompt là đổi hành vi — ghi lại fixture hợp đồng, chạy lại, chấm theo luật viết trước"*.
- [x] **Danh mục.** Mọi file `.txt` dưới `prompts/` phải được nạp bởi A3 hoặc A4; mọi tên được nạp phải có file. Thấy file
      thừa hoặc file thiếu thì test nêu đúng tên.
- [x] **Lượt vá dùng chung file.** `canonical_prompts()["repair"] == canonical_prompts()["merge"]`, và trong
      `prompts/a4/` chỉ có một file cho phân hoạch.
- [x] Mỗi test phải hỏng khi phá đúng điều nó giữ. Nộp danh sách đột biến đã thử:
  - thêm một dấu cách vào `a4/partition.txt`;
  - thêm một file `.txt` lạ;
  - trỏ `repair` sang file khác.
- [x] Toàn bộ test xanh, chặn mạng.

## Bằng chứng bàn giao

Hash vàng được chụp **trước khi dời file** với model `golden-model`, `temperature=0.0` và
`max_output_tokens=8192`, sau đó giữ nguyên trong test:

| Phase/biến thể | Hash |
|---|---|
| A3 `default` | `f44cf4e10d19cf697dac08dfdcd7e91a810913f2d435dbf56bf969a082d50399` |
| A3 `statistics` | `27ba75c246fd190724e42e540421f31b660b60b15b7708ea786e8cf1d100ce18` |
| A3 `technical-report` | `12df3220b52d5be6789524a078d8877f921f51aad205c64cbcb0244833461fd6` |
| A4 `merge` | `068e51fe7021257c0ccd8de8d21dbfd25b84b31ff499427661fd70d864abec31` |
| A4 `repair` | `068e51fe7021257c0ccd8de8d21dbfd25b84b31ff499427661fd70d864abec31` |
| A4 `describe` | `94b1ffe0a23feab8d335136141de8eb904945f38eadd383e1eab3ab10a7d79d2` |
| A4 `check` | `f01acab2cc39818cef30ce3ed16ad618b3ec24d4b488ab6126ca2ece0902ac0c` |

Ba đột biến đã được chạy rồi khôi phục:

1. Thêm khoảng trắng bên trong `a4/partition.txt`: test hash đỏ ở cả `merge` và `repair`, kèm đúng cảnh báo bắt buộc.
2. Thêm `a4/unknown.txt`: test danh mục đỏ và nêu đúng file thừa.
3. Cho `repair` đọc `describe`: test dùng chung prompt đỏ.

Sau khôi phục, `tests/unit/application/test_prompt_library.py`: **3/3 pass**; test đầu tiên đã đỏ trên code cũ vì
`prompt_library` chưa tồn tại, nên không phải guard chỉ được nhìn thấy ở trạng thái xanh.
