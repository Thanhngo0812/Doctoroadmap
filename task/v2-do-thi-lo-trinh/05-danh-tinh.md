# 05 — Danh tính: gộp, tách, đa nghĩa

**Nguồn chân lý:** spec v2, W14–W15

**What to build:** bản đồ danh tính ở tầng graph cho các khái niệm trùng hoặc đa nghĩa, phán trên hai câu neo; A10 và bộ
chấm áp cùng bản đồ; gộp xong gỡ chu trình lại.

**Blocked by:** 04 (cần câu neo); vé 10 — T5 (duyệt các gộp chạm bộ vàng)

**Status:** chờ 04

## Cổng nhận

1. **Q2 = 0** xung đột danh tính còn mở trong phạm vi xuất bản.
2. Mọi gộp chạm khái niệm của bộ vàng có chữ duyệt của chủ dự án.
3. Sau khi áp bản đồ: DAG (0 chu trình), và Q6 trên hai chương vàng được báo lại.

## Acceptance

- [ ] Sinh ứng viên (W14) là hàm thuần có test, gồm ca `Hệ véc tơ độc lập tuyến tính` / `Độc lập tuyến tính`.
- [ ] Áp bản đồ có test cho ca gộp sinh chu trình.
- [ ] Bộ chấm áp bản đồ lên vàng; tệp vàng không bị sửa.
- [ ] Sửa `spec-addendum.md` (A4 / tầng graph) và `CONTEXT.md` cùng commit.
