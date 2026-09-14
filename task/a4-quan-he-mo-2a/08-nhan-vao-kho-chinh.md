# 08 — Nhận vào kho chính

**What to build:** Chỉ làm khi ticket 07 kết luận nhận. Đưa thay đổi về nhánh chính, chạy kho chính làm mẫu thứ hai, rồi
cập nhật tài liệu vận hành.

**Blocked by:** 07 — Chấm theo luật đăng ký trước (kết luận: nhận)

**Status:** không làm — ticket 07 kết luận không nhận (2026-09-14). Kho chính giữ nguyên báo cáo v7, slide v6, ML v6,
XSTK v6.

- [ ] Gộp nhánh `a4-quan-he-mo-2a` theo cách chủ dự án chọn ở bước 0.
- [ ] Chạy `doc2roadmap a4 --doc-id <doc> --gold tests/fixtures/a4/gold-blind.json` cho bốn tài liệu. Lần này gọi
      flash-lite thật và độc lập với ticket 06.
- [ ] Chấm lại bằng `a4-evaluate`: cổng 1, 3, 4 ở ticket 00 phải qua lần nữa. Trượt thì revert và báo reviewer.
- [ ] Chạy lại lần hai: `reused=true`, 0 lời gọi.
- [ ] Cập nhật báo cáo chạy thật (bảng số, tên chỉ số mới), luồng 2a, README nếu có nhắc tên chỉ số, và trạng thái các
      ticket.
- [ ] Toàn bộ test xanh, chặn mạng.
