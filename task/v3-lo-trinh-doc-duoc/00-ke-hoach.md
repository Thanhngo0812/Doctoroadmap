# v3 — Lộ trình chuẩn chỉ và đọc được: kế hoạch vé

> **Bàn giao nhân viên 2026-09-26:** 01 và 03 đã cài/kiểm; 10 đã cài và chạy thật trên ba tài liệu, kết quả thử
> chưa xuất bản (hai gộp mới chạm vàng, Q6 doc-1 hồi quy, doc-2 còn nhóm mở). Xem
> [báo cáo 01/03/10](../../report/v3-01-03-10-ket-qua-2026-09-26.md). Không chạy lại A8. Vé 04 có thể làm tiếp;
> doc-2 cần sửa cây mục trước khi áp vai trò để loại nơi dạy.

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

## Vé

| vé | việc | pha | ai | phụ thuộc | chi phí mô hình |
|---|---|---|---|---|---|
| 01 | chạy thử có dự toán (R10) | CLI | nhân viên | — | 0 |
| 02 | bảng kiểm đọc được (R11) | kiểm thử | **tôi** | — | 0 |
| 03 | vai trò vùng văn bản (R1) | A2 | nhân viên | — | 0 |
| 04 | cấu trúc mục kiểu sách toán (R2) | A2 | nhân viên | 03 | 0 |
| 05 | neo và vị trí chỉ từ vùng dạy (R3) | A9' | nhân viên | 03 | chạy lại neo ≈ 0,5 USD toàn kho phát triển |
| 06 | cạnh không lấy căn cứ từ đề cương/lời nói đầu (R4) | A9 | nhân viên | 03 | 0 |
| 07 | dãy học chỉ gồm khái niệm được dạy (R5) | A10 | nhân viên | 05 | 0 |
| 08 | hiển thị tiên quyết rút gọn và phụ thuộc cấp module (R6) | A10, CLI | nhân viên | 07 | 0 |
| 09 | tên module theo nội dung (R7) | A10/A11 | nhân viên | 03 | ≈ 0,05 USD / tài liệu |
| 10 | danh tính mở rộng (R8) | A9'' | nhân viên | — | ≈ 0,05 USD / tài liệu |
| 11 | tên khái niệm có nội dung (R9) | sau A5 | nhân viên | 05 | ≈ 0,02 USD / tài liệu |
| 12 | cạnh theo định nghĩa ở A8 (R12) | A8 | nhân viên | 03–11 | ≈ 1–7 USD / tài liệu — **chủ dự án duyệt trước khi chạy** |
| 13 | trích mệnh đề có tên ở A3 (R13) | A3 | nhân viên | sau vé 07 v2 | chạy lại A3–A10; cần kế hoạch ánh xạ vàng |

Có thể làm song song: 01, 03, 10 ngay; 04, 05, 06, 09 sau 03; 07 sau 05; 08 sau 07; 11 sau 05.

## Tôi kiểm thử thế nào

Mỗi vé: đọc diff, chạy test (thấy đỏ trên mã cũ bằng `git stash` hoặc đột biến), chạy **bảng kiểm đọc được** (vé 02) trước/sau trên
doc-1, doc-2, doc-6, nhap-mon-ml, doc-3, naive-bayes, và **đọc lộ trình** trước/sau — ghi phán xét vào mục "Kiểm thử" của vé. Số đo cũ
(Q6, Q7, Q7b) báo kèm để bắt hồi quy.

## Liên quan tới vé 07 v2 (tập giữ lại)

Đề nghị hoãn duyệt T10 tới khi vé 03–11 xong, để khoá cấu hình một lần trên luồng đã sửa. T13 (liệt kê mù trên tập giữ lại) không
phụ thuộc luồng, làm lúc nào cũng được.
