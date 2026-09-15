# 01 — Thư mục theo phase và một hàm nạp chung

**What to build:** Dời 11 file prompt vào `prompts/a3/…` và `prompts/a4/…` theo bố cục ở ticket 00. Hai module nạp dùng
chung một hàm. Lượt cụm và lượt vá đọc cùng một file `a4/partition.txt`.

## Vì sao một hàm nạp chung

Phase nào tự viết cách tìm thư mục và đọc file thì mỗi phase lại có một kiểu. Đó là cách hiện trạng đã sinh ra hai
module khác nhau. Một hàm chung giữ đúng một quy ước: UTF-8, bỏ khoảng trắng đầu và cuối, đường dẫn tính từ gói.

**Blocked by:** đợt 2 của `task/a4-quan-he-mo-2a/` kết luận xong (xem ticket 00)

**Status:** done — 2026-09-15

- [x] Dời file bằng `git mv` để lịch sử theo được. Nội dung từng file **giữ nguyên từng byte**.
- [x] `a4-repair.txt` bị xoá. Lượt vá đọc `a4/partition.txt` giống lượt cụm.
- [x] Module mới `application/prompt_library.py`:
  - `PROMPT_ROOT = Path(__file__).with_name("prompts")`;
  - `load_prompt(phase: str, name: str) -> str` đọc `PROMPT_ROOT / phase / f"{name}.txt"`, UTF-8, `strip()`;
  - không tìm thấy file thì báo lỗi nêu đủ đường dẫn đã thử.

  Không đặt tên module là `prompts.py`, vì nó sẽ trùng tên với thư mục `prompts/`.
- [x] `extraction_prompt.load_prompts(few_shot_path=None)` dùng `load_prompt("a3", …)`. Few-shot mặc định là
      `a3/few-shot/default.txt`. Tham số `few_shot_path` (từ `--few-shot` hoặc `DOC2ROADMAP_EXTRACTION_FEW_SHOT`) vẫn
      nhận **đường dẫn bất kỳ** như cũ.
- [x] `canonical_prompt.canonical_prompts()` trả **đúng bốn khoá như cũ**: `merge`, `repair`, `describe`, `check`.
      `merge` và `repair` cùng lấy từ `load_prompt("a4", "partition")`. Giữ nguyên các khoá để config hash và
      `prompt_hash` của từng khâu không đổi.
- [x] Không đổi chữ nào của schema, `prompt_hash`, và nơi dùng `self.prompts[stage]`.
- [x] Test hiện có đang trỏ đường dẫn cũ thì sửa sang đường dẫn mới, giữ nguyên ý kiểm.
- [x] Toàn bộ test xanh, chặn mạng, **không ghi lại fixture nào**.

## Bằng chứng bàn giao

- `git diff --cached --name-status` nhận đủ 10 file đích là `R100`; 11 file nguồn trở thành 10 file sản phẩm vì hai
  bản sao `a4-merge.txt` và `a4-repair.txt` được hợp nhất. Blob của `a4/partition.txt` và blob cũ của
  `a4-merge.txt` cùng là `7483dbd4bc89cbc39699412505201356acaab5a9`.
- Trước khi xoá, SHA-256 của hai file phân hoạch đều là
  `4707b4f78eb88b63aff40715fc6130a2d2bca73eefd77c0e8c129d8fe30e7f1a`.
- `prompt_library.load_prompt` là nơi duy nhất nạp prompt sản phẩm theo phase; đường dẫn few-shot do người dùng truyền
  vẫn được đọc trực tiếp như trước.
- Nhóm test loader/hợp đồng A3/A4: **11/11 pass**. Không sửa hay ghi lại fixture nào; toàn suite ở ticket 04.
