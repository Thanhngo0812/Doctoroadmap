# 01 — Thư mục theo phase và một hàm nạp chung

**What to build:** Dời 11 file prompt vào `prompts/a3/…` và `prompts/a4/…` theo bố cục ở ticket 00. Hai module nạp dùng
chung một hàm. Lượt cụm và lượt vá đọc cùng một file `a4/partition.txt`.

## Vì sao một hàm nạp chung

Phase nào tự viết cách tìm thư mục và đọc file thì mỗi phase lại có một kiểu. Đó là cách hiện trạng đã sinh ra hai
module khác nhau. Một hàm chung giữ đúng một quy ước: UTF-8, bỏ khoảng trắng đầu và cuối, đường dẫn tính từ gói.

**Blocked by:** đợt 2 của `task/a4-quan-he-mo-2a/` kết luận xong (xem ticket 00)

**Status:** todo

- [ ] Dời file bằng `git mv` để lịch sử theo được. Nội dung từng file **giữ nguyên từng byte**.
- [ ] `a4-repair.txt` bị xoá. Lượt vá đọc `a4/partition.txt` giống lượt cụm.
- [ ] Module mới `application/prompt_library.py`:
  - `PROMPT_ROOT = Path(__file__).with_name("prompts")`;
  - `load_prompt(phase: str, name: str) -> str` đọc `PROMPT_ROOT / phase / f"{name}.txt"`, UTF-8, `strip()`;
  - không tìm thấy file thì báo lỗi nêu đủ đường dẫn đã thử.

  Không đặt tên module là `prompts.py`, vì nó sẽ trùng tên với thư mục `prompts/`.
- [ ] `extraction_prompt.load_prompts(few_shot_path=None)` dùng `load_prompt("a3", …)`. Few-shot mặc định là
      `a3/few-shot/default.txt`. Tham số `few_shot_path` (từ `--few-shot` hoặc `DOC2ROADMAP_EXTRACTION_FEW_SHOT`) vẫn
      nhận **đường dẫn bất kỳ** như cũ.
- [ ] `canonical_prompt.canonical_prompts()` trả **đúng bốn khoá như cũ**: `merge`, `repair`, `describe`, `check`.
      `merge` và `repair` cùng lấy từ `load_prompt("a4", "partition")`. Giữ nguyên các khoá để config hash và
      `prompt_hash` của từng khâu không đổi.
- [ ] Không đổi chữ nào của schema, `prompt_hash`, và nơi dùng `self.prompts[stage]`.
- [ ] Test hiện có đang trỏ đường dẫn cũ thì sửa sang đường dẫn mới, giữ nguyên ý kiểm.
- [ ] Toàn bộ test xanh, chặn mạng, **không ghi lại fixture nào**.
