# v3 — Lộ trình chuẩn chỉ và đọc được: kế hoạch vé

> **Kiểm thử 2026-09-26 (Claude):** 01 đạt; 03 đạt, hai điều kiện chuyển sang vé 04; 10 đạt phần đề cử, còn áp tự động thì chưa
> đạt (27/44 phán `same` mới đúng, đại diện có thể là nút chỉ-nhắc, gỡ chu trình sau gộp xoá nhầm cạnh) → vé mới
> [10b](10b-danh-tinh-xac-minh.md). **Không chạy `roadmap --allow-spend` để xuất bản lộ trình trước khi 10b xong.** Báo cáo của nhân
> viên: [01/03/10](../../report/v3-01-03-10-ket-qua-2026-09-26.md).

> **Rà soát đa ngôn ngữ 2026-09-26 (Claude, theo chủ dự án):** tài liệu có thể thuộc bất kỳ ngôn ngữ nào; spec v3 thêm mục "Nguyên tắc:
> tài liệu đa ngôn ngữ" kèm bảng các chỗ đang vi phạm. Vé mới: 14, 15, 16, 17, 02b, T19. Phần từ khoá của vé 03/04 được thay ở vé 14;
> vé 05, 09, 11, 12, 13 có thêm mục sửa. Nặng nhất là vé 16: tên chữ không Latin đang bị coi là ký hiệu, nên A3 loại gần hết khái niệm.

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md) · **Căn cứ:** [báo cáo đánh giá 2026-09-26](../../report/danh-gia-lo-trinh-2026-09-26.md)

**Quy trình (chủ dự án chốt 2026-09-26):** tôi viết spec và vé → chủ dự án giao nhân viên cài đặt → tôi kiểm thử theo mục
"Nghiệm thu" của từng vé và nghiên cứu tiếp. Nhân viên đọc spec v3 trước khi làm vé nào.

## Luật chung cho người làm

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
| 02b | bảng kiểm không phụ thuộc ngôn ngữ (R11 sửa) | kiểm thử | **tôi** | 03 | 0 |
| 03 | vai trò vùng văn bản (R1) | A2 | nhân viên | — | 0 |
| 04 | cấu trúc mục kiểu sách toán (R2) | A2 | nhân viên | 03 | 0 |
| 05 | neo và vị trí chỉ từ vùng dạy (R3) | A9' | nhân viên | 03 | chạy lại neo ≈ 0,5 USD toàn kho phát triển |
| 06 | cạnh không lấy căn cứ từ đề cương/lời nói đầu (R4) | A9 | nhân viên | 03 | 0 |
| 07 | dãy học chỉ gồm khái niệm được dạy (R5) | A10 | nhân viên | 05, 10b | 0 |
| 08 | hiển thị tiên quyết rút gọn và phụ thuộc cấp module (R6) | A10, CLI | nhân viên | 07 | 0 |
| 09 | tên module theo nội dung (R7) | A10/A11 | nhân viên | 03 | ≈ 0,05 USD / tài liệu |
| 10 | danh tính mở rộng (R8) | A9'' | nhân viên | — | ≈ 0,05 USD / tài liệu |
| 10b | xác minh quan hệ danh tính, đại diện được dạy, gỡ chu trình theo vị trí đại diện (R8b) | A9'' | nhân viên | 10 | ≈ 0,02 USD xác minh (+ ≈ 0,28 USD lượt 1 nếu kho mặc định chưa có) |
| 11 | tên khái niệm có nội dung (R9) | sau A5 | nhân viên | 05 | ≈ 0,02 USD / tài liệu |
| 12 | cạnh theo định nghĩa ở A8 (R12) | A8 | nhân viên | 03–11 | ≈ 1–7 USD / tài liệu — **chủ dự án duyệt trước khi chạy** |
| 13 | trích mệnh đề có tên ở A3 (R13) | A3 | nhân viên | sau vé 07 v2 | chạy lại A3–A10; cần kế hoạch ánh xạ vàng |
| 14 | vai trò vùng và cấu trúc mục không phụ thuộc ngôn ngữ (R1, R2 viết lại) | A2 | nhân viên | 03; làm tiếp trên vé 04 | ≈ 0,001–0,01 USD / tài liệu |
| 15 | ngôn ngữ tài liệu bất kỳ ở A5 (R14) | A5 | nhân viên | — | ≈ 0,0001 USD / tài liệu |
| 16 | tên, ký hiệu và tìm nhắc tên không phụ thuộc chữ viết (R15) — **ưu tiên** | A3, A4, A6 | nhân viên | — | 0 |
| 17 | tiền tố danh tính từ bằng chứng trong tài liệu (R16) | A9'' | nhân viên | 10b | ≈ 0,01 USD / tài liệu |
| T19 | cung cấp tài liệu thật ngôn ngữ thứ ba: một chữ viết không Latin (ví dụ tiếng Trung, Nga) và một chữ Latin ngoài vi/en (ví dụ tiếng Pháp) | kiểm thử | **chủ dự án** | — | 0 |

Có thể làm song song: 01, 03, 10 ngay; 04, 05, 06, 09 sau 03; 10b sau 10; 07 sau 05 và 10b; 08 sau 07; 11 sau 05; 16, 15 ngay; 14 làm
tiếp ngay trên vé 04 đang dở; 17 sau 10b. Phần R16 đi cùng vé 05, 12, 13. Chạy thử tài liệu T19 sau 14–17.

## Tôi kiểm thử thế nào

Mỗi vé: đọc diff, chạy test (thấy đỏ trên mã cũ bằng `git stash` hoặc đột biến), chạy **bảng kiểm đọc được** (vé 02) trước/sau trên
doc-1, doc-2, doc-6, nhap-mon-ml, doc-3, naive-bayes, và **đọc lộ trình** trước/sau — ghi phán xét vào mục "Kiểm thử" của vé. Số đo cũ
(Q6, Q7, Q7b) báo kèm để bắt hồi quy. Vé chạm luật văn bản: kiểm thêm có fixture đa ngôn ngữ, không còn danh sách từ của một ngôn ngữ
trong phần mã mới, và `--dry-run` trước/sau.

## Liên quan tới vé 07 v2 (tập giữ lại)

Đề nghị hoãn duyệt T10 tới khi vé 03–11 xong, để khoá cấu hình một lần trên luồng đã sửa. T13 (liệt kê mù trên tập giữ lại) không
phụ thuộc luồng, làm lúc nào cũng được.
