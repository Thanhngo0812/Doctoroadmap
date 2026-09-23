# 06 — Recall có mục tiêu

**Nguồn chân lý:** spec v2, W16–W17

**What to build:** bộ sinh ứng viên từ tên được nhắc trong câu neo, phiên pass chính gộp mục vụn, và một lần chạy lại A8
cho mỗi tài liệu với neo và bản đồ danh tính đã dời lên trước A8.

**Blocked by:** 04, 05; vé 10 — T1 (chấm mù) để biết precision thật của cạnh dư

**Status:** chờ 04, 05, T1

## Cổng nhận (khoá trước khi chạy)

1. **Q5 tăng** trên cả hai chương phát triển, báo recall tăng trên mỗi USD để so với C1 (C1 trên `doc-1`: +5 cạnh vàng /
   2,71 USD).
2. **Q4 trên cạnh mới:** chấm mù vòng hai (vé 10, T11): ngược chiều ≤ 5%, "không làm sai thứ tự học" ≥ 0,90.
3. Không cạnh vàng nào đang có bị mất.
4. Chỉ khi 1–3 đạt mà Q5 vẫn dưới 85% mới xét C1 cho `doc-2`, theo luật đã khoá ở kế hoạch cũ mục 18.

## Acceptance

- [ ] Bộ sinh ứng viên là hàm thuần có test.
- [ ] Gộp mục vụn dùng đúng `plan_main_sessions` có trần token.
- [ ] Mọi lần chạy đi qua `--allow-spend`; dán chi phí thật.
- [ ] Sửa spec A6–A8 và `spec-addendum.md` A8 cùng commit.
