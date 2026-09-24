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

## T1 — kết quả nhận 2026-09-24 (bằng chứng đầu vào, không phải cổng của vé này)

Chấm bằng `scripts/cham-mu/cham_bang.py` và `phan_tich_hai_nguoi.py` trên bốn bản `cham-mu-doc-{1,2}-A{1,2}-output.xlsx`.
Bảng T1 không có dấu hiệu AI trong ô nào, nhưng **chưa có xác nhận là người chấm** (bản A2 lưu cùng phút với T4/T5 do AI
điền) và không bản nào ghi giờ làm.

| | doc-1 (29 cạnh dư) | doc-2 (16 cạnh dư) |
|---|---|---|
| "không làm sai thứ tự học" (A1 / A2) | 0,836 / 0,718 | 0,898 / 0,867 |
| ngược chiều (A1 / A2) | 7% / 0% | 14% / 6% |
| cả hai cùng nói ngược | 0/28 (Wilson 0–12%) | 0/14 (0–22%) |
| ít nhất một nói "không cần thứ tự" | 15/28 = 54% (36–70%) | 6/14 = 43% (21–67%) |
| đồng thuận mức thô, kappa | 19/28, +0,40 | 8/14, +0,19 |
| cạnh vàng lấy mẫu được xác nhận lại | 10/12, 13/13 | 7/7, 7/7 |
| vàng bỏ sót thật (cặp ngẫu nhiên ngoài bao đóng vàng) | 4/14, 1/15 | 1/6, 0/7 |

Đọc:
- **Q4 hiện chưa đạt** (≥ 0,90 và ngược ≤ 5%) theo cả hai người trên cả hai chương.
- Lỗi chính của cạnh dư **không phải ngược chiều** (không cạnh nào cả hai cùng nói ngược) mà là **thừa ràng buộc**: khoảng
  một nửa cạnh dư bị ít nhất một người cho là "không cần thứ tự". Loại lỗi này không làm sai Q6 nhưng kéo lộ trình tới
  mục tiêu dài ra (Q7 / `roadmap-target`).
- Hai người bất đồng chủ yếu ở ranh "đúng chiều" và "không cần thứ tự" (doc-1: 8/9 ca bất đồng) — ranh giới đó chủ quan,
  nên Q4 có nhiễu người lớn; kappa 0,19 trên doc-2 là thấp.
- Nhãn cũ "mức vàng bỏ sót nền" của `cham_bang.py` đếm cả cặp đã nằm trong bao đóng vàng (doc-1: 57%); đã sửa nhãn. Vàng
  bỏ sót thật nhỏ: 1–4 cặp / 14–15.
- **Hệ quả cho vé 06:** thêm cạnh mới có rủi ro chính là thừa ràng buộc, không phải ngược chiều. Bộ sinh ứng viên cần ưu
  tiên độ chính xác; cổng 2 (Q4 trên cạnh mới, chấm mù vòng hai) giữ nguyên. Luật C1 cho `doc-2` không đổi: chỉ xét khi
  cổng 1–3 đạt mà Q5 vẫn dưới 85%.
