# 11 — Cache gặp đầu ra không còn hợp lệ thì gọi lại

**What to build:** Khi luật kiểm chặt hơn làm một đầu ra trong cache không còn hợp lệ, lượt chạy coi đó là cache trượt và
gọi lại mô hình. Hiện nay nó dừng hẳn.

## Vì sao

Trong hàm `call` của `canonical_reasoning.py`, đầu ra lấy từ cache được kiểm lại bằng `validate(row["output"])` nằm
**ngoài** `try`. Ticket 10 làm 8 lượt phán cũ của nhánh v3 không còn hợp lệ. Dựng lại hay chạy tiếp trên kho có các
quyết định đó sẽ ném lỗi và dừng cả tài liệu. Lỗi này có từ trước, nhưng tới giờ chưa luật nào chặt lên nên chưa lộ.

**Blocked by:** 09 — Kế hoạch đợt 2. Làm song song với 10 được.

**Status:** done — 2026-09-14

- [x] Đầu ra từ cache mà `validate` ném `ValueError`, `TypeError`, `KeyError` hoặc `IndexError` thì không trả về. Bộ đếm
      `<stage>_cache_invalid` tăng một, rồi đi tiếp đường gọi thật như cache trượt.
- [x] `ModelTransportError` và các lỗi khác vẫn ném như cũ.
- [x] Dòng nhật ký của lần gọi thật mới ghi `cache_invalid_error` là lỗi đã khiến cache bị bỏ. Dòng này thay dòng cũ ở cùng
      `input_hash`, không thêm dòng trùng.
- [x] **Test:**
  - cache có đầu ra hợp lệ ⇒ 0 lời gọi, như cũ;
  - cache có đầu ra không qua luật mới ⇒ đúng 1 lời gọi mới, `<stage>_cache_invalid = 1`, lượt chạy không dừng;
  - bỏ phần sửa thì test thứ hai phải đỏ.
- [x] Toàn bộ test xanh, chặn mạng.

## Bằng chứng hoàn tất

Test sửa trực tiếp một quyết định merge đã cache thành R2 mâu thuẫn. Trước vá, lượt sau dừng bằng
`ContradictionError`; sau vá, pipeline gọi đúng một lần mới, `merge_cache_invalid = 1`, dòng mới có
`cache_invalid_error` và cùng `input_hash` chỉ còn một dòng. Cache hợp lệ vẫn 0 lời gọi.
