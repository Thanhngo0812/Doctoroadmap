# T10 + 07 v2 — Giao thức khoá cấu hình và chạy tập giữ lại (chuỗi v3)

**Nguồn chân lý:** spec v2 W18–W19 (tập giữ lại mở một lần); spec v3 R1–R17. Giao thức này thay phần chạy của vé v2
[07](../v2-do-thi-lo-trinh/07-xac-nhan-tap-giu-lai.md) và [07b](../v2-do-thi-lo-trinh/07b-cau-hinh-khoa.md) cho chuỗi v3.
**Ai:** tôi soạn và chấm · nhân viên chạy · chủ dự án duyệt khoá, chi và T14.
**Chi phí:** dự toán theo bậc bằng dry-run; trần chi do chủ dự án duyệt ở bậc 0.

**Trạng thái:** soạn 2026-10-01, **chưa khoá**. Các ô "chờ vé 12" điền lúc khoá.

## Vì sao phải viết trước
- Mọi chỉnh sửa v3 dựa trên sáu tài liệu phát triển (bộ vàng doc-1, doc-2), nên số đo trên đó thiên lệch.
- Tập giữ lại là phép đo duy nhất không thiên lệch: hai tài liệu, vàng đã khoá, chưa ai mở. Vì vậy **chỉ chạy một lần**.
- Luật chấm và cách đọc kết quả viết trước khi chạy, để không đọc theo ý muốn.
- Mọi sửa đổi sau khi thấy số là hậu kiểm, báo tách riêng, không thay kết quả chính.

## Tập giữ lại

| | phạm vi vàng | tệp | trạng thái |
|---|---|---|---|
| `xstk-ch3-1` (xác suất thống kê) | cấp 2, dải 10–13 (mục 2.1–2.4), 26 đích | `xstk-ch3-1-chuong-10-13-hoi-y-output.xlsx` | chuyển JSON bằng `a8-gold-check` **ngay trước bậc 5**, không sớm hơn |
| `doc-4` (giáo trình Triết học Mác–Lênin) | Chương VIII, 47 đích, 72 cạnh | `doc-4-chuong-8-vang.json` | khoá 2026-09-25, SHA-256 `df0c6cb9…` (băm lại 2026-10-01: khớp) |
| T13 liệt kê mù Q3 | xstk 2.1/2.3/2.4; doc-4 VII-IV, VII-VII, XII-I | `liet-ke-mu-giu-lai.md` | SHA-256 `40893176…`, chưa chấm |

- doc-4 không phải sách toán: bài kiểm cũng đo việc luồng có tổng quát sang lĩnh vực khác không.
- SHA-256 đầy đủ của mọi tệp nhãn có trong bảng khoá. Tệp chỉ được băm, không mở.

## Điều kiện bắt đầu (tất cả phải đúng)
1. Vé 12 nghiệm thu xong trên sáu tài liệu phát triển (pass phụ đầy đủ, A9/A10, tôi đọc). Vé 09d đạt.
2. Toàn bộ `tests/unit` + `tests/integration` xanh trên commit sẽ khoá; cây làm việc sạch.
3. Bảng khoá đã sinh bằng `scripts/khoa-cau-hinh/tao_bang.py` (không `--nhap`). `prompt_hash` trong bảng khớp manifest của lượt nghiệm
   thu vé 12; lệch là dừng. Chủ dự án đã duyệt.
4. CLI chính nạp được quyết định duyệt danh tính (`roadmap --identity-review`) cho T14.

## Cách chạy — một lần, theo bậc, không đổi cấu hình giữa các bậc
- **Bậc 0 — khoá (T10):**
  - Sinh bảng khoá vào `T10-cau-hinh-khoa.md`, ghi commit vào giao thức này.
  - Chủ dự án duyệt và đặt trần chi của lượt (đề xuất 50 USD trên sổ chi riêng).
- **Bậc 1 — vai trò vùng và cây mục**, theo đúng đường đã dùng cho doc-2:
  - A3–A5 và bộ vàng gắn với version chunks cũ (xstk v2, doc-4 v3), nên **giữ nguyên** version đó.
  - Ingest lại bằng mã đã khoá chỉ để làm cây tham chiếu. Dùng lệnh mặc định, không cờ theo tài liệu. Nếu mã khoá vẫn cần ngoại lệ cũ
    `--heading-scheme vn-textbook` cho doc-4 thì ghi vào bảng khoá trước khi chạy.
  - `label-roles` gán vai trò và chuyển sang chunk cũ bằng khớp văn bản (vé 14b). Tên mục lấy từ cây tham chiếu (vé 09b/09c).
- **Bậc 2:** dry-run cả chuỗi. Chủ dự án duyệt dự toán phần trước A8, rồi chạy `--allow-spend` tới hết danh tính: clusters → mentions →
  provenance → neo → danh tính.
- **Bậc 2b — T14, trước A8:**
  - Chủ dự án duyệt các gộp danh tính chạm khái niệm của bộ vàng giữ lại, bảng kiểu T5. Người duyệt chỉ thấy cặp gộp, không thấy cạnh vàng.
  - Sau đó chạy lại danh tính bằng `--identity-review` (rẻ).
  - Lý do đặt ở đây: trong chuỗi v3, danh tính đứng **trước** A8. Duyệt sau A8 như kế hoạch v2 sẽ buộc chạy lại A8.
- **Bậc 3:** dry-run A8, lúc này có số thật. Chủ dự án duyệt, rồi chạy A8 chính + phụ → A9 → tên khái niệm → A10 → tên module, trên danh
  tính đã duyệt.
- **Trong suốt bậc 1–3**, nhân viên chỉ báo trạng thái, số đếm và chi phí, không đọc nội dung đồ thị.
- **Sự cố:**
  - sập giữa chừng → chạy tiếp từ checkpoint, không đổi cấu hình;
  - lỗi mã chặn chạy → dừng, báo. Bản sửa là hậu kiểm, và kết quả phải ghi "không sạch" kèm lý do.

## Chấm — đã chốt trước
**Bậc 5:** chuyển bảng hội ý xstk thành JSON, ghi SHA-256; băm lại vàng doc-4. Sau đó chấm tự động. Báo cáo ghi rõ script và commit
đã dùng.

**Lệnh chấm** (một lệnh cho Q6, Q7, Q7b, đường cơ sở, P/R cạnh, Q2, kèm Wilson 95%; dùng y hệt cho tài liệu phát triển):
`scripts/doc-lo-trinh/cham_tap_giu_lai.py <doc> <tệp vàng> --goc=<kho> --phien-ban=<v> --json=<tệp>`. R11 và Q3 chạy bằng lệnh riêng
ghi trong bảng.

| mã | đo gì | cách |
|---|---|---|
| Q6 | lỗi thứ tự học: (ngược + cùng vị trí + ngoài phạm vi) / toàn bộ cạnh vàng | lệnh chấm (`score_roadmap_order`). Kèm phân rã `phan_ra_pham_vi_vang.py`, chỉ để chẩn đoán |
| Q7 | độ phủ tổ tiên tới đích; tỉ lệ đích trọn | lệnh chấm, **kèm đường cơ sở "n gần nhất"**: n = làm tròn (số cạnh cứng / số khái niệm) (bài học v2-06) |
| Q7b | độ chính xác tổ tiên trong chương vàng; đường cơ sở như trên | lệnh chấm |
| cạnh | P/R trực tiếp và theo bao đóng, hai đầu thuộc đích vàng, trên rút gọn bắc cầu của cạnh cứng | lệnh chấm, cùng phép đã nghiệm thu vé 12 |
| Q2 | xung đột danh tính còn mở trong phạm vi xuất bản | lệnh chấm (đếm `identity_open_groups` / `identity_open_pairs`) |
| R11 | bảng kiểm đọc được | `kiem_doc_duoc.py`, bản không phụ thuộc ngôn ngữ (vé 02b) |
| Q3 | sót khái niệm trọng yếu | `scripts/liet-ke-mu/cham_q3.py` với T13; bảng đối chiếu tên do tôi làm theo luật dòng ghép đã có |

**Phần chấm của người** (chủ dự án quyết làm phần nào; khuôn đã có từ v2):
- **T15 — chấm mù cạnh (Q4).** Khuyến nghị nhất: đo thẳng "không cần thứ tự" và "ngược chiều" trên cạnh cứng.
- T12 — Q1, 50 khái niệm mỗi tài liệu.
- T16 — Q9, 50 câu neo.
- T17 — Q8, mạch lạc module.
- Seed bốc mẫu ghi vào giao thức trước khi bốc.

**Đọc:** tôi đọc toàn bộ hai lộ trình (tên module, dòng "cần:", đối chiếu sách) và ghi nhận xét có ví dụ.

## Cách đọc kết quả — đã chốt trước, không có cổng buộc dừng
- Mỗi tỉ lệ kèm khoảng tin cậy Wilson 95%.
- **So với mức tài liệu phát triển sau vé 12** (bảng ở mục cuối, điền lúc khoá):
  - điểm giữ lại nằm trong khoảng của tài liệu phát triển, hoặc hai khoảng tin cậy chồng nhau → **giữ được**;
  - cận trên khoảng tin cậy thấp hơn mức phát triển → **không tổng quát hoá ở chỉ số đó**, báo rõ.
- Ngưỡng v2 chỉ báo làm mốc tham chiếu: Q1 ≥ 97%, Q4 ≥ 0,90 và ngược ≤ 5%, Q6 ≤ 5%, Q7 ≥ 95%, Q7b ≥ 70%. Kèm ghi chú chỉ số nào tài liệu
  phát triển đã không đạt từ trước.
- **Q7 chỉ đọc cùng Q7b và đường cơ sở.** Trên tài liệu phát triển, chỉ nối mỗi khái niệm với 2 khái niệm đứng ngay trước nó trong dãy
  học đã có Q7 **cao hơn** đồ thị máy (doc-1: 0,921 so với 0,825; doc-2: 0,703 so với 0,469), nhưng Q7b thấp hơn nhiều (0,378 so với
  0,660; 0,356 so với 1,000). Độ phủ tổ tiên thưởng cạnh theo thứ tự sách. Đồ thị máy chỉ có giá trị khi độ chính xác vượt rõ đường cơ sở
  mà độ phủ không kém quá xa.
- Bộ vàng có nhiễu (doc-2: hai người gán độc lập chỉ cùng chọn 59% cạnh). "Ngoài vàng" không tự động là sai; đọc cạnh trước khi kết luận.
- Báo nguyên kết quả, kể cả xấu. Không chọn lại tài liệu, chương hay chỉ số sau khi thấy số.

## Luật cấm và quyền truy cập
- Trước bậc 5, không ai mở tệp vàng giữ lại hay đọc đồ thị, lộ trình của hai tài liệu. Ngoại lệ duy nhất là T14 của chủ dự án, và chỉ
  thấy cặp gộp.
- Không dùng nhãn vàng giữ lại để chọn cặp, prompt hay tham số, kể cả gián tiếp.
  - Danh sách khái niệm của bộ vàng chỉ dùng cho T14 (chọn cặp gộp cần người duyệt, như W15) và ở bậc chấm.
  - Nhãn cạnh chỉ dùng ở bậc chấm.
- Sau khi thấy số, mọi thay đổi luồng là hậu kiểm, báo tách riêng. Kết quả giữ lại vẫn là kết quả chính.

## Chi phí
- **Ước 15–40 USD.**
  - Phần lớn là doc-4: cả cuốn, 672 chunk, 620 khái niệm A5.
  - Với luật pass phụ hiện hành, riêng pass phụ có thể 10–25 USD. Để so: doc-2 có 421 khái niệm học được, pass phụ dự toán 20,7 USD.
  - xstk nhỏ hơn.
- Số chắc chắn có ở bậc 3. Mọi lời gọi đi qua `SpendGuard`, `--allow-spend` theo từng bậc.

## Mốc hiện tại trên tài liệu phát triển (trước vé 12 — sẽ thay bằng số sau nghiệm thu vé 12)

Đồ thị cuối của luồng cũ, kho `v3-05b-a9v10-evaluation` v10, đo bằng `cham_tap_giu_lai.py`. Trong ngoặc là Wilson 95%.

| chỉ số | doc-1 | doc-2 |
|---|---|---|
| Q6 lỗi thứ tự học | 4/39 = 0,103 (0,041–0,236) | 13/57 = 0,228 (0,138–0,352) |
| Q7 độ phủ (TB) · n gần nhất | 0,825 · 0,921 (n = 2) | 0,469 · 0,703 (n = 2) |
| Q7 đích trọn | 9/23 = 0,391 | 0/21 = 0,000 |
| Q7b độ chính xác (TB) · n gần nhất | 0,660 · 0,378 | 1,000 · 0,356 |
| cạnh trực tiếp sau rút gọn P · R | 18/29 = 0,621 · 18/28 = 0,643 | 11/17 = 0,647 · 11/32 = 0,344 |
| cạnh bao đóng sau rút gọn P · R | 106/129 = 0,822 · 106/131 = 0,809 | 22/23 = 0,957 · 22/68 = 0,324 |
| Q2 danh tính còn mở (nhóm) | 0 | 1 |

## Thông số chờ vé 12 chốt (điền lúc khoá)
- Cửa sổ định nghĩa (hiện −4…+2), luật so câu trích (gộp khoảng trắng), luật gộp hai thứ tự của pass phụ, prompt pass chính/phụ lượt 3,
  cách sinh tên của 09d.
- **Mức tài liệu phát triển để so:** doc-1, doc-2 sau nghiệm thu vé 12, gồm Q6, Q7 (kèm "n gần nhất"), Q7b, P/R cạnh trực tiếp và bao
  đóng, R11.

## Ai làm gì

| bậc | việc | ai |
|---|---|---|
| 0 | sinh bảng khoá, đối chiếu `prompt_hash` với lượt nghiệm thu vé 12 | tôi |
| 0 | duyệt bảng khoá, đặt trần chi | chủ dự án |
| 1–3 | chạy theo bậc, báo số đếm và chi | nhân viên |
| 1–3 | duyệt chi từng bậc | chủ dự án |
| 2b | T14 duyệt gộp danh tính, trước A8 | chủ dự án |
| 5 | chuyển vàng xstk, chấm tự động, đọc lộ trình | tôi |
| 6 | (tuỳ chọn) sinh bảng chấm người T15, T12, T16, T17 → người chấm | tôi → người |
| 7 | báo cáo kết quả, kể cả trượt | tôi |
