# 04 — Prompt v3 và fixture hợp đồng `llm-v3`

**What to build:** Thay prompt merge/vá bằng v3 nguyên văn, rồi ghi lại bốn fixture hợp đồng với mô hình thật để test
phát lại khớp hợp đồng mới.

## Vì sao phải nguyên văn

Luật đánh giá ở ticket 00 được viết cho đúng văn bản v3. Sửa một chữ là luật mất giá trị, vì khi đó ta chấm một prompt
chưa đăng ký.

**Blocked by:** 01 — Spec và ADR 0007; 02 — Schema; 03 — Lắp cạnh

**Status:** done

- [x] `a4-merge.txt` và `a4-repair.txt` là đúng văn bản v3 ở ticket 00, chỉ khác được ký tự xuống dòng. Thấy cần sửa
      chữ nào thì báo reviewer trước, không tự sửa.
- [x] Ghi bốn fixture (merge, repair, describe, check) bằng `scripts/record_a4_fixture.py` vào
      `tests/fixtures/a4/llm-v3/`. Việc này gọi flash-lite thật, 4 lời gọi.
- [x] Test hợp đồng và script ghi trỏ sang `llm-v3`. Xoá `llm-v2`, theo bài học F77: không để lại fixture không ai dùng.
- [x] Test hợp đồng khẳng định hình dạng mới:
  - đầu ra có `relations`;
  - mỗi quan hệ trong fixture hoặc qua validator, hoặc bị loại kèm lý do;
  - không nhóm nào mất.
- [x] Giữ test F57: đổi khung prompt thì phát lại phải hỏng.
- [x] Toàn bộ test xanh, chặn mạng.

Đã ghi đúng 4 fixture bằng `gemini-3.1-flash-lite`; phát lại chặn mạng xanh 4/4. Tám file `llm-v2` cũ đã xoá.
