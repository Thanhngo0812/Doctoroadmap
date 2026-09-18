# 10 — Fixture hợp đồng cho hai loại phiên

**What to build:** Ghi một phiên **pass chính** và một phiên **pass phụ** từ mô hình thật, rồi phát lại được khi
chặn mạng. Fixture chốt hợp đồng, nên từ đây ai đổi prompt là test đỏ.

**Blocked by:** 06, 07 — prompt phải chốt trước khi ghi.

**Status:** done — 2026-09-16

- [x] Một fixture mỗi loại phiên, ghi từ tài liệu thật bằng `gemini-3.1-flash-lite`.
- [x] Phát lại offline: không mạng, không mô hình.
- [x] `prompt_hash` tính từ **prompt sản phẩm**, không lấy từ fixture.
- [x] Đổi một ký tự trong prompt thì test đỏ, kèm nhắc phải ghi lại fixture và chấm theo luật viết trước.
- [x] Dán số lời gọi và chi phí của lượt ghi vào vé.

## Feedback nghiệm thu

- Fixture thật nằm ở `tests/fixtures/a8/baocao-canhan/main.json` và `secondary.json`; test dùng
  `ReplayEntityExtractor`, không truy cập mạng.
- Lượt ghi fixture chính: 1 lời gọi, 5.153 input token, 328 output gồm thinking, 0,00178025 USD.
- Lượt ghi fixture phụ: 1 lời gọi, 1.434 input token, 55 output gồm thinking, 0,000441 USD.
- Hash được tính lại từ prompt/schema/model/generation sản phẩm. Test cố ý đổi một ký tự của prompt và xác nhận
  fixture bị từ chối vì sai `prompt_hash`.
