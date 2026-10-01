# v3 — Lộ trình chuẩn chỉ và đọc được: kế hoạch vé

> **Kiểm thử 2026-10-01 (Claude), commit `64fbc24`, `57a7d8d`, `1ed9c34`:**
> - **09c đạt.** Bất biến dãy học và cạnh đúng ở sáu tài liệu; doc-2 module gọn trong một mục 42/53. Phát hiện thêm doc-3, naive-bayes cũng
>   từng có tên "document>"; tên thay thế là tên khái niệm đầu module → vé mới [09d](09d-ten-module-khong-co-muc.md).
> - **Vé 12:**
>   - phần đầu đạt về mã;
>   - mất độ phủ do cửa sổ định nghĩa tôi đặc tả sai, đã sửa;
>   - cổng pilot so nhầm mốc;
>   - [việc còn lại](12-canh-theo-dinh-nghia-a8.md#sửa-đặc-tả-claude-2026-10-01-và-việc-còn-lại).

> **Kiểm thử 2026-09-28 (Claude), commit `9cc8752`:**
> - **Đạt:** 19 (Vertex trung tính với cache, dry-run trùng từng byte; embedding lệch 8,5×10⁻⁹), 05b, 11b.
> - **09b:** luật phần phụ đạt, tên doc-2 chưa đạt → vé mới [09c](09c-module-theo-cay-sua.md) (module chia theo cây sửa, bỏ nút gốc
>   "document>", tiêu đề chỉ có mã).
> - **Q7 doc-2 = 0,469 không do neo:**
>   - 13 cạnh ngoài phạm vi = 9 vào định lý chỉ có trong bài tập + 3 vào tính chất nói một câu + 1 từ node A3 rác;
>   - phần còn lại là A8 thiếu cạnh so với vàng: 18/44 cạnh trong dãy học không có đường đi.
> - **Không đọc 18/44 là lộ trình sai.** Bằng chứng v2-06: thêm cạnh chủ yếu thừa ràng buộc (T11), độ phủ bao đóng thưởng cạnh theo thứ tự
>   sách, vàng doc-2 chỉ 59% cạnh được cả hai người cùng chọn.

> **Cập nhật nhân viên 2026-09-27:** 10b đã commit riêng (`dc0cbce`). Mã và phép đo 05, 14, 16 đã xong, chờ reviewer nghiệm thu;
> xem [báo cáo](../../report/v3-05-14-16-ket-qua-2026-09-27.md). Vé 07 và 11 được mở đường sau 05; vé 15, 17 và T19 để sau theo chủ dự án.

> **Kiểm thử 2026-09-27 (Claude):** 16 **đạt** (0/1.705 tên đổi phân loại, dry-run A6–A8 tái dùng); 05 **đạt về mã** ("Số phức", "Đa
> thức" chỉ-nhắc là đúng — sách không dạy; hai lỗi Q6 mới là nút chỉ-nhắc nằm tạm cuối dãy tới vé 07); 14 lớp cấu trúc **đạt**, lớp nhãn
> bằng mô hình **chưa đạt** — doc-2 cây cũ có 104 mục bài giảng bị gắn đề cương, làm 42 khái niệm mất trạng thái được dạy → vé mới
> [14b](14b-nhan-vai-tro-chia-lo.md). Vé 06, 07 làm được ngay; nghiệm thu 07 trên doc-2 chờ 14b.

> **Kiểm thử 2026-09-26 (Claude):** 01 đạt; 03 đạt, hai điều kiện chuyển sang vé 04; 10 đạt phần đề cử, còn áp tự động thì chưa
> đạt (27/44 phán `same` mới đúng, đại diện có thể là nút chỉ-nhắc, gỡ chu trình sau gộp xoá nhầm cạnh) → vé mới
> [10b](10b-danh-tinh-xac-minh.md). **Không chạy `roadmap --allow-spend` để xuất bản lộ trình trước khi 10b xong.** Báo cáo của nhân
> viên: [01/03/10](../../report/v3-01-03-10-ket-qua-2026-09-26.md).
> **Cập nhật:** 10b **đạt** (Claude đọc các cặp lệch, bỏ cổng số theo chủ trương tăng tốc, chạy ba tài liệu: 0 gộp sai rõ; doc-1 Q6
> về 1/39). Chờ nhân viên commit mã 10b; vé 07 chỉ còn chờ vé 05.

> **Rà soát đa ngôn ngữ 2026-09-26 (Claude, theo chủ dự án):** tài liệu có thể thuộc bất kỳ ngôn ngữ nào; spec v3 thêm mục "Nguyên tắc:
> tài liệu đa ngôn ngữ" kèm bảng các chỗ đang vi phạm. Vé mới: 14, 15, 16, 17, 02b, T19. Phần từ khoá của vé 03/04 được thay ở vé 14;
> vé 05, 09, 11, 12, 13 có thêm mục sửa. Nặng nhất là vé 16: tên chữ không Latin đang bị coi là ký hiệu, nên A3 loại gần hết khái niệm.

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md) · **Căn cứ:** [báo cáo đánh giá 2026-09-26](../../report/danh-gia-lo-trinh-2026-09-26.md)

**Quy trình (chủ dự án chốt 2026-09-26):** tôi viết spec và vé → chủ dự án giao nhân viên cài đặt → tôi kiểm thử theo mục
"Nghiệm thu" của từng vé và nghiên cứu tiếp. Nhân viên đọc spec v3 trước khi làm vé nào.

## Luật chung cho người làm

- **Tăng tốc (chủ dự án 2026-09-26):** số đo trong vé là thông tin cho reviewer, không phải cổng buộc dừng. Chạy đủ phần việc của vé
  (trong trần chi được duyệt) rồi báo số; reviewer đọc và quyết đạt hay chưa.
- Viết test đỏ trước cho bất biến của vé; test phải được thấy đỏ trên mã cũ.
- Sửa `doc/spec-addendum.md`, `CONTEXT.md` và spec liên quan **cùng commit** với mã.
- Mọi lệnh gọi mô hình đi qua `SpendGuard`; chạy `--allow-spend` trên tài liệu có artifact cũ chỉ sau khi chạy không cờ (hoặc
  `--dry-run` khi có vé 01) để biết stage nào định chi. Sự cố 2026-09-26: quên bước này tốn ≈ 0,64 USD.
- Không mở tập giữ lại (`artifacts/a8-gold/xstk-ch3-1-chuong-10-13-*`, `doc-4-chuong-8-vang.json`); không sửa bộ vàng đóng băng.
- Chỉ dùng `gemini-3.1-flash-lite`, temperature 0. Không đẩy nội dung sách ra dịch vụ nào khác Gemini.
- `artifacts/` và `tmp/` không commit.
- **Tài liệu đa ngôn ngữ** (spec v3, mục Nguyên tắc): không thêm danh sách từ hay regex của một ngôn ngữ vào luồng; dùng bằng chứng cấu
  trúc trong tài liệu hoặc một lời gọi mô hình với tập nhãn đóng. Test của vé chạm luật văn bản có fixture ở ít nhất hai ngôn ngữ ngoài
  vi/en (một chữ viết không Latin, một chữ viết không cách từ). Không vì sửa luật mà bắt chạy lại stage tốn tiền trên tài liệu hiện có:
  chạy `--dry-run` trên sáu tài liệu trước và sau.

## Vé

| vé | việc | pha | ai | phụ thuộc | chi phí mô hình |
|---|---|---|---|---|---|
| 01 | chạy thử có dự toán (R10) | CLI | nhân viên | — | 0 |
| 02 | bảng kiểm đọc được (R11) | kiểm thử | **tôi** | — | 0 |
| 02b | bảng kiểm không phụ thuộc ngôn ngữ (R11 sửa) | kiểm thử | **tôi** | 14 | 0 |
| 03 | vai trò vùng văn bản (R1) | A2 | nhân viên | — | 0 |
| 04 | cấu trúc mục kiểu sách toán (R2) | A2 | nhân viên | 03 | 0 |
| 05 | neo và vị trí chỉ từ vùng dạy (R3) | A9' | nhân viên | 03 | chạy lại neo ≈ 0,5 USD toàn kho phát triển |
| 05b | câu ứng viên của bước neo ưu tiên khối mang tên khái niệm; câu xem trước không phải nơi dạy (R3 bổ sung) — **ưu tiên** | A9' | nhân viên | 05 | chạy lại neo phần đổi ≈ 0,1–0,4 USD |
| 06 | cạnh không lấy căn cứ từ đề cương/lời nói đầu (R4) | A9 | nhân viên | 03 | 0 |
| 07 | dãy học chỉ gồm khái niệm được dạy (R5) | A10 | nhân viên | 05, 10b; nghiệm thu doc-2 chờ 14b | 0 |
| 08 | hiển thị tiên quyết rút gọn và phụ thuộc cấp module (R6) | A10, CLI | nhân viên | 07 | 0 |
| 09 | tên module theo nội dung (R7) | A10/A11 | nhân viên | 03 | ≈ 0,05 USD / tài liệu |
| 09b | tên module: phần phụ có nghĩa, tên nền từ cây đã sửa (R7 bổ sung) | A10 | nhân viên | 09 | ≈ 0,01 USD |
| 09c | module chia theo cây đã sửa; tên nền không lấy nút gốc, tiêu đề chỉ có mã hay nhãn đầu đoạn (R7 bổ sung lần 2) | A10 | nhân viên | 09b | ≈ 0,01 USD |
| 09d | module không có tiêu đề mục chung: sinh tên từ tên khái niệm (R7, nhánh chưa cài từ vé 09) | A10 | nhân viên | 09c | < 0,01 USD |
| 10 | danh tính mở rộng (R8) | A9'' | nhân viên | — | ≈ 0,05 USD / tài liệu |
| 10b | xác minh quan hệ danh tính, đại diện được dạy, gỡ chu trình theo vị trí đại diện (R8b) | A9'' | nhân viên | 10 | ≈ 0,02 USD xác minh (+ ≈ 0,28 USD lượt 1 nếu kho mặc định chưa có) |
| 11 | tên khái niệm có nội dung (R9) | sau A5 | nhân viên | 05 | ≈ 0,02 USD / tài liệu |
| 11b | tên khái niệm: căn cứ rộng hơn dòng nhãn, chống trùng tên (R9 bổ sung) | sau danh tính | nhân viên | 11 | ≈ 0,005 USD |
| 12 | cạnh theo định nghĩa ở A8 (R12; cập nhật 2026-09-28: cửa sổ định nghĩa, câu trích kiểm bằng mã) — **làm trước T10** | A8 | nhân viên | 03–11 | ≈ 1–7 USD / tài liệu, dự toán bằng dry-run — **chủ dự án duyệt trước khi chạy** |
| 13 | trích mệnh đề có tên ở A3 (R13) | A3 | nhân viên | sau vé 07 v2 | chạy lại A3–A10; cần kế hoạch ánh xạ vàng |
| 14 | vai trò vùng và cấu trúc mục không phụ thuộc ngôn ngữ (R1, R2 viết lại) | A2 | nhân viên | 03; làm tiếp trên vé 04 | ≈ 0,001–0,01 USD / tài liệu |
| 14b | nhãn vai trò chia lô theo chương, luật kiểm cấu trúc, chuyển vai trò sang chunk cũ (R1 bổ sung) — **ưu tiên** | A2 | nhân viên | 14 | ≈ 0,005–0,02 USD / tài liệu + chạy lại neo doc-2 ≈ 0,05 USD |
| 15 | ngôn ngữ tài liệu bất kỳ ở A5 (R14) | A5 | nhân viên | — | ≈ 0,0001 USD / tài liệu |
| 16 | tên, ký hiệu và tìm nhắc tên không phụ thuộc chữ viết (R15) — **ưu tiên** | A3, A4, A6 | nhân viên | — | 0 |
| 17 | tiền tố danh tính từ bằng chứng trong tài liệu (R16) | A9'' | nhân viên | 10b | ≈ 0,01 USD / tài liệu |
| 18 | cạnh ngược thứ tự sách không ép dãy học (R17) | A10 | nhân viên | — (làm cùng 07 được) | 0 |
| 19 | gọi mô hình qua Vertex AI để dùng credit Google Cloud (hạ tầng) | LLM | nhân viên | — | thử < 0,01 USD; chi qua Vertex tính vào trần dự án 50 USD (chủ dự án quyết 2026-09-28) |
| T19 | cung cấp tài liệu thật ngôn ngữ thứ ba: một chữ viết không Latin (ví dụ tiếng Trung, Nga) và một chữ Latin ngoài vi/en (ví dụ tiếng Pháp) | kiểm thử | **chủ dự án** | — | 0 |
| T10 · 07 v2 | khoá cấu hình và chạy tập giữ lại một lần — [giao thức](T10-07v2-giao-thuc-tap-giu-lai.md) soạn xong 2026-10-01, chưa khoá; bảng khoá sinh bằng `scripts/khoa-cau-hinh/tao_bang.py`, chấm bằng `scripts/doc-lo-trinh/cham_tap_giu_lai.py` | kiểm thử | tôi (soạn, chấm) · nhân viên (chạy) · **chủ dự án** (duyệt khoá, chi, T14) | 12, 09d | ước 15–40 USD, dry-run theo bậc |
| T10a | lệnh chuẩn cho lượt tập giữ lại: `label-roles --transfer-from-chunks-version`, `roadmap --stop-after identity`, bảng duyệt danh tính không đọc vàng — [vé](T10a-cli-tap-giu-lai.md) | CLI | nhân viên | — (song song pass phụ vé 12) | 0 |
| T15-dev | chấm mù đối đầu cạnh dư đồ thị cũ và mới trên hai chương vàng phát triển — bộ tạo/chấm `scripts/cham-mu/tao_bang_v3.py`, `cham_bang_v3.py` (seed 20261001, ghi trước). **Bảng đã sinh 2026-10-01**: `artifacts/a8-gold/cham-mu-v3-doc-{1,2}.xlsx` (35 + 22 cặp), từ pass chính + pilot lượt ba sửa vì đồ thị cuối chưa có; chấm lại theo đồ thị cuối bằng `--moi-cuoi` | kiểm thử | tôi (sinh bảng, chấm) · **hai người chấm** do chủ dự án xếp | đồ thị cuối vé 12 | 0 USD, ≈ 1 giờ/người |

Có thể làm song song: 01, 03, 10 ngay; 04, 05, 06, 09 sau 03; 10b sau 10; 07 sau 05 và 10b; 08 sau 07; 11 sau 05; 16, 15 ngay; 14 làm
tiếp ngay trên vé 04 đang dở; 17 sau 10b. Phần R16 đi cùng vé 05, 12, 13. Chạy thử tài liệu T19 sau 14–17.

**Cập nhật nhân viên 2026-09-27:** vé 14b đã triển khai và đo trên doc-2, nhap-mon-ml, doc-3; [báo cáo](../../report/v3-14b-ket-qua-2026-09-27.md), chờ reviewer nghiệm thu.

**Hiện tại (2026-10-01, sau kiểm thử `64fbc24`):**
- **Đã xong:** 01, 02, 02b, 03, 05, 05b, 06, 07, 08, 09, 09c, 10, 10b, 11, 11b, 14, 14b, 16, 18, 19; 09b đạt phần luật.
- **Vé 12 đang dở:**
  - Mã phần đầu đạt.
  - Pass chính mất độ phủ vì cửa sổ định nghĩa **tôi đặc tả sai**: thiếu các câu giả thiết đứng trước câu neo. Đặc tả đã sửa thành −4…+2.
  - Cổng pilot so nhầm mốc; mốc đúng là đồ thị cuối luồng cũ sau rút gọn. Chấm lại 0 USD cho thấy với cửa sổ sửa, doc-1 ngang luồng cũ về
    độ chính xác.
- **Cập nhật 2026-10-01 (kiểm thử lượt cửa sổ −4…+2, mã chưa commit):**
  - Kết quả đạt mốc: doc-1 bao đóng P 108/127, R 108/131, so với luồng cũ 106/129, 106/131.
  - Còn ba sửa nhỏ trước khi chi ≈ 31 USD cho pass phụ đầy đủ: so câu trích sau khi gộp khoảng trắng, gộp hai thứ tự bớt ngặt, câu trích phải
    từ chính định nghĩa.
  - 09d: cơ chế đạt, nhưng tên ghép liền mẩu tên → đổi sang chọn tên khái niệm nguyên vẹn rồi nối " · ".
- **Cập nhật 2026-10-01 (kiểm thử lượt ba sửa):**
  - Hợp đồng A8 **chốt**: trên hai chương vàng ngang luồng cũ trong nhiễu đo (mọi khoảng tin cậy Wilson chồng nhau).
  - **Cho chạy pass phụ đầy đủ.**
  - 09d **đạt**.
- **Làm tiếp:**
  1. **Vé 12** (nhân viên): commit mốc. Dry-run rồi chạy pass phụ đầy đủ (≈ 31 USD) trên pass chính lượt ba sửa. Sau đó A9 → tên khái niệm →
     A10 → tên module trong kho đánh giá cuối. Báo `cham_tap_giu_lai.py` (doc-1, doc-2) và `kiem_doc_duoc.py` (sáu tài liệu).
  2. Tôi: đọc lộ trình sáu tài liệu, nghiệm thu vé 12, điền "mức tài liệu phát triển" vào
     [giao thức T10/07 v2](T10-07v2-giao-thuc-tap-giu-lai.md).
  3. Chủ dự án (nên có): xếp hai người chấm mù (T15-dev, ≈ 1 giờ/người). Bảng đặt đầu đối đầu cạnh dư của đồ thị cũ và mới, sinh khi
     đồ thị cuối vé 12 có. Giới hạn ghi trước: mỗi đồ thị khoảng 15–20 cạnh dư trên hai chương, chỉ phân biệt được chênh lệch lớn.
  3b. **T10a** (nhân viên, 0 USD, song song pass phụ): ba lệnh chuẩn cho lượt tập giữ lại.
  4. Sau đó **T10** (khoá cấu hình) và **07 v2** (tập giữ lại, chạy một lần).
- **Ngân sách:** chủ dự án đã duyệt ngân sách lớn (credit 300 USD).
  - Đã chi ≈ 31,1 USD tới lượt ba sửa, ước theo sổ token, chưa phải hoá đơn.
  - Dự kiến: pass phụ ≈ 31 USD và tập giữ lại 15–40 USD, tổng cuối ≈ 77–102 USD.
  - Vẫn chỉ dùng `gemini-3.1-flash-lite`.
- **Kho chính:** sáu tài liệu đã có A6 → A7 → neo → danh tính → A8 pass chính v5 (doc-1 v38–42, doc-2 v30–34…); pass phụ chưa chạy.
- **Không đề xuất dựng lại doc-2 từ A3** trên cây mục mới:
  - ID node đổi thì bộ vàng đóng băng không chấm được nếu chưa có kế hoạch ánh xạ (xem vé 13);
  - hệ quả của cây vỡ đã được xử lý ở tầng hiển thị (14b, 09b, 09c).
- **Hoãn theo chủ dự án:** 15, 17, T19.

## Tôi kiểm thử thế nào

Mỗi vé: đọc diff, chạy test (thấy đỏ trên mã cũ bằng `git stash` hoặc đột biến), chạy **bảng kiểm đọc được** (vé 02) trước/sau trên
doc-1, doc-2, doc-6, nhap-mon-ml, doc-3, naive-bayes, và **đọc lộ trình** trước/sau — ghi phán xét vào mục "Kiểm thử" của vé. Số đo cũ
(Q6, Q7, Q7b) báo kèm để bắt hồi quy. Vé chạm luật văn bản: kiểm thêm có fixture đa ngôn ngữ, không còn danh sách từ của một ngôn ngữ
trong phần mã mới, và `--dry-run` trước/sau.

## Liên quan tới vé 07 v2 (tập giữ lại)

Đề nghị hoãn duyệt T10 tới khi vé 03–11 xong, để khoá cấu hình một lần trên luồng đã sửa. T13 (liệt kê mù trên tập giữ lại) không
phụ thuộc luồng, làm lúc nào cũng được.
