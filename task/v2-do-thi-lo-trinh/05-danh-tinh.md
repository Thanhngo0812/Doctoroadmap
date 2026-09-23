# 05 — Danh tính: gộp, tách, đa nghĩa

**Nguồn chân lý:** spec v2, W14–W15

**What to build:** bản đồ danh tính ở tầng graph cho các khái niệm trùng hoặc đa nghĩa, phán trên hai câu neo; A10 và bộ
chấm áp cùng bản đồ; gộp xong gỡ chu trình lại.

**Blocked by:** 04 (cần câu neo); vé 10 — T5 (duyệt các gộp chạm bộ vàng)

**Status:** mã xong, lượt 1 đã chạy; cổng 2 chờ T5

## Cổng nhận

1. **Q2 = 0** xung đột danh tính còn mở trong phạm vi xuất bản.
2. Mọi gộp chạm khái niệm của bộ vàng có chữ duyệt của chủ dự án.
3. Sau khi áp bản đồ: DAG (0 chu trình), và Q6 trên hai chương vàng được báo lại.

## Acceptance

- [x] Sinh ứng viên (W14) là hàm thuần có test, gồm ca `Hệ véc tơ độc lập tuyến tính` / `Độc lập tuyến tính`.
- [x] Áp bản đồ có test cho ca gộp sinh chu trình.
- [x] Bộ chấm áp bản đồ lên vàng; tệp vàng không bị sửa.
- [x] Sửa `spec-addendum.md` (A4 / tầng graph) và `CONTEXT.md` cùng commit.

## Nhật ký

### Mã (2026-09-24)

- `domain/identity.py`: `validate_identity_response`, `identity_map` (chỉ gộp nhóm mà mọi cặp đều `same`; đại diện dạy
  sớm nhất), `merge_and_break_cycles` (gỡ chu trình bằng `_feedback_edges` của A9).
- `use_cases/judge_identity.py`: stage `identity` sau `teaching`, prompt `a10/identity.txt`; **chưa nối vào composition**.
- A10 nhận stage `identity`; `score_roadmap_order` áp `identity_map` lên cạnh và đích vàng, báo
  `identity_dropped_gold_edges`; tệp vàng không đổi (có test so byte).
- Đột biến đã thử: tắt gỡ chu trình → 2 test đỏ; bỏ lọc node bị loại → 1 test đỏ.

### Lượt 1 — khoá trước khi chạy (2026-09-24)

Đầu vào: teaching lượt 2 của vé 04 (doc-1 v21, doc-2 v16, doc-3 v16, naive-bayes v34, nhap-mon-ml v34, baocao-canhan
v104). Không chạy `xstk-ch3-1` (tài liệu tập giữ lại). Ghi trước:
- **Bất biến (sai là lỗi mã, dừng):** sau gộp 0 chu trình trên mọi tài liệu; không cạnh nào trỏ tới node đã gộp.
- **Cổng 1 (Q2):** số nhóm mở + cặp phán hỏng = 0 trên mọi tài liệu. Khác 0 thì ghi là trượt, không chạy lại để "vá".
- **Cổng 2:** mọi gộp chạm khái niệm vàng (doc-1 chương 10–12, doc-2 98–115) đưa vào bảng T5; chưa bật trước khi duyệt.
- **Cổng 3:** Q6 hai chương vàng báo lại kèm sàn nhiễu U1; chênh trong sàn nhiễu không gọi là cải thiện hay tụt.
- Chi phí dự kiến < 0,1 USD (≈ 110 cặp).

### Lượt 1 — kết quả, 0,027 USD (`scripts/phan-tich-v2/chay_danh_tinh.py`)

Lần gọi đầu dừng ở A10 vì config `identity` thiếu `chunks_version` (đã sửa, có assert trong test); doc-1 được phán lại.

| tài liệu | identity → stages | cặp | phán | gộp | cạnh gỡ | mở | chu trình |
|---|---|---|---|---|---|---|---|
| doc-1 | v24 → v25 | 60 | 56 different, 3 same, 1 sense_split | 3 | 1 | 0 | 0 |
| doc-2 | v18 → v19 | 22 | 16 different, 5 same, 1 sense_split | 5 | 1 | 0 | 0 |
| doc-3, naive-bayes, nhap-mon-ml, baocao-canhan | v18, v36, v36, v106 | 11, 11, 3, 1 | tất cả different | 0 | 0 | 0 | 0 |

Gộp: doc-1 `Hệ véc tơ độc lập tuyến tính → Độc lập tuyến tính`, `Hệ véc tơ phụ thuộc tuyến tính → Phụ thuộc tuyến tính`,
`Tọa độ → Véc tơ tọa độ` (cả ba chạm vàng); doc-2 `B(V, W)`, `Null Space`, `upper triangular`, `degree of a polynomial`,
`Trace` gộp vào tên đầy đủ (không chạm vàng). **Nghi:** `Trace → Trace of a square matrix` — lý do của mô hình nói tới vết
của toán tử, mà sách định nghĩa vết toán tử riêng; chờ T5.

Đối chiếu khoá trước:
- Bất biến: 0 chu trình, 0 cạnh treo trên cả sáu tài liệu — đạt.
- Cổng 1 (Q2): 0 nhóm mở, 0 cặp phán hỏng — **đạt**.
- Cổng 2: 4 cặp chạm vàng (3 gộp + 1 sense_split) nằm trong `artifacts/a8-gold/duyet-danh-tinh.xlsx` (10 cặp) — **chờ T5**.
- Cổng 3: Q6 doc-1 2,6% (39 cạnh vàng; 1 cạnh rời vì hai đầu đã gộp) so 5,0% trước gộp; doc-2 9,8% so 8,2%. Cả hai trong
  sàn nhiễu U1 — không gọi là cải thiện hay tụt. Q7 doc-1 90%, doc-2 58%; 0 thiếu đầu.

Đọc: bước gộp nhỏ và bảo thủ (8/108 cặp); nó không phải đòn bẩy của Q6/Q7. Giá trị của nó là đồ thị không còn hai nút cho
một ý (doc-1 trước đây học `Độc lập tuyến tính` và `Hệ véc tơ độc lập tuyến tính` như hai bài). Chưa nối vào composition.
