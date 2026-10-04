# T10 + 07 v2 — Giao thức khoá cấu hình và chạy tập giữ lại (chuỗi v3)

**Nguồn chân lý:** spec v2 W18–W19 (tập giữ lại mở một lần); spec v3 R1–R17. Giao thức này thay phần chạy của vé v2
[07](../v2-do-thi-lo-trinh/07-xac-nhan-tap-giu-lai.md) và [07b](../v2-do-thi-lo-trinh/07b-cau-hinh-khoa.md) cho chuỗi v3.
**Ai:** tôi soạn và chấm · nhân viên chạy · chủ dự án duyệt khoá, chi và T14.
**Chi phí:** dự toán theo bậc bằng dry-run; trần chi do chủ dự án duyệt ở bậc 0.

**Trạng thái:** **ĐÃ CHẠY VÀ CHẤM XONG 2026-10-04** — [kết quả](../../report/ket-qua-tap-giu-lai-v3-2026-10-04.md); tập giữ lại đã dùng.
**ĐÃ KHOÁ 2026-10-03** — chủ dự án duyệt [bảng khoá](T10-cau-hinh-khoa.md) (commit `2f03781`), nhận đánh đổi của vé 12 và
đặt trần **50 USD** cho cả lượt. **Nâng trần lên 90 USD ngày 2026-10-03** (chủ dự án chọn): pass phụ doc-4 dry-run ước 68,9 USD; chạy
đúng cấu hình đã khoá, không cắt phạm vi. Chạy theo vé [T10b](T10b-chay-tap-giu-lai.md). Lịch sử: soạn 2026-10-01. Cập nhật 2026-10-03: đã điền mức tài liệu phát triển sau vé 12 và thông số vé 12. Điều
kiện 2, 4, 5, 6 đạt (vé 23 đã nghiệm thu); điều kiện 3: [bảng khoá](T10-cau-hinh-khoa.md) đã sinh tại commit `2f03781`, mọi
`prompt_hash` khớp. **Chờ chủ dự án:** nhận đánh đổi của vé 12 (điều kiện 1), duyệt bảng khoá, đặt trần chi.

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
2. Toàn bộ `tests/unit` + `tests/integration` xanh trên commit sẽ khoá. Cây làm việc sạch ở mọi đường ảnh hưởng mã chạy (`src/`,
   `scripts/`, `pyproject.toml`, `uv.lock`). Tệp riêng khác của chủ dự án chưa commit thì bảng khoá liệt kê, không chặn.
3. Bảng khoá đã sinh bằng `scripts/khoa-cau-hinh/tao_bang.py` (không `--nhap`). `prompt_hash` trong bảng khớp manifest của lượt nghiệm
   thu vé 12; lệch là dừng. Chủ dự án đã duyệt.
4. Vé [T10a](T10a-cli-tap-giu-lai.md) xong:
   - `label-roles --transfer-from-chunks-version`;
   - `roadmap --stop-after identity`;
   - bảng duyệt danh tính không đọc vàng.
   Quy trình bậc 1–3 đã viết thành lệnh CLI cụ thể.
5. **Đường chạy giữ lại là đường đã nghiệm thu.** Kiểm tương đương chuỗi (vé T10a mục 5): mọi stage của lệnh `roadmap` ra "tái dùng"
   trên artifact nghiệm thu của tài liệu phát triển.
6. Vé 20, 21, 22 đã xong; A10 sáu tài liệu chạy lại sau vé 20/21. "Mức tài liệu phát triển" lấy từ artifact sau bước này.

## Cách chạy — một lần, theo bậc, không đổi cấu hình giữa các bậc
- **Bậc 0 — khoá (T10):**
  - Sinh bảng khoá vào `T10-cau-hinh-khoa.md`, ghi commit vào giao thức này.
    - 2026-10-03: sinh tại commit `2f03781`. Mã `src/` giống `fce6c48` (vé 23); các commit sau đó chỉ đổi tài liệu và script đánh giá.
  - Chủ dự án duyệt và đặt trần chi của lượt (đề xuất 50 USD trên sổ chi riêng).
- **Bậc 1 — vai trò vùng và cây mục**, theo đúng đường đã dùng cho doc-2:
  - A3–A5 và bộ vàng gắn với version chunks cũ (xstk v2, doc-4 v3), nên **giữ nguyên** version đó.
  - Ingest lại bằng mã đã khoá chỉ để làm cây tham chiếu, với **đúng bộ đọc PDF và thang tiêu đề của chunks gắn A3** (cột "cờ `ingest`
    bậc 1" của bảng khoá): xstk dùng mặc định; doc-4 dùng `--pdf-backend pypdfium2 --heading-scheme vn-textbook`.
    - Lý do: văn bản phải khớp khi chuyển vai trò, mà bộ đọc mặc định tách rời âm tiết ở 34% từ của doc-4.
    - Hai cờ này đã dùng khi tạo chunks gắn vàng; bảng khoá đọc chúng từ manifest, không chọn theo kết quả.
    - Sửa 2026-10-03, trước khoá. Bản trước ghi "dùng lệnh mặc định" và sót bộ đọc PDF.
  - `label-roles` gán vai trò và chuyển sang chunk cũ bằng khớp văn bản (vé 14b). Tên mục lấy từ cây tham chiếu (vé 09b/09c).
- **Bậc 2:** dry-run cả chuỗi. Chủ dự án duyệt dự toán phần trước A8, rồi chạy `--allow-spend` tới hết danh tính: clusters → mentions →
  provenance → neo → danh tính.
- **Bậc 2b — T14, trước A8:**
  - Chủ dự án duyệt **mọi** cặp mà bước danh tính không phán `different` (gộp và tách nghĩa), bảng kiểu T5, chế độ không đọc vàng của vé
    T10a. Tập này lớn hơn yêu cầu "gộp chạm vàng" của W15, nên không ai phải mở vàng trước bậc 5.
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
- **T15 trên tập giữ lại (chủ dự án đồng ý 2026-10-04, sau khi có điểm):** đo độ chính xác thật vì vàng nhiễu. Bộ tạo
  `scripts/cham-mu/tao_bang_giu_lai.py`, seed 20261004. Mỗi tài liệu gồm **mọi** cạnh dư hiển thị (không lấy mẫu), 5 cạnh vàng, 8 cặp
  ngẫu nhiên: xstk 26 cặp (13 dư), doc-4 37 cặp (24 dư). Bảng ở `artifacts/a8-gold/cham-mu-giu-lai-<doc>.xlsx`; chấm bằng
  `cham_bang_v3.py`. Đây là đo bổ sung sau khi thấy số, báo tách riêng, không thay kết quả chính.

**Đọc:** tôi đọc toàn bộ hai lộ trình (tên module, dòng "cần:", đối chiếu sách) và ghi nhận xét có ví dụ.

## Cách đọc kết quả — đã chốt trước, không có cổng buộc dừng
- Mỗi tỉ lệ kèm khoảng tin cậy Wilson 95%.
- **So với mức tài liệu phát triển sau vé 12** (bảng ở mục "Mức tài liệu phát triển sau vé 12"):
  - điểm giữ lại nằm trong khoảng của tài liệu phát triển, hoặc hai khoảng tin cậy chồng nhau → **giữ được**;
  - cận trên khoảng tin cậy thấp hơn mức phát triển → **không tổng quát hoá ở chỉ số đó**, báo rõ.
- Ngưỡng v2 chỉ báo làm mốc tham chiếu: Q1 ≥ 97%, Q4 ≥ 0,90 và ngược ≤ 5%, Q6 ≤ 5%, Q7 ≥ 95%, Q7b ≥ 70%. Kèm ghi chú chỉ số nào tài liệu
  phát triển đã không đạt từ trước.
- **Q7 chỉ đọc cùng Q7b và đường cơ sở.** Trên tài liệu phát triển sau vé 12, chỉ nối mỗi khái niệm với 2 khái niệm đứng ngay trước nó
  trong dãy học đã có Q7 **cao hơn** đồ thị máy (doc-1: 0,921 so với 0,667; doc-2: 0,703 so với 0,395), nhưng Q7b thấp hơn nhiều (0,381
  so với 0,877; 0,356 so với 0,869). Độ phủ tổ tiên thưởng cạnh theo thứ tự sách. Đồ thị máy chỉ có giá trị khi độ chính xác vượt rõ
  đường cơ sở mà độ phủ không kém quá xa. Ở mức phát triển, độ chính xác vượt rõ còn độ phủ kém khá xa; đây là giới hạn đã biết của vé 12.
- Bộ vàng có nhiễu (doc-2: hai người gán độc lập chỉ cùng chọn 59% cạnh). "Ngoài vàng" không tự động là sai; đọc cạnh trước khi kết luận.
- Báo nguyên kết quả, kể cả xấu. Không chọn lại tài liệu, chương hay chỉ số sau khi thấy số.

## Luật cấm và quyền truy cập
- Trước bậc 5, không ai mở tệp vàng giữ lại hay đọc đồ thị, lộ trình của hai tài liệu. Ngoại lệ duy nhất là T14 của chủ dự án, và chỉ
  thấy cặp gộp.
- Không dùng nhãn vàng giữ lại để chọn cặp, prompt hay tham số, kể cả gián tiếp.
  - Danh sách khái niệm và nhãn cạnh của bộ vàng chỉ dùng ở bậc chấm.
  - T14 duyệt mọi cặp danh tính nên không cần chúng.
- Sau khi thấy số, mọi thay đổi luồng là hậu kiểm, báo tách riêng. Kết quả giữ lại vẫn là kết quả chính.

## Chi phí
- **Ước 15–40 USD.**
  - Phần lớn là doc-4: cả cuốn, 672 chunk, 620 khái niệm A5.
  - Với luật pass phụ hiện hành, riêng pass phụ có thể 10–25 USD. Để so: doc-2 có 421 khái niệm học được, pass phụ dự toán 20,7 USD.
  - xstk nhỏ hơn.
- Số chắc chắn có ở bậc 3. Mọi lời gọi đi qua `SpendGuard`, `--allow-spend` theo từng bậc.

## Mức tài liệu phát triển sau vé 12 (điền 2026-10-03) — mốc để so khi đọc kết quả giữ lại

Đồ thị cuối của luồng vé 12: kho `v3-r12-final-evaluation` v8 (sau vé 20/21), tên module ở v9 (sau vé 23); cạnh và dãy học giống v6. Đo bằng `cham_tap_giu_lai.py`,
Claude chạy lại độc lập. Trong ngoặc là Wilson 95%.

| chỉ số | doc-1 | doc-2 |
|---|---|---|
| Q6 lỗi thứ tự học | 4/39 = 0,103 (0,041–0,236); 1 ngược, 3 ngoài phạm vi | 13/57 = 0,228 (0,138–0,352); 0 ngược, 13 ngoài phạm vi |
| Q7 độ phủ (TB) · n gần nhất | 0,667 · 0,921 (n = 2) | 0,395 · 0,703 (n = 2) |
| Q7 đích trọn | 4/23 = 0,174 (0,070–0,371) | 0/21 = 0,000 (0,000–0,155) |
| Q7b độ chính xác (TB) · n gần nhất | 0,877 · 0,381 | 0,869 · 0,356 |
| cạnh trực tiếp sau rút gọn P · R | 17/27 = 0,630 (0,442–0,785) · 17/28 = 0,607 (0,424–0,764) | 11/16 = 0,688 (0,444–0,858) · 11/32 = 0,344 (0,204–0,517) |
| cạnh bao đóng sau rút gọn P · R | 97/111 = 0,874 (0,799–0,923) · 97/131 = 0,740 (0,659–0,808) | 20/25 = 0,800 (0,609–0,911) · 20/68 = 0,294 (0,199–0,411) |
| Q2 danh tính còn mở (nhóm) | 0 | 1 (0 cặp) |
| chấm mù cạnh dư (T15-dev, đồ thị cuối) | 3/10 không cần, 0 ngược | mỗi người 2/5 không cần, 0/5 ngược |

R11 (`kiem_doc_duoc.py`, sáu tài liệu, v9): doc-1 có 6 tên dài, 1 tên khái niệm vô nghĩa ("Định lý 4"), 1 mục bị xé; nhap-mon-ml có 3 tên
dài; doc-2, doc-3, doc-6, naive-bayes 0. Trước vé 23, doc-2 có 5 tên module chỉ có mã.

Luồng cũ, để tham khảo (kho `v3-05b-a9v10-evaluation` v10): doc-1 Q7 0,825, Q7b 0,660, bao đóng 106/129 · 106/131; doc-2 Q7 0,469,
Q7b 1,000, bao đóng 22/23 · 22/68.

## Thông số vé 12 đã chốt (điền 2026-10-03)
- Cửa sổ định nghĩa: câu neo, 4 câu trước, 2 câu sau, trong cùng đoạn của chunk neo (`a8_definition_before = 4`,
  `a8_definition_after = 2`).
- Câu trích của cạnh `can_de_hieu`: phải nằm trong cửa sổ định nghĩa của đích; so sau khi gộp khoảng trắng, lưu nguyên văn. Chỉ
  `can_de_hieu` là cạnh cứng; `cong_cu` là cạnh mềm (`soft_reason: cong_cu`).
- Pass phụ hỏi mỗi cặp theo hai thứ tự. Gộp: cùng chiều, cùng loại, khác `evidence_kind` → giữ loại yếu hơn; cùng chiều, khác loại →
  `cong_cu`.
- Prompt pass chính, pass phụ lượt 3 và mọi stage khác: `prompt_hash` trong bảng khoá, khớp manifest lượt nghiệm thu của doc-1 và doc-6.
- Tên module (09d): chọn tên khái niệm nguyên vẹn, nối " · ".
- Trần token đầu ra của adapter (T10a mục 5): provenance, pass chính, pass phụ 8192; neo 2048; danh tính 1024; tên khái niệm 512; tên
  module 128.
- Độ song song và bộ giới hạn (vé 22) không thuộc phương pháp: phát lại 0 USD cho kết quả y hệt.

## Ai làm gì

| bậc | việc | ai |
|---|---|---|
| 0 | sinh bảng khoá, đối chiếu `prompt_hash` với lượt nghiệm thu vé 12 | tôi |
| 0 | duyệt bảng khoá, đặt trần chi | chủ dự án |
| 1–3 | chạy theo bậc, báo số đếm và chi | nhân viên |
| 1–3 | duyệt chi từng bậc | chủ dự án |
| 2b | T14 duyệt mọi cặp danh tính (không đọc vàng), trước A8 | chủ dự án |
| 5 | chuyển vàng xstk, chấm tự động, đọc lộ trình | tôi |
| 6 | (tuỳ chọn) sinh bảng chấm người T15, T12, T16, T17 → người chấm | tôi → người |
| 7 | báo cáo kết quả, kể cả trượt | tôi |
