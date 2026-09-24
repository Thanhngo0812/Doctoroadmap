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
Chủ dự án xác nhận 2026-09-24: hai người thật chấm riêng. Không bản nào ghi giờ làm.

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

## Chẩn đoán offline trước khi xây (2026-09-24, 0 USD)

Trên đồ thị validated hiện hành (doc-1 v9, doc-2 v6), cạnh vàng không có đường đi trong đồ thị máy: doc-1 8/40, doc-2 27/61.

**Vì sao thiếu** (S = hai đầu cùng một phiên pass chính; A = cặp nghi vấn đã hỏi ở pass phụ; P = nghi vấn chưa hỏi):
- doc-1: 4 SA (đã hỏi, bị trả "không"), 4 chưa từng là ứng viên. doc-1 đã hỏi hết cặp nghi vấn (C1).
- doc-2: 10 cùng phiên chính (8 trong đó là nghi vấn chưa hỏi), 3 nghi vấn khác phiên chưa hỏi, 14 chưa từng là ứng viên.

**Trần cấu trúc:** pass chính loại mọi cạnh mà chunk căn cứ không nhắc cả hai đầu (`prerequisites.py:162`,
`evidence_missing_both_endpoints`; spec A6–A8 dòng 377), và cặp nghi vấn chỉ sinh từ đồng xuất hiện. Cạnh vàng thiếu
**không có chunk nào nhắc cả hai đầu**: doc-1 4/8, doc-2 16/27 — với luật hiện tại, không bộ sinh ứng viên hay pass nào tạo
được chúng.

**Các bộ sinh ứng viên đã đo (không gọi mô hình):**

| bộ sinh | doc-1 | doc-2 |
|---|---|---|
| hỏi hết nghi vấn chưa hỏi (C1) | 0 cặp (đã hỏi hết) | 9.419 cặp ≈ 7,1 USD, bắt tối đa 11/27 → Q5 ≤ 74% |
| chỉ nghi vấn cùng phiên chính | 0 | 8.131 cặp ≈ 6,2 USD, tối đa 8/27 |
| tên A trong mô tả / câu neo của B (W16 bước 1) | 949 cặp, 6/8 | 2.732 cặp, 4/27 |
| tên A trong chunk định nghĩa / chunk dạy của B | 1.206 cặp, 2/8; 0,2% là vàng | 3.265 cặp, 2/27; 0,2% là vàng |

**Giả thuyết đã bác:** "vàng nhiều cạnh yếu kéo Q5 xuống" — cạnh `strong` còn được phủ kém hơn (doc-1 9/14, doc-2 7/14).
"Vàng nhiễu do người gán" — ở doc-2, cạnh cả hai người gán độc lập cùng chọn cũng chỉ 27/46 = 59% (doc-1: 20/23 = 87%).

**Hệ quả:** W16 bước (1)–(3) không đưa doc-2 tới Q5 85%; C1 có trần 74% với 7 USD. Muốn vượt phải nới luật "chunk căn
cứ nhắc cả hai đầu" cho một loại cạnh mới (định nghĩa của B dùng A một cách ngầm) — thay đổi hợp đồng chống bịa của A8,
cần chủ dự án quyết trước khi xây. Chờ quyết định.
