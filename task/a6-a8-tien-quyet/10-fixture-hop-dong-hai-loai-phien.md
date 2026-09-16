# 10 — Fixture hợp đồng cho hai loại phiên

**What to build:** Ghi một phiên **pass chính** và một phiên **pass phụ** từ mô hình thật, rồi phát lại được khi
chặn mạng. Fixture chốt hợp đồng, nên từ đây ai đổi prompt là test đỏ.

**Blocked by:** 06, 07 — prompt phải chốt trước khi ghi.

**Status:** ready-for-agent

- [ ] Một fixture mỗi loại phiên, ghi từ tài liệu thật bằng `gemini-3.1-flash-lite`.
- [ ] Phát lại offline: không mạng, không mô hình.
- [ ] `prompt_hash` tính từ **prompt sản phẩm**, không lấy từ fixture.
- [ ] Đổi một ký tự trong prompt thì test đỏ, kèm nhắc phải ghi lại fixture và chấm theo luật viết trước.
- [ ] Dán số lời gọi và chi phí của lượt ghi vào vé.
